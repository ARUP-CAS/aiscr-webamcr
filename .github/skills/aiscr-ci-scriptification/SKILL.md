---
name: aiscr-ci-scriptification
description: Scriptify prompts/plans into reproducible scripts and run validation
  and hygiene in CI without agent calls. Use when the user asks to scriptify automation,
  run validation in CI without AI, replace agent steps with scripts, or design script-first
  CI.
---

<!-- aiscr:compiled=aiscr-ci-scriptification -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.github/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-ci-scriptification — scriptification and CI without agents

Evaluate which prompts, plans, or skills can be turned into reproducible scripts; define script-first CI steps that run validation and hygiene without agent calls.

## Phase awareness

This skill operates within the **implement** phase of the OpenSpec lifecycle.
It is typically invoked as part of `/opsx:apply` or a standalone approved task.
Before executing, check for an active OpenSpec change or domain spec under
`openspec/`.
If one exists, load its context files as the primary authority.
If none exists for this domain, run `/opsx:propose`, stop for human approval,
and only continue after that change becomes the active context of the run.
It must not create new OpenSpec changes directly, promote backlog items, or
escalate scope beyond the approved task boundary.

## Context to load first

1. the workflow contract summarized in this compiled skill — behavioral requirements and scriptification architecture
2. `AGENTS.md` — governance and scope
3. `.agents/README.md` — structure of `.agents/`
4. repository-local script documentation when present — existing scripts inventory
5. `.github/workflows/plan-validation.yml` — current CI workflow (reference)
6. the embedded execution plan below — execution procedures and operator runbook

## Existing script-first CI (management repo)

| Script | Purpose |
|--------|---------|
| `validate_plans.py --strict` | Plan schema and content |
| `reset_plan_status.py --dry-run` | Plan status reset dry-run |
| `doc_discovery.py --check` | Instruction-bearing file inventory |
| `link_check.py` | Internal Markdown link validation |
| `validate_release_yml.py` | Release YAML schema |
| `run_validation_all.py` | One-shot local run of all above |

## Steps

1. Ask the user: target repo, scope (management vs application repo).
2. Browse and document current setup: inventory prompts, plans, scripts, and CI jobs.
3. Evaluate which parts are scriptifiable using the deterministic vs judgment-heavy framework from the spec.
4. Define script-only steps and CI jobs (consistent CLI: `--dry-run`, `--check`, exit codes).
5. Implement new or extended scripts after approval.
6. Update CI workflow to run validation/dry-run without agent calls.
7. Update READMEs and governance docs with clear script vs prompt split.
8. Regression/testing: run scripts and confirm expected exit codes.

<!-- aiscr:gen:id=guardrails -->
## Iron Law

**IRON LAW:** `NEVER ADD PLACEHOLDER CI STEPS. EVERY STEP MUST HAVE AN ACTUAL COMMAND WITH A DEFINED EXIT CODE BEFORE PRESENTING THE RESULT.`

No exceptions. "Implement later" or "TBD" in any CI step means the plan is not ready.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The step intent is clear — I'll add a TODO comment and implement later" | Block completion; every CI step must have a concrete command and defined exit codes before presenting. |
| "The script is 'mostly working' — I'll add it to CI and fix edge cases later" | Scripts must pass `run_validation_all.py` (or equivalent) before they are added to CI. |
| "I'll define the CLI flags later when the script is stable" | CLI conventions (`--dry-run`, `--check`, explicit exit codes) must be defined alongside the script, not after. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Every CI step in the output has an actual command with defined exit codes — no placeholder text ("add appropriate step", "implement later", "TBD").
- [ ] All new or modified scripts pass `run_validation_all.py` (or equivalent) without errors.
- [ ] Each script has consistent CLI conventions: `--dry-run`, `--check`, and explicit exit codes documented.
- [ ] CI workflow file updated to run new scripts; no agent-only steps remain in scope.
- [ ] READMEs and governance docs updated to reflect the new script vs prompt split.
<!-- aiscr:endgen -->

## Governance

- Do **not** run `orchestrate_local_agent_sync.py` `apply --approve`, the retired `sync_agent_configs.py` operator path, or cross-repo sync unless the user explicitly asks.
- Once an overarching scriptification plan is approved, running the resulting scripts does not require additional planning loops (single-loop model).
- Requirement authority: the workflow contract summarized in this compiled skill
- Execution runbook: the embedded execution plan below

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- Read the identifiers and references stated in this workflow and follow the **Usage** section before loading a different workflow's context.
