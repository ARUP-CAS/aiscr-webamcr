---
name: aiscr-doc-hygiene-audit
description: Run a documentation hygiene audit on this repository (or a target repo).
  Identifies duplication, drift, token inefficiency, and broken links.
disable-model-invocation: true
user-invocable: true
effort: high
---

<!-- aiscr:compiled=aiscr-doc-hygiene-audit -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.claude/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-doc-hygiene-audit — documentation hygiene audit

Run a documentation hygiene audit and optionally apply safe, governance-aligned fixes.

**When to use vs alternatives:** Use for **structural and link hygiene** (duplication, drift, discovery classification, broken references, token-heavy patterns, report inventory). For **language, typos, CZ/EN README pairs, and GFM readability** as the primary goal, use **`/aiscr-docs-language-review`** instead (`docs-language-quality` spec).

## Phase awareness

This skill operates within the **implement** phase of the OpenSpec lifecycle.
It is typically invoked as part of `/opsx:apply` or a standalone approved task.
Before executing, check for an active OpenSpec change or domain spec under
`openspec/`.
If one exists, load its context files as the primary authority.
If none exists for this domain, run `/opsx:propose`, stop for human approval,
and only continue after that change becomes the active context of the run.
It must not create new **governance-driven** OpenSpec changes directly, promote backlog items, or
escalate scope beyond the approved task boundary, except for the backlog-only handoff governed by
the workflow contract summarized in this compiled skill after explicit per-run approval (see **Report-to-backlog handoff** below).

## Report-to-backlog handoff

When the audit leaves actionable deferred findings that need scheduling (not fixed inline under an approved safe-fix run, and not informational or duplicate-only), follow the workflow contract summarized in this compiled skill (*Documentation hygiene reports hand off actionable findings*).

1. After the audit report path is known, list backlog candidates (proposed slug, stable finding keys, short title, grouping rationale).
2. Ask for **explicit per-run** approval to emit OpenSpec backlog items. Running the audit alone does not approve backlog writes.
3. If approved, draft the backlog candidate body inline — candidate slug, a one-line summary, `**Source report:**` (the approved report path), and `**Finding keys:**` — without copying sensitive evidence, then stop. Promotion into the management hub's backlog (creating the OpenSpec backlog change and refreshing the backlog overview) is a separate, explicit hub action by a maintainer; this workflow does not create hub changes or auto-invoke hub commands.
4. Name spawned backlog slugs in the audit report, or state why no backlog item was created.

Do not promote spawned backlog or implement it (`/opsx:apply`) inside this skill.

## Context to load first

1. the workflow contract summarized in this compiled skill — behavioral requirements and architecture
2. the workflow contract summarized in this compiled skill — backlog emission contract (when emitting follow-ups)
3. `AGENTS.md` — governance and scope
4. `.agents/README.md` — structure of `.agents/`
5. the embedded execution plan below — execution procedures and operator runbook
6. `.agents/prompts/audit_doc_hygiene.md` — audit prompt template

## Modes

- **Report-only** (default): identify issues, estimate token/maintenance savings, do not change files.
- **Report+safe-fixes**: apply low-risk cleanups where the plan classifies them as safe. Destructive changes (deletion, archival) always require explicit human confirmation.

## Steps

1. Ask the user: target repo (default: this repo), mode (report-only or report+safe-fixes).
2. Run prerequisite scripts (read-only):

   ```bash
   python .agents/scripts/doc_discovery.py
   python .agents/scripts/link_check.py
   ```

   Discovery classifies OpenSpec surfaces in three classes — `openspec_specs` (durable
   capability specs under the workflow contract summarized in this compiled skill), `openspec_active_changes` (active
   change artifacts under `openspec/changes/<slug>/`), and `openspec_archived_changes`
   (archived artifacts under `openspec/changes/archive/`) — so durable requirement
   owners stay distinguishable from change-local context and historical records.
   Link-check covers OpenSpec Markdown by default so broken file or heading
   references between OpenSpec specs, change artifacts, `.agents/`, and assistant
   entry surfaces are reported alongside other hygiene findings.

3. Analyze the script output against the audit checks and preserve evidence for each finding.
4. Classify findings as **Critical / Important / Optional**.
5. **Reports and long-lived assets:** when the audit includes `.agents/reports/**`, classify report-like assets as keep, compress, archive, or remove candidates. Compression is the intermediate step before destructive cleanup: preserve source path, retained decisions or conclusions, omitted-detail category, and follow-up/archive pointer. Old or heavy usage logs are in scope, but their required compliance fields and model/runtime accountability must survive. Prefer a lightweight hybrid pattern: a short report-local status header or pointer plus a maintained summary/index entry when cross-report scanning is useful.
6. **Hub-only:** when the target is the management hub (or another repo whose `documentation-consistency` spec requires it), additionally classify each duplication or drift finding on the **prose ownership × source** axes per check C9 in `audit_doc_hygiene.md`. Each finding records `ownership_class ∈ {canonical, summary, historical, obsolete}` and `source ∈ {hand-written, generated}`. Findings with `source = generated` SHALL route the recommended edit to the generator or canonical source rather than the emitted file. The ownership labels live in the audit report itself; they are NOT persisted to a separate registry. **Backlog coordination:** when C9 findings touch `.agents/reports/**` or the identifiers and references stated in this workflow, consult the active backlog registry (`.agents/backlog-overview.md` and `openspec/changes/` for current proposals) and decide whether to absorb, sequence, or defer any item that already owns the cleanup. For `ai-session-learnings.md`, classify reviewed entries as keep, merge, distribute, or retire; distributed entries must name the narrower contextual owner, and retired entries need an explicit rationale. Do not name specific backlog slugs in this skill — the backlog set is dynamic; load the registry at audit time.
7. In report+safe-fixes mode, apply low-risk changes after user confirmation.
8. Write audit report to `.agents/reports/` with today's date in the filename:

   ```bash
   python -c "import datetime; print(datetime.date.today().isoformat())"
   ```

<!-- aiscr:gen:id=guardrails -->
## Iron Law

**IRON LAW:** `NEVER MODIFY ANY FILE DURING A HYGIENE AUDIT WITHOUT FIRST PRESENTING ALL FINDINGS TO THE USER. DEFAULT MODE IS REPORT-ONLY.`

No exceptions. Changes are only permitted in report+safe-fixes mode and only after the user explicitly confirms each finding class.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "This is clearly a broken link — I'll fix it now" | Classify and present all findings first; apply fixes only in report+safe-fixes mode with user confirmation. |
| "The audit is done — I'll write the report and fix the obvious issues at the same time" | Write the report first; fixes are a separate step requiring explicit entry into report+safe-fixes mode. |
| "Deleting this stale file is clearly safe" | Destructive changes require explicit per-item user confirmation regardless of mode. |

## Verification before completion

Before claiming this workflow complete:

- [ ] All findings presented (Critical / Important / Optional) before any file was modified.
- [ ] No silent auto-fixes applied.
- [ ] Audit report written to `.agents/reports/` with date-stamped filename.
- [ ] Destructive changes (deletion, archival) have explicit per-item user confirmation.
- [ ] If sibling repo targeted: branch stated and user confirmed before any write.
<!-- aiscr:endgen -->

## Governance

- Do not apply any changes without presenting findings first.
- Destructive changes (deleting or archiving files) require explicit human review.
- When target is another repo, state the branch and obtain user confirmation before applying.
- Full workflow: the embedded execution plan below

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- Read the identifiers and references stated in this workflow and follow the **Usage** section before loading a different workflow's context.

## Embedded execution plan

### Plan: Documentation Hygiene and Governance Alignment

> **OpenSpec migration:** Persistent behavioral requirements for this workflow now live in the workflow contract summarized in this compiled skill. This `.plan.md` file remains the reusable execution and governance layer for aiscr-management. See the identifiers and references stated in this workflow.

#### Context

This plan is for running a **documentation hygiene and governance alignment** pass in an AIS CR repository.
It uses `.agents/prompts/audit_doc_hygiene.md` as the main execution prompt and adds a structured lifecycle and validation layer around it.

