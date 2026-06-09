---
name: aiscr-canonical-workflows-context
description: Load the prescribed context for a named aiscr-management workflow before
  executing it. Use this when starting a standard management task (config sync, doc
  audit, plan validation, governance bootstrap, model mapping update, etc.) to ensure
  you read the right files in the right order.
disable-model-invocation: false
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-canonical-workflows-context.md -->

# aiscr-canonical-workflows-context

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Thin router: map the user’s task to **one row** in the canonical reference, then load that row’s **Context (order)** before executing its plan or script.

This skill is execution-facing only. If the task is to edit the workflow registry, workflow reference, or generated skill surfaces, use **`/aiscr-canonical-workflows-context-maintenance`** instead.

## Phase awareness

This skill is a **meta/orchestration** helper that supports the OpenSpec lifecycle
without participating in phase transitions. It loads context, builds plans, or
maintains registries. It does not create OpenSpec changes or execute implementation tasks.
Check for relevant domain specs when the task touches governed capabilities.
If no relevant domain spec exists, consider running `/opsx:propose` to formalize the capability before execution work begins.

## Reference (single source)

- **Human table:** `.agents/canonical_configs/references/canonical_workflows_context.md` — columns **Workflow**, **Context (order)**, **Plan / script**, **Notes** (and assistant fallbacks where listed).
- **Machine registry:** `.agents/canonical_configs/references/canonical_workflows_context.toml` — authoritative `aiscr-*` slug set for CI (`parity.workflows-toml-md-slug-match`). If a slug exists in TOML but the Markdown row is unclear, align Markdown on the next maintenance pass; do not invent workflows absent from the reference.

For **plan-only** workflows (empty `plan_file` in TOML), follow the **Notes** column and `.agents/canonical_configs/references/aiscr_skillset_mapping.md`.

## If the reference file is missing (sibling / sparse checkout)

When `.agents/canonical_configs/references/canonical_workflows_context.md` is not in the workspace, open the **hub** copy (same path under the `aiscr-management` repo), e.g. `https://github.com/ARUP-CAS/aiscr-management/blob/main/.agents/canonical_configs/references/canonical_workflows_context.md`. Resolve the workflow row there, then load **only paths that exist** in the current repo (skip missing files and state what was skipped).

## Inputs and outputs

- **From the user:** Workflow name, task description, or `aiscr-<name>` slug.
- **From you:** (1) Named **Workflow** row. (2) Ordered list of context paths to read. (3) Target plan or script. (4) Short confirmation before any high-impact step.

## Steps

1. If the user did not name a workflow, ask which standard task they are starting (examples: doc hygiene, config sync, plan validation, governance bootstrap, release notes).

2. Find the matching row in `canonical_workflows_context.md` (match **Workflow** text or infer from **Notes** / skillset mapping). Prefer exact slug match when the user says `aiscr-…`.

3. Load each file in the row’s **Context (order)** list. Read in order; do not skip governance files at the top of the list unless the path is missing (sibling case above).

4. Record the **Plan / script** cell and any warnings (e.g. human-approved apply only).

5. Confirm briefly: context loaded for [workflow]; next step is [plan or script name].

6. Continue per `AGENTS.md` and `.agents/canonical_configs/governance_rules/planning-core.md` (single-loop planning, approval before mutating scripts).

When delegating (e.g. explore plans, governance check), prefer **AIS CR project subagents** per `subagent_vanilla_templates_and_mapping.md`.

## Iron Law

**IRON LAW:** `NEVER EXECUTE A WORKFLOW WITHOUT FIRST LOADING THE PRESCRIBED CONTEXT FROM canonical_workflows_context.md. CONTEXT LOADING IS MANDATORY, NOT OPTIONAL.`

No exceptions. Skipping context loading leads to wrong plan, wrong scripts, and wrong approval gates.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "I know this workflow well — I'll skip context loading" | The canonical context may have changed; load it every time. |
| "The workflow isn't in the context map — I'll infer the context" | Inform the user and ask how to proceed; do not guess at file order. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Matching row found in `canonical_workflows_context.md` for the named workflow.
- [ ] All prescribed context files loaded in the listed order before any execution began.
- [ ] If no row was found, fallback and gap documented and communicated to user.

## Plan and workflow

`.agents/plans/canonical-workflows-context.plan.md`

**Registry fallback:** Read canonical_workflows_context.md directly and load listed context in order.

## Governance

- Do not run `sync_agent_configs.py` or `orchestrate_local_agent_sync.py apply` without explicit user approval.
- Prefer `--dry-run` where scripts support it.
- This skill does not replace the backing plan; it only ensures context order.

## Valid next steps

- `/aiscr-<workflow>` -- execute the loaded workflow skill
- `/opsx:apply <slug>` -- implement tasks from an OpenSpec change
- `/aiscr-canonical-workflows-context-maintenance` -- update the workflow registry itself