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
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Run the reusable maintenance workflow defined in `.agents/plans/canonical-workflows-context-maintenance.plan.md`.

## Phase awareness

This skill is a **meta/orchestration** helper that supports the OpenSpec lifecycle
without participating in phase transitions. It loads context, builds plans, or
maintains registries. It does not create OpenSpec changes or execute implementation tasks.
Check for relevant domain specs when the task touches governed capabilities.
If no relevant domain spec exists, consider running `/opsx:propose` to formalize the capability before execution work begins.

## Context to load first

1. `AGENTS.md` — governance and scope
2. `.agents/canonical_configs/references/canonical_workflows_context.md` — current workflow–context reference
3. `.agents/canonical_configs/references/aiscr_skillset_mapping.md` — skill inventory
4. `.agents/canonical_configs/references/subagent_vanilla_templates_and_mapping.md` — subagent mapping
5. `.agents/plans/canonical-workflows-context-maintenance.plan.md` — maintenance plan

## Relationship to `/aiscr-canonical-workflows-context`

- **`/aiscr-canonical-workflows-context`** — load context to *run* one of the standard workflows.
- **`/aiscr-canonical-workflows-context-maintenance`** — *run the maintenance plan* that updates the workflow registry/reference pair, keeps the workflow skills aligned, and validates the touched surfaces.

## Steps (follow the plan in order)

1. **Step 1 — Update the reference**: add/update rows in `canonical_workflows_context.md` for any new or changed workflows.
2. **Step 2 — Maintain the registry and execution skill**: update the workflow registry/reference pair and keep the execution-facing workflow skill aligned when the routing contract changes.
3. **Step 3 — Maintain the workflow skill sources**: keep `aiscr-canonical-workflows-context` and `aiscr-canonical-workflows-context-maintenance` pointed at the correct backing plans and responsibility boundaries.
4. **Step 4 — Integrate into docs**: update `aiscr_skillset_mapping.md`, `AGENTS.md`, and direct plan listings without creating a second workflow-to-plan index.
5. **Step 5 — Regenerate touched surfaces**: run targeted `generate_workflow_skills.py` for the two workflow slugs and regenerate touched governance-rule stems when the same change set requires it.
6. **Step 6 — Run targeted validation**: `validate_plans.py --strict`, `validate_workflows_context_paths.py`, `validate_tool_parity.py`, and `link_check.py --output text`.

## Iron Law

**IRON LAW:** `NEVER OVERWRITE canonical_workflows_context.md WITHOUT FIRST READING THE FULL CURRENT CONTENT AND PROPOSING THE CHANGES TO THE USER AS A DIFF.`

No exceptions. This file is the navigation backbone for all standard AIS CR workflows — silent overwrites corrupt guidance for every downstream skill.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "I'll just add the new workflow row — it's additive, no need to read the whole file" | Read the full file first; check for duplicate entries, ordering conflicts, or stale rows. |
| "I'll update the generated skill trees by hand" | Edit the canonical workflow source files, then regenerate the touched workflow slugs. |
| "Skill quality issues are obvious — I'll fix them directly" | Present findings; apply only after user confirmation per change. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Full current `canonical_workflows_context.md` read before any edits.
- [ ] Diff of changes proposed and explicitly approved by user.
- [ ] No entries removed without user confirmation.
- [ ] Targeted workflow validation passes after changes.
- [ ] `aiscr_skillset_mapping.md` and cross-references updated if skill inventory changed.

## Plan and workflow

`.agents/plans/canonical-workflows-context-maintenance.plan.md`

**Registry fallback:** Load context; follow canonical-workflows-context-maintenance.plan.md manually.

## Governance

- Do **not** run `sync_agent_configs.py` unless the user explicitly asks.
- Default to local-only work; do not stage, commit, push, or switch to a remote-delivery branch without a direct user order.
- Full workflow: `.agents/plans/canonical-workflows-context-maintenance.plan.md`

## Valid next steps

- `/aiscr-canonical-workflows-context` -- reload context to verify the updated registry
- `/aiscr-plans-validation` -- validate plan schema and context paths after changes
- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change