Typical targets include application repositories (`aiscr-webamcr`, `aiscr-digiarchiv-2`), documentation sites (`aiscr-webamcr-help`, `aiscr-api-home`), data tools (`aiscr-oao`), and this management repo itself (`aiscr-management`). This plan is typically orchestrated by the **aiscr-doc-hygiene-audit** skill (see the identifiers and references stated in this workflow); the plan remains usable without the skill.

#### Goals

- Identify and fix **duplication, drift, and broken cross‑references** in documentation and config files.
- Clarify **who owns which information** (governance vs operational vs prompts).
- Improve **token efficiency** for AI‑injected instruction files (align with the general token/efficiency principle in [AGENTS.md](../../../AGENTS.md) and [CLAUDE.md](../../../CLAUDE.md)).
- Reduce **long-term cost and noise** from obsolete reports and instruction assets (e.g. under `.agents/reports/`) by evaluating them for cleanup or consolidation based on future cost-benefit for agent runs.
- Keep the identifiers and references stated in this workflow as a compact learning index by classifying reviewed entries as keep, merge, distribute, or retire during management-hub hygiene runs.

#### Scope and assumptions

- In scope:
  - Files listed in the prompt’s C1 discovery stage (README*, CONTRIBUTING, AGENTS, CLAUDE, prompts, `.agents/config/*`, etc.).
  - Governance and AI‑instruction files for both humans and agents.
  - **Reports** (e.g. under `.agents/reports/`) for **analysis** as long-lived assets; they are not automatically deleted — cleanup actions are gated behind the run mode (report-only vs report+safe-fixes) and human decisions.
- Out of scope:
  - Changing the underlying business rules or project conventions (only how they are documented and referenced).
  - Refactoring application code (beyond what’s necessary to fix path or config references).
- Assumptions:
  - `.agents/prompts/audit_doc_hygiene.md` is present or can be copied into the repo.
  - The repo already has at least a minimal governance baseline (or the `governance-bootstrap` plan will be applied first).

#### Execution approach

- Inventory instruction-bearing files and confirm the sets found by the prompt.
- Trace where particular rules or paths are used in code vs documentation when resolving drift.
- After fixes, double-check that no new inconsistencies were introduced and that governance responsibilities are clear.

#### Steps

##### Step 1 — Discover instruction-bearing files (run scripts first)

- Run the **doc discovery script** (e.g. `python .agents/scripts/doc_discovery.py --output json`) to get a deterministic list of instruction-bearing files with line counts and per-entry classification `category`. If the repo has a link-check script (e.g. `python .agents/scripts/link_check.py`), run it and fix any broken refs.
- Use the script output as the canonical C1 file list. Record languages and apparent audiences per file (agent can augment). Explicitly note **report-like assets** (e.g. from discovery output under `.agents/reports/`) so they can be evaluated in the reports-cleanup phase (C8).
- **OpenSpec coverage:** discovery classifies durable specs (`openspec_specs`), active OpenSpec change artifacts (`openspec_active_changes`), and archived change artifacts (`openspec_archived_changes`). Treat OpenSpec specs as durable requirement owners for migrated domains, treat active change artifacts as change-local context (proposal/design/tasks/delta specs — not yet canonical), and treat archived change artifacts as historical records for C8 evaluation, not current operating guidance.
- If no script exists, fall back to the C1 File Discovery phase from the prompt (README variants, CONTRIBUTING, AGENTS/CLAUDE, CODEOWNERS, `.agents/prompts/*`, `.agents/config/*`, `.agents/reports/*`, the workflow contract summarized in this compiled skill, active and archived `openspec/changes/**/*.md`, auto‑memory files, etc.).

##### Step 2 — Run full documentation hygiene audit

