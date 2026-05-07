---
name: aiscr-canonical-workflows-context
description: Load the prescribed context for a named aiscr-management workflow before
  executing it. Use this when starting a standard management task (config sync, doc
  audit, plan validation, governance bootstrap, model mapping update, etc.) to ensure
  you read the right files in the right order.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-canonical-workflows-context.md -->

# aiscr-canonical-workflows-context

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-canonical-workflows-context/SKILL.md`](.cursor/skills/aiscr-canonical-workflows-context/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.gemini/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Load the prescribed context for a named aiscr-management workflow before executing it. Use this when starting a standard management task (config sync, doc audit, plan validation, governance bootstrap, model mapping update, etc.) to ensure you read the right files in the right order.

Thin router: map the user’s task to **one row** in the canonical reference, then load that row’s **Context (order)** before executing its plan or script.

This skill is execution-facing only. If the task is to edit the workflow registry, workflow reference, or generated skill surfaces, use **`/aiscr-canonical-workflows-context-maintenance`** instead.

## Phase awareness

This skill is a **meta/orchestration** helper that supports the OpenSpec lifecycle
without participating in phase transitions. It loads context, builds plans, or
maintains registries. It does not create OpenSpec changes or execute implementation tasks.
Check for relevant domain specs when the task touches governed capabilities.
If no relevant domain spec exists, consider running `/opsx:propose` to formalize the capability before execution work begins.

## Workflow routing

Load [`.cursor/skills/aiscr-canonical-workflows-context/SKILL.md`](.cursor/skills/aiscr-canonical-workflows-context/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/canonical-workflows-context.plan.md`

**Registry fallback:** Read canonical_workflows_context.md directly and load listed context in order.

## Valid next steps

- `/aiscr-<workflow>` -- execute the loaded workflow skill
- `/opsx:apply <slug>` -- implement tasks from an OpenSpec change
- `/aiscr-canonical-workflows-context-maintenance` -- update the workflow registry itself
