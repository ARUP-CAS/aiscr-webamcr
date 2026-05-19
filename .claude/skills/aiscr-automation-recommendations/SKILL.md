---
name: aiscr-automation-recommendations
description: Maintain .agents/canonical_configs/references/automation_recommendations.md
  as a living document. Use when the user asks to update automation recommendations
  or review global automation guidance.
disable-model-invocation: true
user-invocable: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-automation-recommendations.md -->

# aiscr-automation-recommendations

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-automation-recommendations/SKILL.md`](.cursor/skills/aiscr-automation-recommendations/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.claude/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Maintain .agents/canonical_configs/references/automation_recommendations.md as a living document. Use when the user asks to update automation recommendations or review global automation guidance.

Maintain `.agents/canonical_configs/references/automation_recommendations.md` as a living document for AIS CR.

**Requirement authority:** [`openspec/specs/openspec-requirement-governance/spec.md`](/openspec/specs/openspec-requirement-governance/spec.md) (automation patterns section) — durable behavioral requirements for automation patterns.

## Phase awareness

This skill is a **meta/orchestration** helper that supports the OpenSpec lifecycle
without participating in phase transitions. It loads context, builds plans, or
maintains registries. It does not create OpenSpec changes or execute implementation tasks.
Check for relevant domain specs when the task touches governed capabilities.
If no relevant domain spec exists, consider running `/opsx:propose` to formalize the capability before execution work begins.

## Workflow routing

Load [`.cursor/skills/aiscr-automation-recommendations/SKILL.md`](.cursor/skills/aiscr-automation-recommendations/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

_No backing plan file;_ follow fallback and governance.

**Registry fallback:** Load openspec/specs/openspec-requirement-governance/spec.md first for the durable behavioral contract; skill is spec-first.

## Valid next steps

- `/aiscr-hooks-governance` -- review and harden automation hooks
- `/aiscr-plugins-enablement` -- enable relevant plugins and document fallbacks
- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