- Using `.agents/prompts/audit_doc_hygiene.md`, run the full audit. Attach the discovery and link-check outputs from Step 1 as input so C1 and C5 are reproducible.
- Agent covers: Audience & responsibility mapping (C2), Duplication detection (C3), Drift detection (C4), Cross‑reference integrity (C5, using link-check result as baseline), Token efficiency (C6), Governance rules presence (C7), **Reports & long-lived assets cleanup (C8)**, and **Prose ownership classification (C9)** when the target is the management hub or another repo whose `documentation-consistency` spec requires the ownership × source axes. For management-hub runs that include the identifiers and references stated in this workflow, C9 also classifies reviewed learning entries as keep, merge, distribute, or retire.
- Capture the generated report in `.agents/reports/` (for example `doc_hygiene_<date>.md`). The report date and filename must use the current date from a deterministic command (e.g. `python -c "import datetime; print(datetime.date.today().isoformat())"`); do not infer or guess the date.

##### Step 3 — Classify and prioritise findings; evaluate reports and long-lived assets

- Group findings into:
  - **Critical/FAIL** – contradictions, broken references, governance drift.
  - **Important/WARN** – redundant duplication that risks future drift.
  - **Optional** – mainly token efficiency and minor structural clean‑ups.
- For each finding, decide:
  - Which file will be the **canonical owner** of the information.
  - Which files should use **cross‑references** instead of duplicated content.
- **Evaluate reports and long-lived assets** (C8): For files under `.agents/reports/` and similar long-lived instruction-style documents:
  - Identify large or outdated report files; group them by category (large inventories, dated audits, automation notes, overhead snapshots, incidents, release notes, usage logs, and other report-like assets).
  - For each, assess **token footprint** (e.g. from discovery line counts), **drift risk** (last-modified or superseded-by cues), and **governance relevance**.
  - Classify the recommended lifecycle action as keep, compress, or remove. Compression is the intermediate step before destructive cleanup: preserve retained decisions, source path, omitted-detail category, and follow-up pointer before recommending removal.
  - For usage logs, include old and heavy entries in scope, but preserve the minimal compliance fields (`When`, `Agent / runtime`, `Model / backend`, `What`, `Impacted`, `Close-out`) and any verification evidence or pointer when narrative detail is compressed.
  - Use the **index-first** placement pattern (see `.agents/reports/README_en.md` → *Report compression lifecycle*): the default outcome for a stale/superseded/obsolete report is to remove it and record it in `.agents/reports/historical-index.md` (date, original path, one-line scope), leaving the content recoverable from git history. Retain a report in place with a short status header *only* when it carries substantive load-bearing decisions or reference content. Do **not** leave per-file stubs.
- **Evaluate session learnings** when the target is the management hub and the identifiers and references stated in this workflow is in scope:
  - Classify reviewed entries as keep, merge, distribute, or retire.
  - For distributed entries, name the narrower contextual owner (rule, reference, prompt, skill source, script README, or report pointer).
  - For retired entries, record the rationale before removing or reducing the entry.

##### Step 4 — Apply governance-alignment fixes

- Following the prompt’s FIX MODE guidance:
  - Apply auto‑fixable changes without extra confirmation (e.g. removing embedded config blocks where live config exists).
  - For impactful changes (file restructuring, major README edits), plan and apply edits in small, reviewable steps.
- **Run mode and reports:**
  - In **report-only mode**, fixes for reports are limited to rewordings or adding warnings/pointers (e.g. "superseded by X"); do not delete or move report files.
  - In **report+safe-fixes mode**, permit small structural changes only: e.g. adding a short status header to a report that is being **retained in place**, adding cross-references to newer canonical docs, or consolidating obviously redundant synthetic reports while preserving critical incident history and usage-log accountability. **File removal stays out of auto-fix scope** — it remains a recommendation only and requires explicit human approval.
  - When removal **is** approved, the mechanism is **index-first**: remove the file and add a row to `.agents/reports/historical-index.md` (date, original path, one-line scope). Do not replace the file with a per-file stub. Protected categories (incidents, postmortems, formal governance, active operational) are never removed; a recent working window is kept full until the next audit cycle.
- Typical fixes (non-report):
  - Move branch/workflow rules entirely into `CONTRIBUTING.md` with short references elsewhere.
  - Ensure `AGENTS.md` only contains governance, not operational procedures.
  - Move duplicated, detailed operational instructions into `review_codebase.md` or equivalent.
  - Reduce `ai-session-learnings.md` entries to compact durable findings and move detailed or duplicated guidance to the contextual owner named during classification.

