---
name: aiscr-plans-validation
description: Run the aiscr-management validation suite (plan schema, doc discovery,
  link check). Read-only; reports findings without modifying files.
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-plans-validation.md -->

# aiscr-plans-validation

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-plans-validation/SKILL.md`](.cursor/skills/aiscr-plans-validation/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.codex/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Run the aiscr-management validation suite (plan schema, doc discovery, link check). Read-only; reports findings without modifying files.

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

## Workflow routing

Load [`.cursor/skills/aiscr-plans-validation/SKILL.md`](.cursor/skills/aiscr-plans-validation/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/plans-validation.plan.md`

**Registry fallback:** Run python .agents/scripts/run_validation_all.py (or individual scripts) per plan; no sync without approval.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
