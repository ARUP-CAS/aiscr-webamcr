---
name: aiscr-review-pr
description: Review a GitHub PR — durable behavioral contract in OpenSpec spec; execution
  runbook in plan. Ingest prior review context, structure findings into buckets (resolved
  / disputed / not addressed / new), post body and inline comments as a single grouped
  review via GH API.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-review-pr.md -->

# aiscr-review-pr

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-review-pr/SKILL.md`](.cursor/skills/aiscr-review-pr/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.gemini/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Review a GitHub PR — durable behavioral contract in OpenSpec spec; execution runbook in plan. Ingest prior review context, structure findings into buckets (resolved / disputed / not addressed / new), post body and inline comments as a single grouped review via GH API.

Review a PR end-to-end: gather prior context, structure findings, and post as a formal
GH review with inline comments where possible.

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

Load [`.cursor/skills/aiscr-review-pr/SKILL.md`](.cursor/skills/aiscr-review-pr/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/review-pr.plan.md`

**Registry fallback:** Load openspec/specs/pr-review-workflow/spec.md first for the durable behavioral contract. PR number + optional GH_TOKEN; run review_pr.py gather for prior context; structure findings into buckets (resolved, disputed, not addressed, new) with severity labels; post grouped review per review-pr.plan.md (review_pr.py post).

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
