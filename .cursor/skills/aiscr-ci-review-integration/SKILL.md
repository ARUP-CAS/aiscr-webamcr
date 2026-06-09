---
name: aiscr-ci-review-integration
description: Integrate review_tools.py and related AI-review checks into CI for web
  application repos. Use when the user asks to add AI review to CI, wire review_tools
  into GitHub Actions, or standardise CI + AI review for webapps.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-ci-review-integration.md -->

# aiscr-ci-review-integration

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

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

1. `openspec/specs/ci-artifact-review/spec.md` — behavioral requirements and architecture
2. `AGENTS.md` — governance and scope
3. `.agents/README.md` — structure of `.agents/`
4. `.agents/plans/ci-review-integration.plan.md` — CI integration workflow

## Steps

1. Ask the user: target webapp repo path; which `review_tools.py` tasks to run on PRs vs scheduled (e.g. `status`, `lint-artifacts`, `all`).
2. Assess current CI setup: read existing `.github/workflows/` files; identify gaps.
3. Assess current review tooling: confirm `review_tools.py` is present and functional.
4. Design CI + AI review flow: propose new or updated workflow file(s).
5. Implement workflow changes after user approval.
6. Document usage in `AGENTS.md`, `CLAUDE.md`, or `.agents/README.md`.
7. Validate: trigger workflow on a test branch and confirm `review_tools.py` exit codes and logs.

## Iron Law

**IRON LAW:** `NEVER MODIFY A CI WORKFLOW FILE WITHOUT FIRST SHOWING THE PROPOSED DIFF TO THE USER AND RECEIVING EXPLICIT APPROVAL.`

No exceptions. CI changes affect all contributors and deployments — treat every edit as high-impact regardless of apparent size.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "It's just a small change to the workflow" | Show the full proposed diff; obtain explicit approval before writing. |
| "The current CI is fine — I'll just add a step" | Read existing workflow files first; assess impact of the addition. |
| "I'll commit and fix on a follow-up" | Validate workflow changes with the user before any commit. |

## Verification before completion

Before claiming this workflow complete, confirm:

- [ ] Proposed CI workflow diff was shown to user and explicitly approved.
- [ ] Workflow validated: trigger on test branch and confirm `review_tools.py` exit codes and logs.
- [ ] Branch stated per target repo and user confirmed before applying changes.
- [ ] Governance docs updated where applicable (AGENTS.md, CLAUDE.md, .agents/README.md).

## Plan and workflow

`.agents/plans/ci-review-integration.plan.md`

**Registry fallback:** Load openspec/specs/ci-artifact-review/spec.md first for the durable behavioral contract; assess `.github/workflows/*.yml` for current CI setup; confirm `review_tools.py` presence and `review_config.yaml` configuration; design CI + AI review flow per plan Step 2; follow ci-review-integration.plan.md for workflow implementation and validation.

## Governance

- Do **not** run high-impact scripts (`sync_agent_configs.py`) unless the user explicitly asks.
- When target is another repo, state the branch and obtain user confirmation before applying.
- For repos that do not yet have `review_tools.py`, use `/aiscr-governance-bootstrap` (asset port phase) first.
- Full workflow: `.agents/plans/ci-review-integration.plan.md`

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow