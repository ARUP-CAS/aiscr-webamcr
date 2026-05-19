<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-review-pr.md -->

# aiscr-review-pr

Review a GitHub PR — durable behavioral contract in OpenSpec spec; execution runbook in plan. Ingest prior review context, structure findings into buckets (resolved / disputed / not addressed / new), post body and inline comments as a single grouped review via GH API.

**Route**: Load [`.claude/skills/aiscr-review-pr/SKILL.md`](.claude/skills/aiscr-review-pr/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-review-pr/SKILL.md`](.cursor/skills/aiscr-review-pr/SKILL.md) when Cursor reader body is preferred.

`.agents/plans/review-pr.plan.md`
Load openspec/specs/pr-review-workflow/spec.md first for the durable behavioral contract. PR number + optional GH_TOKEN; run review_pr.py gather for prior context; structure findings into buckets (resolved, disputed, not addressed, new) with severity labels; post grouped review per review-pr.plan.md (review_pr.py post).
