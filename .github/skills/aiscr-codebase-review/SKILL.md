---
name: aiscr-codebase-review
description: Long-running codebase review for the repository it runs in (any AIS CR
  repo except the management hub); two modes (full pass T01-T11, incremental update
  U01-U06) dispatched via detect -> propose-with-evidence -> user-confirm. Owns the
  cache and report schema, severity vocabulary, and English-default output language;
  repo-specific scope stays in the target repo's review_config.toml. The generated
  skill embeds its runbook.
---

<!-- aiscr:compiled=aiscr-codebase-review -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.github/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-codebase-review — codebase-review lifecycle (full and update)

Run the long-running codebase-review lifecycle against the repository this workflow is
invoked in (the **target repository**). It defines the lifecycle, policy, and schemas;
repo-specific scope (apps, file lists, vendored exclusions, thresholds, analysis
families) stays in the target repo's `.agents/config/review_config.toml`. The detailed
runbook — lifecycle phases, cache and report schema, severity, language discipline, and
the complexity budget — lives in the embedded execution plan below.

**When to use vs alternatives:** Use this for a **static codebase review** (architecture,
data layer, security, async, frontend, docs, CI/CD, scripts) producing
`.agents/reports/review_reports/` and analysis JSONs. For **GitHub PR review** use
`/aiscr-review-pr`; for **live deployed UI / SEO** checks use
`/aiscr-prod-ui-crawl-review` (optional T12). Do not conflate them.

## Phase awareness

This skill is a **Category B (execution)** workflow. It runs as a standalone, approved
operational task in the target repository and does **not** require an active OpenSpec
change to produce a review pass. When an OpenSpec change or domain spec governs the
review work, load it as the primary authority; the hub-canonical durable contract is
the workflow contract summarized in this compiled skill. If review findings warrant a governed
change (for example a coordinated refactor or a backlog item), use `/opsx:propose` to
open one and stop for approval — but routine review passes proceed without it. Do not
silently escalate scope beyond the agreed task.

The workflow exposes **two modes** selected by the `detect → propose-with-evidence →
user-confirms` pattern (stable ids under *Codebase-review modes* in
the identifiers and references stated in this workflow):

| Mode | Stable id | When proposed |
|------|-----------|---------------|
| Full pass | `codebase-review-mode-full` | No prior pass, a partial cache to resume, or a full re-run is warranted |
| Incremental update | `codebase-review-mode-update` | A completed pass exists and the goal is a delta refresh |

Mode auto-detection is a **recommendation, not a decision** — present the proposed mode
with its evidence and obtain explicit user confirmation before any write. The detect
phase runs **even when the operator typed a mode argument**. Cache-aware resumption is
**intrinsic to `codebase-review-mode-full`**; there is no third mode. The workflow
**refuses** to run with the management hub `aiscr-management` as the target.

## Context to load first

1. The target repository's `AGENTS.md` — repo-specific agent instructions take precedence.
2. `.agents/config/review_config.toml` (target) — Tier 3 scope: app/module names, key file lists, vendored exclusions, analysis families, severity thresholds, task-size guardrails, `phase_outputs` mapping, `open_issues`.
3. `.agents/config/review_cache.json` (target) — task status, file hashes, sub-task entries, `last_updated`.
4. `.agents/reports/review_reports/` (target) — presence of `final_audit.md` and per-task reports.
5. the embedded execution plan below — the execution-layer runbook (lifecycle phases, cache/report schema, severity, language, complexity budget, three-tier split).
6. the workflow contract summarized in this compiled skill — durable behavioral contract (when present in the repo).
7. the identifiers and references stated in this workflow — *Codebase-review modes* stable ids.

If `.agents/scripts/review_tools.py` exists in the target repo, use it for mechanical
detection (`hash`, `status`, `coverage-gaps`, `cross-validate`, `id-inventory`,
`lint-artifacts`, `all`); it is repo-local plumbing, not a hub contract.

## Steps

