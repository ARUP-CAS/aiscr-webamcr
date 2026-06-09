---
name: aiscr-prod-ui-crawl-review
description: Deployed UI/SEO verification for user-facing public URLs in a target
  review_codebase workflow (optional T12/session); not GitHub PR review.
disable-model-invocation: true
user-invocable: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-prod-ui-crawl-review.md -->

# aiscr-prod-ui-crawl-review

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-prod-ui-crawl-review/SKILL.md`](.cursor/skills/aiscr-prod-ui-crawl-review/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.claude/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Deployed UI/SEO verification for user-facing public URLs in a target review_codebase workflow (optional T12/session); not GitHub PR review.

Run optional **live deployed** checks for any AIS CR repo whose **public users** load HTML over HTTPS (webapp, docs site, static site, etc.) using `review_codebase.md` + `review_config.yaml`. Outputs: `deployed_ui_analysis.json` + `review_reports/T12.md` (typical)—**not** `review_pr.py`.

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

Load [`.cursor/skills/aiscr-prod-ui-crawl-review/SKILL.md`](.cursor/skills/aiscr-prod-ui-crawl-review/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/prod-ui-crawl-review.plan.md`

**Registry fallback:** Load openspec/specs/production-ui-verification/spec.md first for the durable behavioral contract; in target repo load `AGENTS.md`, `review_codebase.md`, `review_config.yaml`; read `deployed_verify` allowlisted URLs; confirm staging-first and explicit approval for production; run Tier 1 checks (optionally Tier 2 per policy); write `deployed_ui_analysis.json` and `T12.md`; update `review_cache.json`; map findings to source assets per stack; follow prod-ui-crawl-review.plan.md for execution workflow.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
