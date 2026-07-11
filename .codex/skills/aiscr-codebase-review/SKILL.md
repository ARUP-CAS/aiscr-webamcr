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

- This `.codex/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
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

## Embedded execution plan

### Plan: Codebase review lifecycle (full pass and incremental update)

> **Spec-led.** Persistent behavioral requirements live in
> the workflow contract summarized in this compiled skill. The workflow-skill entry point is
> this compiled workflow skill (`/aiscr-codebase-review`).
> This plan is the reusable execution and governance layer.

#### Context

This plan lives in **aiscr-management** (the AIS CR / ARUP-CAS management hub) and
defines the codebase-review lifecycle for any AIS CR repository the workflow runs in.
After the workflow skill is propagated to a repository, an agent in that repository
runs the review against **its own repository** — the "target repository" is simply the
repo the workflow is invoked from. The management hub `aiscr-management` is **refused**
as a target (it carries no review configuration or state by design).

The workflow owns the lifecycle, policy, and schemas; **repo-specific scope** (app and
module names, key file lists, vendored exclusions, analysis families, severity
thresholds, task-size guardrails, the `phase_outputs` mapping, and the GitHub
open-issues count) lives in the target repo's `.agents/config/review_config.toml`
(Tier 3 — see *Three-tier authority split*). Per-repo state lives in
`.agents/config/review_cache.json` and `.agents/reports/review_reports/`. If
`.agents/scripts/review_tools.py` exists in the target repo, use it for mechanical
detection (`hash`, `status`, `coverage-gaps`, `cross-validate`, `id-inventory`,
`lint-artifacts`, `all`); it is repo-local plumbing, not a hub contract.

A repository is **enrolled** in the lifecycle when it has review setup
(`review_config.toml`, `review_cache.json`, or `review_reports/`). Receiving the skill
stub through the shared sync surface does **not** enrol a repo: the workflow refuses to
auto-scaffold review artifacts in a repo that has none. Initial enrolment is a
deliberate, separately-approved step (governance bootstrap, or a controlled change that
introduces `review_config.toml`) — **not** something the config-sync tooling performs.

**Not in scope:** GitHub PR review (`aiscr-review-pr`, `review_pr.py`) and deployed
live-UI/SEO verification (`aiscr-prod-ui-crawl-review`, optional T12). Those are
separate workflows; do not conflate them with the static codebase review here.

#### Modes and dispatch

Two modes are selected by the bootstrap-style `detect → propose-with-evidence →
user-confirms` pattern (stable ids under *Codebase-review modes* in
the identifiers and references stated in this workflow):

| Mode | Stable id | When proposed |
|------|-----------|---------------|
| Full pass | `codebase-review-mode-full` | No prior pass, a partial cache to resume, or a full re-run is warranted |
| Incremental update | `codebase-review-mode-update` | A completed pass exists and the goal is a delta refresh |

The detect phase runs **even when the operator typed a mode argument**, so the
requested mode is verified against evidence: **refuse** when incompatible (for example
`update` requested but no prior pass exists → recommend `codebase-review-mode-full`);
**warn** on partial match; reject any other mode value, stating both supported ids.
Mode auto-detection is a **recommendation, not a decision** — present the proposed mode
with its evidence and obtain explicit user confirmation before any write. Cache-aware
resumption is **intrinsic to `codebase-review-mode-full`**; there is no third mode.

**Datetime discipline.** All timestamps (`completed_at`, `last_updated`, report date
fields) MUST come from a verifiable source — `git log -1 --format=%ci -- <path>`
(ISO 8601) or the runtime clock — never guessed.

#### Canonical lifecycle phases

Phase names are **abstract and stack-neutral**. The target repo's `review_config.toml`
`phase_outputs` mapping binds each canonical phase id to that repo's concrete analysis
output filenames (preserved without rename); per-task report headers MAY append a
stack-specific descriptor for reader clarity (for example *T03 — Data-layer analysis
(Django ORM)* or *T03 — Data-layer analysis (Solr / XSLT)*), but cross-references in
`final_audit.md` and the findings sources use the canonical phase id.

**Full pass (T01–T11):**

- **T01 — Repository map.** Structural index: directories and their purpose, application/module boundaries, file sizes and types, infrastructure components. Update whenever structure changes.
- **T02 — Dependency graph.** Internal and external dependencies; production code only (exclude test directories from the architectural import graph). Distinguish module-level imports (load-time, higher circular-dependency risk) from lazy imports. Detect circular dependencies (module-level vs lazy carry different severity per Tier 3 thresholds), high fan-in modules (decomposition candidates) and high fan-out modules (high-responsibility candidates), and outdated dependency versions. Record architectural issues in `refactoring_backlog.toml`.
- **T03 — Data-layer analysis.** Persistence and data-access patterns: models/schemas read directly (not via summary), migrations, query patterns, eager-vs-lazy loading, signal/handler chains that can cause hidden N+1 queries, custom managers/query helpers. Detect N+1 queries, counting anti-patterns, missing eager-loading, missing change-detection caching, deprecated data-layer APIs, unindexed filtered fields, and queries in templates or property methods. Record severe issues as bugs.
- **T04 — Build and container analysis.** All build/container/orchestration files and infrastructure service configs. Detect oversized images, build-only dependencies leaking into production images, poor layer caching, outdated/insecure base images, hardcoded secrets, incorrect secret-injection mechanisms per service, dev/prod version parity gaps, services placed in the wrong environment, multi-process containers lacking a supervisor or exec pattern, and admin/monitoring interfaces exposed without isolation or auth.
- **T05 — Security analysis.** Production security audit. Run the framework's deploy check first and record warnings. Inspect framework security settings (including dangerous fallback values), secrets management (distinguishing placeholder from real-looking credentials), authentication/authorization, proxy-level controls (HTTPS/HSTS/headers, defense-in-depth), CORS, CSRF, injection risks (raw queries), and XSS risks (unsafe-HTML helpers) classified by input provenance: hardcoded static → acceptable; model/DB value without escaping → medium; request/user input → high. Audit dependencies for known CVEs; when scanners are unavailable, record "CVE audit recommended". Cross-reference build-level findings from T04 by ID rather than duplicating them. For security-sensitive areas consider a dedicated security review before merge.
- **T06 — Async and background-processing analysis.** Asynchronous/scheduled task processing: task definitions, schedule configuration, retry and error handling, shared state, timeouts, routing/priority. Detect tasks without error handling, race conditions, long synchronous operations inside tasks, missing idempotence in critical tasks, synchronous calls that should be async, leaks in long-running tasks, and external calls without timeout or retry. Summarize trivial wrapper tasks; describe domain-significant tasks in detail.
- **T07 — Frontend analysis.** Only first-party code authored by the project's developers; skip vendored/third-party assets per `vendored_exclusions`. Inspect custom JS/CSS architecture, async patterns, template inline scripts (extraction candidates), server→client data-passing patterns, and CDN loading (SRI/integrity, fallback). Detect logic/anti-pattern errors, API-misuse silent failures, logical-operator (De Morgan) mistakes in guards, missing SRI on external `<script>`/`<link>`, missing minification of custom assets, and inconsistent data-passing. Third-party library internals, vendored bundles, and npm-package CVEs (the latter belong to T05) are out of scope.
- **T08 — Documentation analysis.** Documentation and documentation generators: site config, generator scripts (including subprocess return-code and stderr/stdout handling), auto-generated tables, license docs. Detect generators that may fail, fragile parsing without error handling, outdated generated content, duplication, broken/outdated links, inconsistent formatting, and docs that no longer match code behavior.
- **T09 — CI/CD analysis.** Automation, testing, and deployment pipeline: workflow definitions, pre-commit hooks, linting config, test infrastructure, and security/supply-chain tooling (image scanning, SBOM, signing, provenance, static analysis, dependency-update bots). Detect workflows without timeouts, missing coverage reporting, secrets exposed in logs, missing branch protection, suboptimal cache use, hooks that fail in CI, and missing security scanning. Summarize how the pipeline supports supply-chain security so T05 and T11 can cross-reference.
- **T10 — Operational scripts analysis.** Operational and development scripts (the repository-root scripts directory; documentation generators belong to T08). Treat config files (cron tables, service inis) as related artifacts, not line-by-line scripts. Detect missing error handling (`set -e`/`-u`/`-o pipefail` where applicable), unvalidated inputs before destructive operations, hardcoded paths/hostnames, unvalidated environment assumptions, duplicated functionality, and missing help text. Each issue entry carries `id`, `severity`, `summary`, affected `scripts`, and `recommendation`.
- **T11 — Final audit.** Consolidated synthesis written only after T01–T10 are complete. See *Report schema* for the fixed English section ordering. Run `review_tools.py all` (when present) and verify referenced IDs before finalizing.

**Incremental update (U01–U06):**

- **U01 — Change detection.** Identify what changed since the last review: changed/deleted files (hash comparison), new untracked files (new source modules, build files, scripts, workflows, frontend assets, templates), and the affected phases.
- **U02 — Coverage audit.** Find files, modules, or directories missed or under-covered by the initial cycle (apps without data-layer coverage, custom frontend files not analyzed, uncovered scripts, new directories not in the repository map). Resolve small gaps in-session via the coverage-gap sub-task workflow; defer large gaps to a recommended `full` re-run with a clear action item.
- **U03 — Cross-validation and consistency.** Run mechanical checks (orphan bugs, backlog-prefix mismatches, severity mismatches, cache-path validity, orphan/duplicate IDs, JSON/schema/entry-completeness lint). Manually verify final-audit accuracy (top-findings list references valid IDs; no high-severity finding missing; section content matches task reports).
- **U04 — Spot-check findings validity.** Targeted (not full) re-verification: read the referenced file/line for every Critical/High bug and a sample of Medium bugs; confirm or invalidate; re-check key architectural findings; flag fixed-but-not-updated entries for status update.
- **U05 — Workflow-evolution integration.** Classify accumulated workflow-improvement feedback (`incorporated` / `pending` / `rejected` / `partially incorporated`) and produce a prioritized list of pending suggestions with concrete, copy-pasteable diffs for the human reviewer. Agents MUST NOT self-modify the canonical workflow source during an update session; feedback routes to the hub through the documented workflow-evolution feedback path.
- **U06 — Artifact refresh.** Update all artifacts from U01–U05 in one atomic pass, in this order: analysis JSONs (append/update in place, never overwrite); `bugs.toml` (new + fixed-status) and `refactoring_backlog.toml`; `review_tools.py render` to regenerate the Markdown twins; the cache (`file_hashes`, `last_updated`); and `final_audit.md` in two passes — (a) body sections to reflect the current consolidated state, (b) a dated changelog entry. Collect findings first, write once at U06.

U05 implementation detail: legacy `.agents/prompts/prompt_evolution/*_prompt_update.md`
files are migration evidence, not active prompt patches. Record evidence paths,
proposed hub targets, and dispositions; prepare human-readable handoff candidates;
keep well-formed pending suggestions non-blocking. Do not write hub backlog items
unless the user explicitly approves backlog handoff for the current review run.
Approved handoff uses `report-to-backlog-handoff` and hub note-idea workflow semantics,
creates or updates only `schema: backlog` items, cites sibling evidence, and stops
before planning or implementation.

##### DONE MEANS DONE

Never mark a task `done` until **every file in scope was directly read** — not via a
sub-agent summary, search snippet, or directory listing. If the review-complexity
budget is exhausted before a phase is fully covered: split into sub-tasks, mark the
completed part `done`, mark the parent `split`, and leave the remainder `pending`. Do
not silently escalate `update` mode into a `full` re-run within the same session —
document the gap and recommend a separate `full` invocation.

#### Cache schema

`.agents/config/review_cache.json` is repo-local and conforms to this canonical schema.
**Canonical `schema_version`: `"2"`.**

```json
{
  "schema_version": "2",
  "last_updated": "<iso8601>",
  "tasks": {
    "T01": { "status": "pending|done|skipped", "completed_at": null, "report_path": null },
    "T03": {
      "status": "pending|done|split",
      "completed_at": null,
      "report_path": null,
      "sub_tasks": {
        "T03a": { "status": "pending|done", "completed_at": null, "scope": "<module or component>", "report_path": null }
      }
    }
  },
  "file_hashes": {
    "<relative_path>": { "sha256": "<hash>", "last_reviewed": "<iso8601>", "task_id": "<T0X>" }
  }
}
```

Required fields: `schema_version`, `last_updated`; per task `status` and (when
complete) `completed_at` / `report_path`; for split phases a `sub_tasks` map whose
entries carry `scope` and `report_path`; and `file_hashes` keyed by relative path.

A repo whose cache predates this schema is brought to `schema_version: "2"` by an
**incremental field add** only — introduce `schema_version` and any missing fields
(`sub_tasks`, `scope`, per-task `report_path`). Do **not** move payload between fields,
rename existing task or sub-task ids, or invalidate completed tasks.

#### Findings schema

Review findings are **structured sources of truth**, not prose. `.agents/reports/bugs.toml`
and `.agents/reports/refactoring_backlog.toml` are authored by the agent; the Markdown
files `bugs.md` and `refactoring_backlog.md` are **generated twins** produced by
`review_tools.py render` and must never be hand-edited. Tooling reads typed fields from
the TOML; no machine-read field is recovered by matching a Markdown heading or a bold
label.

**Canonical `schema_version`: `"1"`** for both files. `lint-artifacts` rejects an
unrecognized version by name rather than reading absent fields.

`preamble` carries the file-level narrative that belongs to the document rather than to
any finding — the bugs header stating the open-issue count and status vocabulary, the
backlog note explaining that refactoring priority is evaluated on a different frame from
bug severity. It is part of the source so that regeneration cannot discard it.

```toml
### .agents/reports/bugs.toml
schema_version = "1"
preamble = """
Before adding a new bug, check the existing GitHub Issues (currently 113 open).
Statuses: `already tracked (Issue #XXX)` | `extends existing issue #XXX` | `new issue candidate`"""

[[bug]]
id = "BUG-001"
title = "eval() on values from the database in the identifier generators"
severity = "Critical"          # Critical | High | Medium | Low
task = "T03"                   # discovering phase id
github_issue = "new issue candidate"
description = """..."""
recommended_fix = """..."""
alignment = """..."""          # optional; documents a severity/priority divergence

  [[bug.files]]
  path = "webclient/projekt/models.py"
  line = 663                   # optional
  symbol = "Projekt.set_permanent_ident_cely()"  # optional
  note = "found in T03c"       # optional
```

`alignment` is the **only** place a documented severity-versus-priority divergence is
recorded. `cross-validate` reads that field; it never infers intent from wording in
`description` or `recommended_fix`.

```toml
### .agents/reports/refactoring_backlog.toml
schema_version = "1"
preamble = """
Structural improvements discovered during the audit."""

[[item]]
id = "CIRC-01"
title = "Circular dependency projekt <-> oznameni"
priority = "High"              # High | Medium | Low
task = "T02"                   # or "T02/T03" when two phases share the finding
description = """..."""        # authored as Description, or as Finding
recommendation = """..."""     # authored as Recommendation, or as Proposal
impact = """..."""             # optional; own field, never folded into description
effort = "L"                   # optional; S | M | L | XL
severity = "Medium"            # optional; when the item also carries a bug severity
files = ["webclient/oznameni/models.py", "webclient/projekt/forms.py"]  # optional
applications = ["uzivatel (31)", "core (26)"]  # optional; affected module scope
bugs = ["BUG-004"]             # optional cross-references into bugs.toml
```

Required per bug: `id`, `severity`, `task`, and at least one `files` entry. Required per
backlog item: `id`, `priority`, `task`, `description`. Severity and priority values
outside the canonical vocabularies are a `lint-artifacts` error naming the offending
identifier.

**Label normalization.** Repositories that authored backlog items with `Finding` and
`Proposal` labels map them to `description` and `recommendation`. `Impact` has no
synonym and is retained as its own optional field rather than folded into `description`.

**Identifier discipline.** A finding's identifier is durable. Where a backlog heading
carries no identifier but the repo's analysis artifacts already name one for the same
finding (for example `SOLR-001` in `solr_analysis.json`, `ARCH-01` in
`dependency_graph.json`), that identifier is carried forward. Identifiers are never bound
to headings by automated title similarity, and a newly assigned identifier requires
maintainer review.

#### Repository configuration schema

Repo-specific scope lives in `.agents/config/review_config.toml` (Tier 3). The engine
reads only a structural subset; the remaining keys are agent-facing. TOML orders bare
keys before tables, so top-level scalars and arrays precede every `[table]` header.

```toml
repository = "aiscr-webamcr"
branch = "test"
open_issues = 113
ignored_directories = ["media", "staticfiles"]
source_extensions = [".py", ".js", ".html"]

[vendored_exclusions]
directories = ["vendor", "libs"]
copyright_headers = ["/*!", "* @license"]
file_patterns = ["*.min.js", "*.min.css"]
filenames = ["leaflet.js"]

[[tasks]]
id = "T01"
target_file = ".agents/analysis/repository_map.json"

[[key_django_apps]]
dir = "webclient/core"
```

The engine parses this with the standard library (`tomllib`). It carries **no
hand-maintained parser** for any structured format, and it requires Python 3.11 or newer.

#### Report schema

Each completed task (and each sub-task, e.g. `T03c`) produces its own
`.agents/reports/review_reports/<id>.md` written in the same session as the analysis —
never deferred. Per-task report body: summary of findings, identified problems,
improvement suggestions, a refactoring-effort estimate table, and a workflow-evolution
note. Also update the relevant analysis JSON and the findings sources `bugs.toml` and
`refactoring_backlog.toml`, then run `review_tools.py render` to regenerate their
Markdown twins.

`final_audit.md` (T11) uses this fixed **English** section ordering so reports are
comparable across repositories regardless of stack:

1. Major architectural issues
2. Security risks (prioritized)
3. Dependency issues (circular and problematic)
4. High-complexity modules
5. Data-layer performance issues
6. Build and deployment issues
7. Frontend risks
8. CI/CD gaps
9. Major technical debt
10. Prioritized refactoring plan
11. Long-term maintenance recommendations
12. Changelog

Repo-specific findings fit **inside** these sections; do not introduce parallel report
layouts. **Body sections (1–11) must reflect the current consolidated state** — a
reader of the body alone must get the complete picture. The changelog records *what
changed and when*; incremental updates append a dated changelog entry and update the
affected body sections (never the changelog alone).

##### Coverage-gap resolution

When `coverage-gaps` or a U02 audit finds missed files/modules: create sequentially
named sub-tasks (letter-suffix convention), each covering a cohesive group reviewable
in one DONE-MEANS-DONE pass; read every in-scope file; write the sub-task report; then
in a single atomic pass, in this order: update the analysis JSON (append), write
`bugs.toml` and `refactoring_backlog.toml`, run `review_tools.py render` to regenerate
the Markdown twins, update the cache sub-task entry (`status`, `completed_at`, `scope`,
`report_path`), and update `final_audit.md` body **and** changelog. Rendering belongs
inside the pass so the twins are never stale between phases. Common pitfall: updating
only the changelog while leaving body sections stale — update both.

#### Severity vocabulary and bug-tracking discipline

Use one shared **English** severity vocabulary across `bugs.toml`,
`refactoring_backlog.toml`, and final-audit ranking: **Critical / High / Medium / Low**.
Severity and priority are **typed fields** in the findings sources, never labels
recovered from Markdown prose.
The numeric thresholds that map a finding to a severity (fan-in/fan-out cutoffs,
version-gap sizes, etc.) are Tier 3 values in the target repo's `review_config.toml`;
this workflow names the rule, the repo supplies the value.

**GitHub Issue cross-reference is mandatory.** Before filing a `bugs.toml` or
`refactoring_backlog.toml` entry, check the target repo's GitHub Issues and mark the entry
as *already tracked (Issue #N)*, *extends existing Issue #N*, or *new candidate*. When a
bug also appears in the refactoring backlog, reconcile severity vs priority; document
any intentional divergence in the bug entry. When a `Critical` bug is found, record it
and surface it at the top of the session summary before starting the next task.

Each bug entry carries: file path and line, severity, GitHub-Issue status, description,
recommended fix, and source task id. Backlog items prefixed `[TXX]` must match the task
that discovered them.

#### Output language and quotation discipline

Review outputs are authored in **English by default** — task reports, `final_audit.md`
body and changelog, `bugs.toml` and `refactoring_backlog.toml` prose fields (`title`,
`description`, `recommended_fix`, `recommendation`, `preamble`), analysis JSON
descriptions/notes, workflow-evolution feedback, severity values, and `final_audit.md`
section headings.

**Quotation carve-out.** When citing Czech-native repository content — source comments,
docstrings, GitHub issue titles, documentation passages, and AIS CR domain entity names
used as identifiers (Projekt, Akce, Lokalita, Dokument, PIAN, Hesláře, Knihovna3D, and
similar) — the cited material and the domain identifiers are preserved **verbatim** in
Czech; only the workflow's own analytical voice is in English. A parenthetical English
gloss MAY be added when the quotation is load-bearing for an analytical claim. Treat
identifiers and AIS CR domain nouns as code.

**Pre-existing Czech artifacts** (authored before a repo adopted the English-default
rule) are converged conditionally, not in a forced sweep:

- **Severity labels** are normalized to the English vocabulary in a single targeted
  pass when the workflow first runs against a repo that still carries Czech labels — a
  label-value pass, distinct from prose translation.
- **`final_audit.md` section headings** are translated to the English ordering on that
  same first run.
- **Prose** converges under a **translate-on-touch** policy: a session that modifies a
  file translates that whole file in the same session.
- **Directory READMEs** follow the hub README pair policy
  (`parity.readme-language-entry-scope-fence`): `README_en.md` is the agent-facing
  English twin, `README.md` the Czech human-facing twin; both carry the
  `Language entry scope:` marker.

User-facing Czech surfaces (repo `README.md`, the GitHub issue tracker, incident
postmortems) are out of scope and unchanged.

#### Review complexity budget and splitting

Split a phase based on whether the operator can honestly complete a **coherent review
unit** under DONE MEANS DONE while preserving useful report and cache granularity —
**not** on raw line count. Line counts (`max_lines_per_task`, `max_lines_per_file` in
the repo config) are coarse guardrails and caution/diagnostic signals only.

Inputs to the split decision: file count, logical-unit boundaries, coupling/fan-out,
risk class, statefulness, stack-family differences, artifact-update load, and prior
cache coverage. Each split must cite the coherent unit being separated (an app, module,
configset, XSLT/template family, frontend feature group, high-risk boundary, or
artifact-update batch). A low-line-count change MAY still split or isolate when it
touches coupled authentication, permission, async, persistence, deployment, or
public-API behavior — cite the risk/coupling boundary in the rationale.

Sub-tasks use the **letter-suffix convention** (`T03a`, `T03b`, `T03c`, …); each
produces its own per-task report and a `review_cache.json` sub-task entry with `scope`.
The per-sub-task scope and the numeric thresholds are Tier 3 in the repo config. If a
repo chooses to make the complexity budget machine-readable, it MAY add a
`review_complexity` / split-trigger section to `review_config.toml`; this is repo-local
and not a precondition for use.

##### Per-stack analysis-family extension

A repo adds stack-specific analysis families purely through its `review_config.toml`
`phase_outputs` mapping — for example a search/index analysis output and a
transform/stylesheet analysis output both mapping to the canonical **T03 — Data-layer
analysis** phase. No fork of the canonical source is required to add a stack-specific
analysis family; the canonical phase id space stays stable across repos and stack
detail lives in config (Tier 3).

##### Three-tier authority split

- **Tier 1 — Lifecycle (hub-canonical):** phase list and intent, report layout, cache
  and findings schemas and their versioning, artefact format classification,
  mode-dispatch contract, two-pass `final_audit.md` rule.
- **Tier 2 — Policy (hub-canonical):** severity vocabulary, analysis heuristics, DONE
  MEANS DONE, GitHub-Issue cross-reference, review-complexity split rule, datetime
  discipline, bug-entry format, output-language and quotation discipline. Tier 2 names
  the *rule*; Tier 3 supplies the *value*.
- **Tier 3 — Scope (target repo `review_config.toml`):** app/module names, vendored
  exclusions, per-stack analysis families, severity thresholds, task-size guardrails,
  risk/coupling hints, key file lists, `phase_outputs`. The hub-canonical source MUST
  NOT hardcode Tier 3 scope.

#### Execution approach

For a large full pass, an orchestrating agent MAY delegate per-phase analysis to manage
context, but it remains accountable for **DONE MEANS DONE**: a phase is only `done` when
every in-scope file was directly read, not when a delegated summary was returned.
Delegated output is evidence to verify, not a substitute for the read-every-file rule.

#### Validation

- Run `review_tools.py all` (when present in the target repo) and fix inconsistencies
  (orphan IDs, severity mismatches, missing report paths) before marking a task `done`;
  run it again before finalizing `final_audit.md` (T11).
- Confirm the cache conforms to `schema_version: "2"` and that no completed task was
  invalidated by a schema field-add.
- Confirm the findings sources conform to `schema_version: "1"` and that
  `review_tools.py render --check` reports no stale Markdown twin.
- Confirm `final_audit.md` uses the canonical English section ordering and that body
  sections and changelog were updated together.
- Confirm severity values are Critical/High/Medium/Low and that bug/backlog entries
  carry a GitHub-Issue cross-reference.
- Update the rolling usage-log entry per
  the applicable governance rules.

## Bundled scripts

The enrollment bundle installs these repository-local runtime scripts:

- `.agents/scripts/review_tools.py`
