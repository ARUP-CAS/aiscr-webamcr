---
name: aiscr-ci-review-integration
description: Integrate review_tools.py and related AI-review checks into CI for web
  application repos. Use when the user asks to add AI review to CI, wire review_tools
  into GitHub Actions, or standardise CI + AI review for webapps.
---

<!-- aiscr:compiled=aiscr-ci-review-integration -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.github/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
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
