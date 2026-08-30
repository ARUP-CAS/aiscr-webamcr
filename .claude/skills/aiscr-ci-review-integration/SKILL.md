---
name: aiscr-ci-review-integration
description: Integrate review_tools.py and related AI-review checks into CI for web
  application repos. Use when the user asks to add AI review to CI, wire review_tools
  into GitHub Actions, or standardise CI + AI review for webapps.
disable-model-invocation: true
user-invocable: true
---

<!-- aiscr:compiled=aiscr-ci-review-integration -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.claude/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-ci-review-integration — CI and AI review integration

Integrate `review_tools.py` and related AI-review checks into CI pipelines for AIS CR web application repositories.

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

1. the workflow contract summarized in this compiled skill — behavioral requirements and architecture
2. `AGENTS.md` — governance and scope
3. `.agents/README.md` — structure of `.agents/`
4. the embedded execution plan below — CI integration workflow

## Steps

1. Ask the user: target webapp repo path; which `review_tools.py` tasks to run on PRs vs scheduled (e.g. `status`, `lint-artifacts`, `all`).
2. Assess current CI setup: read existing `.github/workflows/` files; identify gaps.
3. Assess current review tooling: confirm `review_tools.py` is present and functional.
4. Design CI + AI review flow: propose new or updated workflow file(s).
5. Implement workflow changes after user approval.
6. Document usage in `AGENTS.md`, `CLAUDE.md`, or `.agents/README.md`.
7. Validate: trigger workflow on a test branch and confirm `review_tools.py` exit codes and logs.

<!-- aiscr:gen:id=guardrails -->
## Iron Law

**IRON LAW:** `NEVER MODIFY A CI WORKFLOW FILE WITHOUT FIRST SHOWING THE PROPOSED DIFF TO THE USER AND RECEIVING EXPLICIT APPROVAL.`

No exceptions. CI changes affect all contributors and deployments — treat every edit as high-impact regardless of apparent size.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "It's just a small change to the workflow" | Show the full proposed diff; obtain explicit approval before writing. |
| "The current CI is fine — I'll just add a step" | Read existing workflow files first; assess impact of the addition. |
| "I'll commit and fix on a follow-up" | Validate workflow changes with the user before any commit. |
<!-- aiscr:endgen -->

## Verification before completion

Before claiming this workflow complete, confirm:

- [ ] Proposed CI workflow diff was shown to user and explicitly approved.
- [ ] Workflow validated: trigger on test branch and confirm `review_tools.py` exit codes and logs.
- [ ] Branch stated per target repo and user confirmed before applying changes.
- [ ] Governance docs updated where applicable (AGENTS.md, CLAUDE.md, .agents/README.md).

## Governance

- Do **not** run high-impact sibling sync (`orchestrate_local_agent_sync.py` `apply --approve` or the retired `sync_agent_configs.py` compatibility entry) unless the user explicitly asks.
- When target is another repo, state the branch and obtain user confirmation before applying.
- For repos that do not yet have `review_tools.py`, the management hub's governance-bootstrap asset-port phase must provide it first.
- Full workflow: the embedded execution plan below

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- Read the identifiers and references stated in this workflow and follow the **Usage** section before loading a different workflow's context.

## Embedded execution plan

### Plan: CI + AI Review Integration for Web Applications

> **OpenSpec migration:** Persistent behavioral requirements for this workflow now live in the workflow contract summarized in this compiled skill. This `.plan.md` file remains the reusable execution and governance layer for aiscr-management. See the identifiers and references stated in this workflow.

#### Context

This plan lives in `aiscr-management` and targets AIS CR **web application** repositories (for example `aiscr-webamcr`, `aiscr-digiarchiv-2`, `aiscr-amcr-home`, `aiscr-home`) that:

- already use or plan to use `review_tools.py` and `.agents/` artefacts, and
- run CI workflows in GitHub Actions or similar systems.

It describes how to integrate AI‑assisted review into CI in a way that is safe, observable, and aligned with existing governance. To bring `review_tools.py` into a repo that does not yet have it, use the management hub's governance-bootstrap workflow (optional asset-port phase). For script-first CI and validation without agent calls (complementary to this workflow), use the ci-scriptification workflow.

**Note — management repo visibility:** the governance-bootstrap and asset-port workflows live in the management hub (`aiscr-management`), which may not be accessible from a sibling-repo context without direct filesystem or CLI access. When `review_tools.py` is missing, ask a maintainer with hub access to run the asset-port phase, or bring the needed files in locally first.

#### Goals

- Ensure `review_tools.py` and related checks can be run **consistently in CI**, not only locally.
- Provide maintainers with clear feedback on review status without overwhelming them.
- Keep CI configuration maintainable and aligned across AIS CR webapps.

#### Scope and assumptions

- In scope:
  - Web application repos with non‑trivial backend/frontend code and existing `.agents/` setup.
  - CI workflows that run on PRs and/or main branch pushes.
- Out of scope:
  - Low‑level implementation details of `review_tools.py`.
  - Introducing new CI platforms beyond what the repo already uses.
- Assumptions:
  - The repo already has `.agents/scripts/review_tools.py` and `review_config.toml` configured (or has ported them via the [governance bootstrap](the embedded execution plan below) workflow, optional asset port phase).

#### Execution approach

- Inspect `.github/workflows/*.yml` (or equivalent CI config); find `review_tools.py` and its usage (if any).
- Trace how CI scripts and review tools interact with the codebase.
- Review final CI workflow changes for correctness and clarity.

#### Steps

##### Step 1 — Assess current CI and review tooling

- Identify:
  - Existing CI workflows (build, test, lint, deploy).
  - Any current use of `review_tools.py` or `.agents/` artefacts in CI.
- Note:
  - Which tasks from `review_tools.py` make sense to run in CI (for example `status`, `lint-artifacts`, `all`).

##### Step 2 — Design CI + AI review flow

- Decide:
  - When to run AI‑assisted checks (for example on PRs only, or on a nightly schedule).
  - Which commands to run, such as:
    - `python .agents/scripts/review_tools.py status`
    - `python .agents/scripts/review_tools.py lint-artifacts`
    - Optional: `python .agents/scripts/review_tools.py all` for heavier runs.
- Define success/failure criteria:
  - Which findings should fail the build vs only produce warnings.

##### Step 3 — Implement CI workflow changes

- Add or update CI workflow files (for example `.github/workflows/review_tools.yml`) to:
  - Set up the appropriate environment (Python, dependencies).
  - Check out the repository, install minimal dependencies, and run chosen review_tools commands.
  - Surface results clearly in CI logs or as artefacts.

##### Step 4 — Document usage

- In `AGENTS.md`, `CLAUDE.md`, or `.agents/README.md`:
  - Document how CI and `review_tools.py` interact.
  - Explain:
    - Which jobs will run on which branches.
    - How agents should interpret CI failures or warnings from AI‑assisted checks.

##### Step 5 — Validation

- Run a test PR through the updated CI to:
  - Confirm that:
    - `review_tools.py` runs successfully or fails with meaningful errors.
    - Noise is acceptable and not overwhelming (avoid failing on minor warnings initially).
- Review the workflow YAML and associated documentation for clarity and alignment with other AIS CR repos.

#### Validation

- Run the new or updated workflow (e.g. `workflow_dispatch` or push to a test branch) and confirm `review_tools.py` exit codes and logs.
- Trigger the updated CI workflow on a test PR:
  - Ensure that `review_tools.py` commands complete successfully and their output is visible in logs.
  - Check that failure thresholds and noise levels are acceptable for maintainers.
- Review the CI workflow:
  - Inspect the CI workflow definitions and related documentation,
  - Confirm consistency with other AIS CR webapp repos where similar integration exists.

#### Notes / Adaptation per repo

- For repos with long‑running review cycles, consider running full `review_tools.py all` only in scheduled workflows, with lighter checks on each PR.
- For smaller webapps, a single job that runs `status` and `lint-artifacts` on PRs may be sufficient.

#### Options (planning phase)

**Delivery (choose before any commit or push):**

- **(A)** Create a branch and open a **draft** PR for the changes (recommended).
- **(B)** Create a branch only (no PR).
- **(C)** Local changes only (no branch, no push).

Do not commit or push until the user has chosen.

**Sibling-repo branch:** When adding workflows to a sibling (webapp) repo, state which branch will be used in that repo and obtain user confirmation before applying changes.

#### Plan refinement / Autoupdate

After integrating CI + AI review into one or more webapps:

- Recommended if relevant: apply updates to this `.plan.md` (e.g. CI patterns such as better defaults for which tasks to run on PRs vs schedules); validate changes accordingly and verbosely.
- Keep repo‑specific CI details (matrix, environments, secrets) in the respective repo’s workflow files and docs, not in the plan.
- If common issues arise (for example excessive noise or flaky checks), adjust the `Steps` and validation guidance to recommend more robust defaults.
- If repeated experience shows that `review_tools.py` or related prompts need behaviour changes, apply updates to those scripts or prompts and validate accordingly (verbose validation).

## Bundled scripts

The enrollment bundle installs these repository-local runtime scripts:

- `.agents/scripts/review_tools.py`
