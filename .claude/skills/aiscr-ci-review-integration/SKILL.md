---
name: aiscr-ci-review-integration
description: Integrate review_tools.py and related AI-review checks into CI for web
  application repos. Use when the user asks to add AI review to CI, wire review_tools
  into GitHub Actions, or standardise CI + AI review for webapps.
disable-model-invocation: true
user-invocable: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-ci-review-integration.md -->

# aiscr-ci-review-integration

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-ci-review-integration/SKILL.md`](.cursor/skills/aiscr-ci-review-integration/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.claude/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Integrate review_tools.py and related AI-review checks into CI for web application repos. Use when the user asks to add AI review to CI, wire review_tools into GitHub Actions, or standardise CI + AI review for webapps.

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

## Workflow routing

Load [`.cursor/skills/aiscr-ci-review-integration/SKILL.md`](.cursor/skills/aiscr-ci-review-integration/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/ci-review-integration.plan.md`

**Registry fallback:** Load openspec/specs/ci-artifact-review/spec.md first for the durable behavioral contract; assess `.github/workflows/*.yml` for current CI setup; confirm `review_tools.py` presence and `review_config.yaml` configuration; design CI + AI review flow per plan Step 2; follow ci-review-integration.plan.md for workflow implementation and validation.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
