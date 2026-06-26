---
name: aiscr-doc-hygiene-audit
description: Run a documentation hygiene audit on this repository (or a target repo).
  Identifies duplication, drift, token inefficiency, and broken links.
---

<!-- aiscr:compiled=aiscr-doc-hygiene-audit -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.github/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
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
