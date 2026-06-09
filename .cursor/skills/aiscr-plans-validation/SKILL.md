---
name: aiscr-plans-validation
description: Run the aiscr-management validation suite (plan schema, doc discovery,
  link check). Read-only; reports findings without modifying files.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-plans-validation.md -->

# aiscr-plans-validation

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Run all CI-style validation checks for this repository and report findings.

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

For every standard workflow’s prescribed context order, see `.agents/canonical_configs/references/canonical_workflows_context.md` (meta skill **`aiscr-canonical-workflows-context`**).

1. `AGENTS.md` — governance and scope
2. `.agents/README.md` — structure of `.agents/`
3. `.agents/scripts/README.md` — what each validation script does
4. `.agents/plans/plans-validation.plan.md` — validation workflow

## Steps

1. Run the full validation suite:

   ```bash
   python .agents/scripts/run_validation_all.py
   ```

   Add `--no-path-checks` to match CI behaviour (no absolute path checks).

2. If any check fails, run individual scripts for details:
   - `python .agents/scripts/validate_plans.py --strict` — plan schema and content
   - `python .agents/scripts/doc_discovery.py` — instruction-bearing file inventory
   - `python .agents/scripts/link_check.py` — internal Markdown link validation

3. Report findings in three groups:
   - **Errors** (must fix before merge)
   - **Warnings** (should fix)
   - **Info** (optional improvements)

4. **Periodic maintenance only:** For full plan lifecycle work (inventory, keep vs demote), follow `.agents/plans/plans-validation.plan.md` **Step 8** and update `.agents/canonical_configs/references/plan_demotion_policy.md` — not part of every validation run.

## Iron Law

**IRON LAW:** `NEVER AUTO-FIX VALIDATION ERRORS IN PLAN FILES. THIS WORKFLOW IS REPORT-ONLY. WAIT FOR USER APPROVAL BEFORE APPLYING ANY CHANGES.`

No exceptions. The scripts are read-only; any fix requires a separate user-approved action.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The plan has a broken link — I'll fix it now since I'm already here" | Report the finding; do not modify any plan file as part of this workflow. |
| "The validation error is a trivial typo — I'll apply the one-line fix" | All fixes require explicit user approval; report only, then ask. |
| "The `--no-path-checks` flag is optional — I'll omit it for thoroughness" | Use `--no-path-checks` to match CI behaviour; only add `--with-path-checks` when explicitly requested for a stricter local run. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Validation run completed without modifying any plan file.
- [ ] All findings grouped (Errors / Warnings / Info) and reported to user.
- [ ] No auto-fixes applied; fix proposals presented separately if needed.
- [ ] Periodic lifecycle work (Step 8) confirmed as out of scope for this run (or explicitly in scope per user request).

## Plan and workflow

`.agents/plans/plans-validation.plan.md`

**Registry fallback:** Run python .agents/scripts/run_validation_all.py (or individual scripts) per plan; no sync without approval.

## Governance

- These scripts are **read-only** (no mutations). Run without approval.
- Do not run `sync_agent_configs.py` — that requires explicit human approval.
- Full workflow: `.agents/plans/plans-validation.plan.md`

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow