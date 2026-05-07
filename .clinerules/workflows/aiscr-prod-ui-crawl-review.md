<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-prod-ui-crawl-review.md -->

# aiscr-prod-ui-crawl-review

Deployed UI/SEO verification for user-facing public URLs in a target review_codebase workflow (optional T12/session); not GitHub PR review.

**Route**: Load [`.claude/skills/aiscr-prod-ui-crawl-review/SKILL.md`](.claude/skills/aiscr-prod-ui-crawl-review/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-prod-ui-crawl-review/SKILL.md`](.cursor/skills/aiscr-prod-ui-crawl-review/SKILL.md) when Cursor reader body is preferred.

`.agents/plans/prod-ui-crawl-review.plan.md`
Load openspec/specs/production-ui-verification/spec.md first for the durable behavioral contract; in target repo load `AGENTS.md`, `review_codebase.md`, `review_config.yaml`; read `deployed_verify` allowlisted URLs; confirm staging-first and explicit approval for production; run Tier 1 checks (optionally Tier 2 per policy); write `deployed_ui_analysis.json` and `T12.md`; update `review_cache.json`; map findings to source assets per stack; follow prod-ui-crawl-review.plan.md for execution workflow.