##### Step 5 — Update or introduce governance sections

- If missing or outdated, add a **documentation governance** section (or update an existing one) that clearly states:
  - Which file owns which type of information.
  - Where duplication is allowed (e.g. brief summaries for user‑facing READMEs).
  - Where it is explicitly forbidden.
- Ensure this section is consistent with `AGENTS.md` and this management repo’s expectations.

##### Step 6 — Validation

- Re‑run the **discovery and link-check scripts** and confirm no regressions (e.g. new broken refs, missing files).
- Re‑run at least a **partial audit** (C2–C8) and confirm statuses have improved and no new FAILs were introduced.
- Confirm the final audit report includes a **"Reports & long-lived assets"** subsection (C8) summarising candidates and recommended actions.
- Review the result:
  - Sanity-check the updated documentation structure.
  - Verify that AI-injected files (e.g. `CLAUDE.md`, `.cursor/rules`) are lean and reference, rather than repeat, governance docs.

#### Validation

- Re-run the `audit_doc_hygiene` workflow (at least partially) and confirm:
  - that critical findings have been addressed,
  - that no new FAIL-level issues were introduced,
  - and that the report includes the **C8 — Reports & long-lived assets cleanup** section with candidates and recommended actions.
- Review the updated documentation set:
  - check consistency of ownership and cross-references,
  - ensure AI-injected files remain short and point back to governance docs instead of duplicating them.

**Concrete verification steps (extended audit with C8):**

1. `python .agents/scripts/doc_discovery.py --output json` — confirm reports (e.g. under `.agents/reports/`) are listed with line counts for token approximation.
2. `python .agents/scripts/link_check.py` — ensure no broken same-repo links (exit 0).
3. Run the full audit using `.agents/prompts/audit_doc_hygiene.md` and verify the output includes the **C8 — Reports & long-lived assets cleanup** section with a table of candidates and expected token/maintenance savings.
4. `python -m unittest discover -s tests -v` — ensure tests for `doc_discovery.py` and `link_check.py` (and other validation scripts) pass without regressions.

#### Notes / Adaptation per repo

- In heavily governed repos like `aiscr-webamcr` or `aiscr-digiarchiv-2`, expect more findings related to historical drift; plan multiple audit iterations if needed.
- In newer or simpler repos, focus on establishing clear governance responsibilities even if duplication is currently low.
- In this management repo (`aiscr-management`), treat `.agents/` documentation as primary and avoid moving governance into `.cursor`, `.claude`, or `.codex` configs.

#### Options (planning phase)

**Delivery (choose before any commit or push):**

- **(A)** Create a branch and open a **draft** PR for the changes (recommended).
- **(B)** Create a branch only (no PR).
- **(C)** Local changes only (no branch, no push).

Do not commit or push until the user has chosen.

**Scope / target:** Confirm with the user which repo(s) or scope for this run (e.g. single repo, list of repos). Do not assume from context.

**Sibling-repo branch:** When the target is another repo, state which branch will be used in the target repo and obtain user confirmation before applying changes.

#### Plan refinement / Autoupdate

After completing this plan in a repository:

- Recommended if relevant: apply updates to this `.plan.md` (e.g. audit or fix workflow, better grouping of findings or clearer governance alignment patterns); validate changes accordingly and verbosely.
- Avoid encoding repository‑specific findings directly into the plan; capture those in the repo’s own reports instead.
- If some checks or steps are consistently not useful or missing, refine the `todos` and `Steps` sections so future audits are more efficient.
- Where the plan relies on prompts or helper scripts (for example `audit_doc_hygiene.md`), apply updates to those prompts or tools and validate accordingly (verbose validation).

## Bundled scripts

The enrollment bundle installs these repository-local runtime scripts:

- `.agents/scripts/doc_discovery.py`
- `.agents/scripts/link_check.py`
- `.agents/prompts/audit_doc_hygiene.md`
