---
name: aiscr-doc-hygiene-audit
description: Run a documentation hygiene audit on this repository (or a target repo).
  Identifies duplication, drift, token inefficiency, and broken links. Use the aiscr-doc-auditor
  subagent for the analysis phase.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-doc-hygiene-audit.md -->

# aiscr-doc-hygiene-audit

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Run a documentation hygiene audit and optionally apply safe, governance-aligned fixes.

## Phase awareness

This skill operates within the **implement** phase of the OpenSpec lifecycle.
It is typically invoked as part of `/opsx:apply` or a standalone approved task.
Before executing, check for an active OpenSpec change or domain spec under
`openspec/`.
If one exists, load its context files as the primary authority.
If none exists for this domain, run `/opsx:propose`, stop for human approval,
and only continue after that change becomes the active context of the run.
It must not create new OpenSpec changes directly, promote backlog items, or
escalate scope beyond the approved task boundary.

## Context to load first

1. `openspec/specs/documentation-consistency/spec.md` — behavioral requirements and architecture
2. `AGENTS.md` — governance and scope
3. `.agents/README.md` — structure of `.agents/`
4. `.agents/plans/doc-hygiene-audit.plan.md` — execution procedures and operator runbook
5. `.agents/prompts/audit_doc_hygiene.md` — audit prompt template

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

3. Delegate analysis to the `aiscr-doc-auditor` subagent with the script output attached.
4. Classify findings as **Critical / Important / Optional**.
5. In report+safe-fixes mode, apply low-risk changes after user confirmation.
6. Write audit report to `.agents/reports/` with today's date in the filename:

   ```bash
   python -c "import datetime; print(datetime.date.today().isoformat())"
   ```

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

## Plan and workflow

`.agents/plans/doc-hygiene-audit.plan.md`

**Registry fallback:** Load openspec/specs/documentation-consistency/spec.md first for the durable behavioral contract; then run `python .agents/scripts/doc_discovery.py --output json` and `python .agents/scripts/link_check.py` for deterministic inventory; follow doc-hygiene-audit.plan.md for report-only or report+safe-fixes mode execution.

## Governance

- Do not apply any changes without presenting findings first.
- Destructive changes (deleting or archiving files) require explicit human review.
- When target is another repo, state the branch and obtain user confirmation before applying.
- Full workflow: `.agents/plans/doc-hygiene-audit.plan.md`

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow