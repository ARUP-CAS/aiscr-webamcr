---
name: aiscr-ci-scriptification
description: Scriptify prompts/plans into reproducible scripts and run validation
  and hygiene in CI without agent calls. Use when the user asks to scriptify automation,
  run validation in CI without AI, replace agent steps with scripts, or design script-first
  CI.
disable-model-invocation: true
---

<!-- aiscr:compiled=aiscr-ci-scriptification -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.cursor/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
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

## Embedded execution plan

### Plan: Scriptification and CI Without Agent Calls

> **OpenSpec migration:** Persistent behavioral requirements for this workflow now live in the workflow contract summarized in this compiled skill. This `.plan.md` file is the reusable execution and governance layer for aiscr-management. See the identifiers and references stated in this workflow.

#### Context

This plan is the execution-layer runbook for scriptification in the AIS CR ecosystem.

Use the workflow contract summarized in this compiled skill for the durable contract (scriptification methodology, capability categories, CLI conventions, repo-type adaptation). Use this plan for operator sequencing, CI integration steps, and validation choreography.

#### Execution approach

- Inventory the repo's automation/agent area (prompts, plans, scripts, config), list plan steps that mention "run script" vs "use prompt/agent", and confirm or document existing CI (e.g. `.github/workflows` or equivalent).
- Trace how existing validation or state-reset scripts are used and what they depend on; identify shared parsing or conventions for reuse.
- Propose a single, consistent CLI/exit-code convention for all scripts and where to place them within the repo's chosen structure.
- Review the final plan document, script list, and test strategy before implementation.

These steps gather context; they do not replace reading the repo's governance docs, which remain authoritative.

#### Steps

##### Step 1 — Browse and document current setup

