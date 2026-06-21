---
name: aiscr-codebase-review
description: "Long-running codebase review for the repository it runs in (any AIS CR repo except the management hub); two modes (full pass T01-T11, incremental update U01-U06) dispatched via detect -> propose-with-evidence -> user-confirm. Owns the cache and report schema, severity vocabulary, and English-default output language; repo-specific scope stays in the target repo's review_config.yaml. The generated skill embeds its runbook."
agent: agent
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-codebase-review.md -->

# aiscr-codebase-review

Long-running codebase review for the repository it runs in (any AIS CR repo except the management hub); two modes (full pass T01-T11, incremental update U01-U06) dispatched via detect -> propose-with-evidence -> user-confirm. Owns the cache and report schema, severity vocabulary, and English-default output language; repo-specific scope stays in the target repo's review_config.yaml. The generated skill embeds its runbook.

**Skill body (authoritative):** [`.cursor/skills/aiscr-codebase-review/SKILL.md`](../../.cursor/skills/aiscr-codebase-review/SKILL.md) — load that repository-local file for the full AIS CR workflow body, guardrails, implementation steps, and verification requirements.
