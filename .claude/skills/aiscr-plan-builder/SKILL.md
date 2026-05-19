---
name: aiscr-plan-builder
description: Create a new plan under .agents/plans/ that follows the AIS CR schema
  and governance. Uses plan_builder.md to generate the plan, then validates and registers
  it.
disable-model-invocation: true
user-invocable: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-plan-builder.md -->

# aiscr-plan-builder

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-plan-builder/SKILL.md`](.cursor/skills/aiscr-plan-builder/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.claude/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Create a new plan under .agents/plans/ that follows the AIS CR schema and governance. Uses plan_builder.md to generate the plan, then validates and registers it.

Generate a new plan file under `.agents/plans/` following the AIS CR plan schema and governance.

## Phase awareness

This skill is a **meta/orchestration** helper that supports the OpenSpec lifecycle
without participating in phase transitions. It loads context, builds plans, or
maintains registries. It does not create OpenSpec changes or execute implementation tasks.
Check for relevant domain specs when the task touches governed capabilities.
If no relevant domain spec exists, consider running `/opsx:propose` to formalize the capability before execution work begins.

## Workflow routing

Load [`.cursor/skills/aiscr-plan-builder/SKILL.md`](.cursor/skills/aiscr-plan-builder/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/plan-builder.plan.md`

**Registry fallback:** Read plan_builder.md; follow AIS CR plan schema manually.

## Valid next steps

- `/aiscr-plans-validation` -- validate the newly created plan
- `/aiscr-canonical-workflows-context` -- load context for a specific workflow
- `/opsx:apply <slug>` -- implement tasks from an OpenSpec change
