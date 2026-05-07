<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-ci-review-integration.md -->

# aiscr-ci-review-integration

Integrate review_tools.py and related AI-review checks into CI for web application repos. Use when the user asks to add AI review to CI, wire review_tools into GitHub Actions, or standardise CI + AI review for webapps.

**Route**: Load [`.claude/skills/aiscr-ci-review-integration/SKILL.md`](.claude/skills/aiscr-ci-review-integration/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-ci-review-integration/SKILL.md`](.cursor/skills/aiscr-ci-review-integration/SKILL.md) when Cursor reader body is preferred.

`.agents/plans/ci-review-integration.plan.md`
Load openspec/specs/ci-artifact-review/spec.md first for the durable behavioral contract; assess `.github/workflows/*.yml` for current CI setup; confirm `review_tools.py` presence and `review_config.yaml` configuration; design CI + AI review flow per plan Step 2; follow ci-review-integration.plan.md for workflow implementation and validation.