1. **Detect** (read-only). Inspect cache existence and populated tasks, the cache
   `last_updated`, presence of `final_audit.md` and per-task reports, and source-file
   recency (via `review_tools.py hash` when available). **Refuse** when the target is
   `aiscr-management`. **Enrolment check:** if the repo has **no review setup at all** —
   no `review_config.toml`, no `review_cache.json`, and no `review_reports/` — it is
   **not enrolled**; the skill stub being present is not enrolment. Explain that
   creating review configuration and state is a deliberate, separately-approved step
   (bootstrap or a controlled enrolment change), and **stop** without scaffolding.
2. **Log model usage** at the start per `aiscr-model-logging.md`.
3. **Propose one mode with evidence** (`codebase-review-mode-full` / `-update`). Verify
   any operator-typed mode against the evidence: **refuse** when incompatible (e.g.
   `update` with no prior pass → recommend `full`), **warn** on partial match, reject
   any other value (state both ids).
4. **Obtain explicit user confirmation** before any write-capable step.
5. **Execute the confirmed mode** per `codebase-review.plan.md`:
   - `codebase-review-mode-full`: run phases T01–T11 governed by the repo
     `review_config.toml`; resume from the cache (run only `pending` tasks; do not
     restart `done` tasks unless their inputs changed since `last_updated`); honour
     vendored exclusions, the review complexity budget, and **DONE MEANS DONE**.
   - `codebase-review-mode-update`: run phases U01–U06; write findings into the existing
     `final_audit.md` body sections plus a dated changelog entry — never a separate report.
   - In U05, treat workflow-evolution notes as sibling-local evidence. Classify each
     suggestion with an evidence path, proposed hub target, and disposition
     (`incorporated`, `pending`, `rejected`, or `partially incorporated`). Do not compare
     suggestions against retired sibling `review_codebase.md` / `review_update.md`
     prompts, and do not edit hub workflow sources from the sibling review run.
6. **Write outputs** per the plan's cache/report schema, severity vocabulary, and
   output-language discipline: update analysis JSONs, `bugs.md`,
   `refactoring_backlog.md`, `final_audit.md` (body **and** changelog), and the cache
   atomically per phase. Timestamps come from git or the runtime clock, never guessed.
7. **Handle workflow-evolution handoff** only after explicit approval for the current
   review run. Approved hub-owned follow-up uses the existing `report-to-backlog-handoff`
   and hub note-idea workflow semantics, then stops at a `schema: backlog` item. Without that
   approval, feedback remains in sibling evidence or report output.
8. **Validate** with `review_tools.py all` (when present); fix inconsistencies before
   marking a task `done`.
9. **Close out** the rolling usage-log entry per `aiscr-usage-logging.md` (agent/runtime,
   model, subagents used, MCP servers used, mode, target repo, impacted paths).

<!-- aiscr:gen:id=guardrails -->
## Iron Law

**IRON LAW:** `NEVER MARK A TASK DONE UNTIL EVERY FILE IN ITS SCOPE WAS DIRECTLY READ — NOT VIA SUMMARY, SEARCH, OR DIRECTORY LISTING.`

**IRON LAW:** `NEVER RUN THE CODEBASE-REVIEW WORKFLOW AGAINST THE MANAGEMENT HUB (AISCR-MANAGEMENT) AS THE TARGET.`

**IRON LAW:** `NEVER CREATE REVIEW SCAFFOLDING (REVIEW_CONFIG.TOML, REVIEW_CACHE.JSON, .AGENTS/ANALYSIS/, .AGENTS/REPORTS/REVIEW_REPORTS/) IN A REPO THAT HAS NONE WITHOUT EXPLICIT, SEPARATELY-APPROVED ENROLMENT. THE SKILL STUB BEING PRESENT IS NOT ENROLMENT.`

**IRON LAW:** `NEVER PROCEED PAST MODE PROPOSAL WITHOUT EXPLICIT USER CONFIRMATION.`

**IRON LAW:** `NEVER HARDCODE REPO-SPECIFIC SCOPE (APP NAMES, FILE LISTS, VENDORED LIBRARIES, THRESHOLD VALUES) INTO THE HUB-CANONICAL SOURCE — IT BELONGS IN THE TARGET REPO REVIEW_CONFIG.TOML.`

