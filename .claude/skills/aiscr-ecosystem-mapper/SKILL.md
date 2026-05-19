---
name: aiscr-ecosystem-mapper
description: Create, refresh, or update the AIS CR ecosystem map. Use when the user
  asks to update the ecosystem map, add a repo to the map, refresh the map, or check
  ecosystem map consistency.
disable-model-invocation: true
user-invocable: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-ecosystem-mapper.md -->

# aiscr-ecosystem-mapper

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-ecosystem-mapper/SKILL.md`](.cursor/skills/aiscr-ecosystem-mapper/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.claude/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Create, refresh, or update the AIS CR ecosystem map. Use when the user asks to update the ecosystem map, add a repo to the map, refresh the map, or check ecosystem map consistency.

Create, refresh, or update `.agents/canonical_configs/references/ecosystem_map.md` so it remains the single source of truth for AIS CR sibling repositories.

## Phase awareness

This skill is a **meta/orchestration** helper that supports the OpenSpec lifecycle
without participating in phase transitions. It loads context, builds plans, or
maintains registries. It does not create OpenSpec changes or execute implementation tasks.
Check for relevant domain specs when the task touches governed capabilities.
If no relevant domain spec exists, consider running `/opsx:propose` to formalize the capability before execution work begins.

## Workflow routing

Load [`.cursor/skills/aiscr-ecosystem-mapper/SKILL.md`](.cursor/skills/aiscr-ecosystem-mapper/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

_No backing plan file;_ follow fallback and governance.

**Registry fallback:** Read ecosystem_map.md; update manually per governance.

## Valid next steps

- `/aiscr-config-sync` -- sync configurations to sibling repos after map updates
- `/aiscr-canonical-workflows-context` -- load context for a specific workflow
- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
