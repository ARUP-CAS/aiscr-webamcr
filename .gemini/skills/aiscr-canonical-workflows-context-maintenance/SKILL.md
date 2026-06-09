---
name: aiscr-canonical-workflows-context-maintenance
description: 'Run the canonical-workflows-context maintenance plan: update the workflow
  registry and reference, keep the execution and maintenance workflow skills aligned,
  refresh direct doc consumers, and validate the touched workflow surfaces.'
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-canonical-workflows-context-maintenance.md -->

# aiscr-canonical-workflows-context-maintenance

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-canonical-workflows-context-maintenance/SKILL.md`](.cursor/skills/aiscr-canonical-workflows-context-maintenance/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.gemini/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Run the canonical-workflows-context maintenance plan: update the workflow registry and reference, keep the execution and maintenance workflow skills aligned, refresh direct doc consumers, and validate the touched workflow surfaces.

Run the reusable maintenance workflow defined in `.agents/plans/canonical-workflows-context-maintenance.plan.md`.

## Phase awareness

This skill is a **meta/orchestration** helper that supports the OpenSpec lifecycle
without participating in phase transitions. It loads context, builds plans, or
maintains registries. It does not create OpenSpec changes or execute implementation tasks.
Check for relevant domain specs when the task touches governed capabilities.
If no relevant domain spec exists, consider running `/opsx:propose` to formalize the capability before execution work begins.

## Workflow routing

Load [`.cursor/skills/aiscr-canonical-workflows-context-maintenance/SKILL.md`](.cursor/skills/aiscr-canonical-workflows-context-maintenance/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/canonical-workflows-context-maintenance.plan.md`

**Registry fallback:** Load context; follow canonical-workflows-context-maintenance.plan.md manually.

## Valid next steps

- `/aiscr-canonical-workflows-context` -- reload context to verify the updated registry
- `/aiscr-plans-validation` -- validate plan schema and context paths after changes
- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