**IRON LAW:** `NEVER SELF-MODIFY HUB CODEBASE-REVIEW WORKFLOW SOURCES OR EMIT HUB BACKLOG ITEMS FROM A SIBLING REVIEW RUN WITHOUT EXPLICIT CURRENT-RUN HANDOFF APPROVAL.`

No exceptions. These override any "the file is obviously fine", "the cache says done so I

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The detect phase picked `full` so I can just start writing" | Present the proposed mode with evidence; wait for explicit user confirmation. |
| "The operator asked for `update`, so I'll run `update`" | Run detect first; if no prior pass exists, refuse and recommend `codebase-review-mode-full`. |
| "I read the summary / a subagent's report, that's enough to mark done" | DONE MEANS DONE — read every in-scope file directly, or split. |
| "This app name / file list belongs in the canonical body" | Tier 3 — it goes in the target repo `review_config.toml`, not the hub source. |
| "Update mode found a big gap; I'll just do a full re-run now" | Document the gap; recommend a separate `full` invocation. Do not escalate in-session. |
| "I'll add the new findings to the changelog only" | Update `final_audit.md` body sections **and** the changelog. |
| "The source comment is Czech; I'll translate it in the quote" | Preserve Czech-native quoted content and domain identifiers verbatim; only the analytical voice is English. |
| "This 2,000-line file is over the line limit, split it" | Line count is a caution signal, not the trigger — justify splits by coherent unit and complexity. |
| "The skill stub is here, so I'll create `review_config.toml` and start a pass" | If the repo has no review setup it is not enrolled — explain that enrolment is deliberate and separately approved, and stop. |
| "I'll target aiscr-management to test the workflow" | Refuse. The hub carries no review lifecycle; point to `run_validation_all.py` / `validate_tool_parity.py`. |
| "U05 found a good workflow fix, so I'll patch the hub source now" | Record the evidence and prepare a handoff candidate; hub backlog emission requires explicit approval for this run. |
<!-- aiscr:endgen -->

## Verification before completion

- [ ] Detect phase ran (cache, reports, file-change recency) before any mode proposal; target is not the hub; a repo with no review setup was reported not-enrolled and not scaffolded.
- [ ] A mode was proposed **with evidence** and the user **explicitly confirmed** it before any write; an operator-typed mode was verified against evidence.
- [ ] Every file in each completed task's scope was directly read (DONE MEANS DONE); splits used the letter-suffix convention with per-sub-task reports and cache entries citing `scope`.
- [ ] Cache conforms to canonical `schema_version: "2"`; no completed task invalidated by a field-add.
- [ ] `final_audit.md` uses the canonical English section ordering; body sections **and** changelog updated together.
- [ ] Severity labels use Critical/High/Medium/Low; bug/backlog entries cross-referenced with GitHub Issues.
- [ ] Output language is English by default; Czech-native quotations and AIS CR domain identifiers preserved verbatim.
- [ ] `review_tools.py all` (when present) passed; inconsistencies fixed.
- [ ] Rolling usage-log entry updated (agent/runtime, model, subagents, MCP servers, mode, target repo, impacted paths).

## Governance

- The workflow runs **in the target repository's working tree** and writes review
  outputs there. It makes no hub-side writes when run against another repository.
- The management hub's configuration-sync path distributes the **skill surface**
  (the vendor stub, this canonical doc, and the plan) to repositories; it does **not**
  create review configuration, state, or reports. Review artifacts are produced only by
  **running this workflow**, and initial enrolment of a repo that has none is a
  deliberate, separately-approved step — never a side effect of receiving the stub.
- Repo-specific scope is authoritative in the target repo `review_config.toml` (Tier 3);
  the hub-canonical source and plan never hardcode it.
- This canonical source plus the embedded execution plan below are the single
  operational source. Agents must not self-modify them during a review session;
  workflow-evolution feedback is human-mediated through report-to-backlog handoff and
  hub note-idea workflow semantics after explicit current-run approval.
- Durable contract: the workflow contract summarized in this compiled skill. Full runbook:
  the embedded execution plan below.

## Valid next steps

- When review findings warrant coordinated work, open a governed backlog change.
- Read the identifiers and references stated in this workflow and follow the **Usage** section before loading a different workflow's context.
