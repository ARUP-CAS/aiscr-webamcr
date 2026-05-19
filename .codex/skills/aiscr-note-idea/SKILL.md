---
name: aiscr-note-idea
description: Capture an idea as an OpenSpec backlog change using the lightweight backlog
  schema, then stop before promotion.
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-note-idea.md -->

# aiscr-note-idea

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-note-idea/SKILL.md`](.cursor/skills/aiscr-note-idea/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.codex/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Capture an idea as an OpenSpec backlog change using the lightweight backlog schema, then stop before promotion.

Capture one new idea as an OpenSpec backlog change under `openspec/changes/`
without starting planning or promotion into the governance-driven workflow.

## Phase awareness

This skill operates at the **ideation** layer of the OpenSpec lifecycle.
It captures a new idea as a backlog change without planning or promotion.
After completing its workflow, it hands off to `/aiscr-plan-from-idea` for
governance-driven promotion or `/opsx:continue` for manual artifact work.
It must not promote, create governance-driven artifacts, or cross into planning.

## Workflow routing

Load [`.cursor/skills/aiscr-note-idea/SKILL.md`](.cursor/skills/aiscr-note-idea/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

_No backing plan file;_ follow fallback and governance.

**Registry fallback:** Create `openspec/changes/<slug>/` with schema `backlog`, fill `proposal.md` from the backlog template, refresh `.agents/backlog-overview.md`, and stop before planning or promotion.

## Valid next steps

- `/aiscr-plan-from-idea <slug>` -- promote this backlog item into the AIS CR planning-first governance-driven flow
- `/opsx:continue <slug>` -- continue artifact work on this change manually
- `/aiscr-note-idea` -- capture another idea as a separate backlog item
