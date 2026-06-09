---
name: aiscr-plan-builder
description: Create a new plan under .agents/plans/ that follows the AIS CR schema
  and governance. Uses plan_builder.md to generate the plan, then validates and registers
  it.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-plan-builder.md -->

# aiscr-plan-builder

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Generate a new plan file under `.agents/plans/` following the AIS CR plan schema and governance.

## Phase awareness

This skill is a **meta/orchestration** helper that supports the OpenSpec lifecycle
without participating in phase transitions. It loads context, builds plans, or
maintains registries. It does not create OpenSpec changes or execute implementation tasks.
Check for relevant domain specs when the task touches governed capabilities.
If no relevant domain spec exists, consider running `/opsx:propose` to formalize the capability before execution work begins.

## Context to load first

1. `AGENTS.md`
2. `.agents/README.md`
3. `.agents/plans/README.md` — plan schema, required keys, allowed status values
4. `.agents/plans/plan-builder.plan.md`
5. `.agents/prompts/plan_builder.md` — meta-prompt for generating plans

## Steps

1. Ask the user:
   - Plan name (becomes filename: `<name>.plan.md`)
   - Goal/purpose in one sentence
   - Scope: which repos or directories does it affect?
   - Related prompts/scripts (if known)

2. Read `.agents/prompts/plan_builder.md` and follow it to generate the plan frontmatter and body.

3. Draft the plan with:
   - YAML frontmatter: `name`, `overview`, `scope`, `relatedRepos`, `todos`
   - Numbered sections: Prerequisites, Steps, Verification
   - `status: pending` for all todos initially
   - **Before presenting for review, run the self-review gate:**
     - No placeholder text (`TBD`, `TODO`, `implement later`, `similar to step N`, `Add appropriate…`).
     - Every to-do names a concrete artefact, file, script, report, or command.
     - Every stated goal maps to at least one to-do.
     - To-do `id` values are content-derived kebab-case slugs, not positional labels (`step-1`).
     - The Impacts section (or equivalent) names every file, directory, or repository that will be touched.
   - Plans that fail any gate item must be revised before presenting.
   - See `plan_builder.md` "Self-review checklist" and "To-do quality requirements" for full criteria and bad/good examples.

4. Present the draft to the user for review.

5. After approval, write to `.agents/plans/<name>.plan.md`.

6. Validate the new plan:

   ```sh
   python .agents/scripts/validate_plans.py --strict
   ```

7. Register the new plan in `aiscr_skillset_mapping.md` and update `AGENTS.md` skills table if it maps to a new skill.

## Iron Law

**IRON LAW:** `NEVER PRESENT A PLAN THAT HAS NOT PASSED THE SELF-REVIEW CHECKLIST: NO PLACEHOLDER TEXT, EVERY GOAL MAPS TO A STEP, EVERY STEP NAMES A CONCRETE ARTEFACT.`

No exceptions. A plan that fails the self-review gate must be revised before presentation.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The plan is mostly done — I'll present it and fix the placeholders in a follow-up" | Block presentation until all self-review items pass; revise first. |
| "`TBD` for this step is acceptable because the scope is unclear" | Clarify scope before presenting; never carry placeholder text into a presented plan. |
| "The Impacts section can be filled in after approval" | Impacts is required; name every file, directory, and repo that will be touched before presenting. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Self-review gate passed: no placeholder text, concrete artefacts, goals map to steps, content-derived kebab-case ids, Impacts names all touched paths.
- [ ] Plan schema valid (Goals + Impacts + Agent assignments + Evaluation/recommendation sections present).
- [ ] `validate_plans.py --strict` passed on the new plan file.
- [ ] Plan not written to disk until user explicitly approved the presented draft.

## Plan and workflow

`.agents/plans/plan-builder.plan.md`

**Registry fallback:** Read plan_builder.md; follow AIS CR plan schema manually.

## Governance

- Plan files must follow the schema in `.agents/plans/README.md`.
- Plans must have ≥3 granular, actionable to-dos — see `plan_builder.md` "To-do quality requirements" for criteria and examples.
- Do not write the file until the user approves the draft.
- Full workflow: `.agents/plans/plan-builder.plan.md`

## Valid next steps

- `/aiscr-plans-validation` -- validate the newly created plan
- `/aiscr-canonical-workflows-context` -- load context for a specific workflow
- `/opsx:apply <slug>` -- implement tasks from an OpenSpec change