- List all **prompts** (in the repo's prompt directory or equivalent) with a one-line purpose and whether they are fully agentic or already reference scripts.
- List all **plans** (in the repo's plan directory or equivalent) and for each note:
  - Steps that already say "run `<script>`" or equivalent.
  - Steps that say "use prompt X" or "run audit with agent".
- List **scripts** (validation, reset, sync, or other automation) with their CLI interface (args, dry-run if any, exit codes).
- Document existing **CI** (workflows, triggers, and whether any automation scripts are already run there).
- Produce a short **inventory** (e.g. in a reports or docs area) that summarises: prompts, plans, scripts, and "script vs agent" classification per step.

##### Step 2 — Evaluate scriptifiable parts of prompts and plans

Evaluate by **capability**, not by current file name. Refer to the spec's Architecture section for the four capability categories and the script-vs-agent decision framework.

Summarise in the inventory: which **new scripts** (or roles) will be added, and which prompt/plan steps will be reworded to "run `<script>`" instead of "use agent". Use role-based names (e.g. "plan schema validation script", "doc discovery script") so the plan stays valid if file names or paths change.

##### Step 3 — Define steps that must run specific code (no agent)

- **CI (in the target repository)**
  - Run the **plan/schema validation** script (with strict mode if supported) — must pass.
  - Run the **todo/state-reset** or **config dry-run** script in **dry-run only** — must complete successfully with no file writes.
  - Optionally run any **doc-hygiene** scripts (discovery, link check) in "check only" mode; fail the job on broken refs or invalid output if that is the chosen policy.
- **Plans**
  - In each relevant plan, replace vague "run the audit" with concrete "run the discovery and link-check scripts (or equivalent), then run the audit prompt with the produced report".
- **Prompts**
  - In any documentation-hygiene or audit prompt, add a **Prerequisites** section: run the following scripts and attach their output before running this prompt, so that deterministic steps (discovery, links, optional config diff) are reproducible.

Do not hard-code script paths or names in the plan body; each repo documents its own script names and paths in its README and inventory.

##### Step 4 — Cleanup previous setup and replace with script-first design

- **Narrow prompt scope** — Do not delete prompts; narrow their scope so that script-covered steps are no longer described as agent tasks (e.g. "run the discovery script" instead of "locate all instruction files").
- **Add scripts** — Provide (or extend) scripts that fulfil: plan/schema validation; optional todo/reset with dry-run; doc-hygiene discovery and link check; optional config-diff. Use a consistent CLI convention (e.g. `--dry-run`, `--strict`, exit 0/1, structured output).
- **Add CI job(s)** — Ensure CI runs validation and dry-run (and optionally doc-hygiene checks) without invoking an agent or external prompt API.
- **Replace plan and prompt text** — Where a step says "use prompt X to do Y", replace with "run script Z; then if needed use prompt X for the remainder". Keep exploratory or review-only steps as plain steps.

##### Step 5 — Update READMEs and related prompts

- **Agent/automation README** (e.g. `.agents/README.md` or the repo's equivalent) — Add a subsection on "Scripts vs prompts": when to run a script (deterministic checks, CI) vs when to use a prompt (generation, judgment, repo-specific content). List the repo's scripts (or script roles) and how CI uses them.
- **Plans README** (or equivalent) — State that CI runs plan/schema validation and dry-run of todo or config scripts; add a pointer to the CI workflow. Mention that plan steps should prefer "run `<script>`" for deterministic parts.
- **Prompts README** (or equivalent) — For any audit-style prompt, describe the script-first flow: run discovery and link-check (and optionally drift) scripts first, then run the prompt with their output.
- **Governance docs** (e.g. AGENTS.md, CLAUDE.md, or equivalent) — Add a short note that validation and doc-hygiene checks can run in CI without an agent, and that the repo's automation scripts are the source of truth for those checks.
- **Plan-builder or plan-generation prompt** (if present) — Add a guideline: for deterministic steps (schema check, link check, dry-run), prefer "run `<script>`" and name the script or role; reserve non-deterministic exploration or review for plain judgment steps.

Use the repo's actual doc names and paths; the plan does not assume a fixed list.

##### Step 6 — Robust testing concept

- **Unit tests** — For validation and dry-run scripts: tests that load fixture inputs (e.g. a minimal plan file or a small doc tree) and assert expected result or exit code. For doc-hygiene scripts: tests with a fixture tree (sample README, broken link, valid link) and assert exit codes and key output.
- **Snapshot / baseline** — Run the plan/schema validation against the current set of plan files and treat "all passed" as the baseline; new plans must pass the same checks. For todo/reset scripts, run dry-run and optionally capture "would change" output to detect unintended behaviour changes.
- **CI as regression gate** — CI runs on relevant triggers (e.g. PRs touching the automation area or main branch). Failure of validation or dry-run fails the build. No agent calls in CI.
- **Behavioural parity** — Document the intended behaviour of each script. After adding or changing scripts, ensure (1) existing plan files still pass validation, (2) discovery and link-check outcomes match the previous manual or agent behaviour where applicable. Keep a short checklist (in the plan or in the plans README) for "before merging scriptification, verify: …".

##### Step 7 — Validation and handover

- Run the CI workflow locally (e.g. via `act` or a branch push) and confirm it passes.
- Run any new doc-hygiene or validation scripts against the target repository and fix reported issues (or document known exceptions).
- Final pass: ensure every modified prompt, plan, and README clearly separates "run this script" from "use an agent for this step".

#### Validation

- **Schema and scripts** — The plan/schema validation script passes (strict mode if supported). The todo/reset or config dry-run script runs without error and does not modify files.
- **CI** — The workflow runs on the intended events and fails the job when validation or dry-run fails. No step invokes an AI agent or external prompt API.
- **Regression** — All current plans remain valid. Doc-hygiene or validation script output is reviewed and either fixed or documented as accepted.
- **Docs** — READMEs and governance docs state when to use scripts vs prompts; plan steps converted to "run script" are updated and consistent.
- Optionally review changes to scripts and CI and confirm the validation workflow is described in the README.

##### Testing

- **Unit tests** — For the plan/schema validation script: run against fixture plans (valid frontmatter, invalid frontmatter, missing required section); assert exit code and key output. For the todo/reset script: fixture plan with mixed statuses; run dry-run and apply; assert exit codes and that `cancelled` is unchanged unless `--include-cancelled`. For doc-discovery: fixture tree with zero or more instruction files; run with `--check` and `--output json`; assert exit 0/1 and structure. For link-check: fixture tree with valid link, broken file link, broken section anchor; assert exit 0/1 and reported broken refs.
- **Baseline** — All current plan files pass the validation script in strict mode; dry-run of reset completes successfully; discovery and link-check produce expected outcomes. CI enforces this on every change to the automation area.
- **Before merging scriptification changes** — (1) All current plans pass validation. (2) Dry-run reset runs without error. (3) Discovery and link-check outcomes match expectations or exceptions are documented. (4) READMEs and governance docs clearly separate "run this script" from "use an agent for this step".

#### Notes / Adaptation per repo

- The plan is **structure-agnostic**: it describes **capabilities** (plan validation, dry-run, doc discovery, link check, script-first prompts) rather than specific file or path names. Repos with different directory layouts (e.g. `.agents/`, `.automation/`, or future layouts) or different script names can apply the same pattern.
- **Management repository** — Typically runs full plan/schema validation and todo dry-run in CI; may add doc-hygiene scripts; updates its agent/automation READMEs and governance docs with the script vs prompt split.
- **Application or docs repositories** — Apply only the steps that fit: e.g. run existing review/lint or validation scripts in CI; optionally run doc-hygiene or plan validation if those scripts exist in the repo or are shared from the management repo.
- **Sibling repos (explicit target)** — When the user explicitly asks to apply scriptification to a sibling repo, follow the full plan steps in that repo. State the planned branch per target repo and obtain user confirmation before applying changes. Use a `--dry-run` step first for any script that writes files. Governance docs and CI updates in the sibling repo follow the same human-approval rules as the management repo.
- **Governance** — The repo's governance docs must continue to require human approval before running any high-impact sync or mapping operations outside dry-run; scriptification does not change that.
- **Futureproofing** — As repos develop, script names and paths may change. Keep this plan focused on roles and patterns; document repo-specific script names and paths in the repo's own README and inventory.

**Example: management repo** — Run plan schema validation and todo/reset dry-run in CI; add or adopt doc-hygiene discovery and link-check scripts; update the agent/automation README, plans README, and prompts README with the script vs prompt split. CI also runs release config validation (`validate_release_yml.py`) and Markdown lint (PyMarkdown, `.pymarkdown.yaml`). Script names and paths are those used in that repo.

**Example: application repo** — Run any existing review or lint scripts in CI; optionally run doc-hygiene or validation scripts if present or shared. Adapt steps to the artefacts and paths that exist in that repo.

#### Options (planning phase)

**Delivery (choose before any commit or push):**

- **(A)** Create a branch and open a **draft** PR for the changes (recommended).
- **(B)** Create a branch only (no PR).
- **(C)** Local changes only (no branch, no push).

Do not commit or push until the user has chosen.

**Scope / target:** Confirm with the user which repo(s) or target (e.g. management repo, or list of sibling repos). Do not assume from context.

**Sibling-repo branch:** For sibling targets, state which branch will be used in each target repo and obtain user confirmation before applying changes.

**Dry-run or read-only first:** Run any config/sync/reset or todo-reset step in dry-run (or read-only) mode first; only apply changes after the user confirms the dry-run output.

#### Plan refinement / Autoupdate

After applying scriptification in one or more repositories:

- Recommended if relevant: apply updates to this `.plan.md` (e.g. clearer capability names, additional script roles, or improved testing checklists); validate changes accordingly and verbosely. Keep the plan structure-agnostic; do not hard-code repo-specific paths or script names.
- Keep repository-specific decisions (script names, paths, CI workflow names) in the target repo's README and inventory, not in this plan.
- If certain steps are routinely unnecessary or additional steps repeatedly needed, update the `todos` and `Steps` to capture the improved scriptification flow.
- If it becomes clear that underlying prompts (e.g. doc-hygiene or audit prompts) or validation scripts need changes, apply updates to those artefacts and validate accordingly (verbose validation).
