---
name: aiscr-automation-recommendations
description: Maintain .agents/canonical_configs/references/automation_recommendations.md
  as a living document. Use when the user asks to update automation recommendations
  or review global automation guidance.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-automation-recommendations.md -->

# aiscr-automation-recommendations

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Maintain `.agents/canonical_configs/references/automation_recommendations.md` as a living document for AIS CR.

**Requirement authority:** [`openspec/specs/openspec-requirement-governance/spec.md`](/openspec/specs/openspec-requirement-governance/spec.md) (automation patterns section) — durable behavioral requirements for automation patterns.

## Phase awareness

This skill is a **meta/orchestration** helper that supports the OpenSpec lifecycle
without participating in phase transitions. It loads context, builds plans, or
maintains registries. It does not create OpenSpec changes or execute implementation tasks.
Check for relevant domain specs when the task touches governed capabilities.
If no relevant domain spec exists, consider running `/opsx:propose` to formalize the capability before execution work begins.

## Context to load first

1. `AGENTS.md` — governance and scope
2. [`openspec/specs/openspec-requirement-governance/spec.md`](/openspec/specs/openspec-requirement-governance/spec.md) — **primary authority** for automation pattern requirements
3. `.agents/canonical_configs/references/automation_recommendations.md` — document to maintain

## Steps

1. Ask the user: what triggered the update (maintainer feedback, new observations from repos, scheduled review).
2. Read current `automation_recommendations.md` and identify sections that need updating.
3. Collect input: maintainer feedback or observations from actual automation setups in repos.
4. Propose updates to the document; present diff before applying.
5. Apply approved changes; note follow-up issues or PRs for affected repos where applicable.
6. Note whether a next review cycle should be scheduled.

## Iron Law

**IRON LAW:** `NEVER OVERWRITE automation_recommendations.md WITHOUT FIRST READING THE FULL CURRENT CONTENT AND PROPOSING A DIFF TO THE USER.`

No exceptions. This file is a shared reference for all AIS CR agents — silent overwrites can corrupt guidance across all workflows.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "I'm just adding a section — no need to read the whole file" | Read the full current file; check for duplicate sections and conflicting guidance. |
| "The change is small — I'll just apply it" | Propose the diff to the user before applying any change. |
| "This is a trusted update from the plan" | Still requires reading full content and presenting diff for approval. |

## Verification before completion

Before claiming this workflow complete, confirm:

- [ ] Full current `automation_recommendations.md` was read before any edits.
- [ ] Proposed diff was presented to user and explicitly approved.
- [ ] No sections were silently overwritten or removed.
- [ ] Document is internally consistent — no duplicate or contradictory sections.

## Plan and workflow

_No backing plan file;_ follow fallback and governance.

**Registry fallback:** Load openspec/specs/openspec-requirement-governance/spec.md first for the durable behavioral contract; skill is spec-first.

## Governance

- Do **not** run high-impact scripts unless the user explicitly asks.
- Present proposed changes before applying; do not bulk-overwrite.
- **Spec is primary authority:** When the spec and this skill differ, follow the spec and surface the discrepancy.

## Valid next steps

- `/aiscr-hooks-governance` -- review and harden automation hooks
- `/aiscr-plugins-enablement` -- enable relevant plugins and document fallbacks
- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change