<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-codebase-review.md -->

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.clinerules/workflows/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Long-running codebase review for the repository it runs in (any AIS CR repo except the management hub); two modes (full pass T01-T11, incremental update U01-U06) dispatched via detect -> propose-with-evidence -> user-confirm. Owns the cache and report schema, severity vocabulary, and English-default output language; repo-specific scope stays in the target repo's review_config.yaml. The generated skill embeds its runbook.

**Skill body (authoritative):** [`.claude/skills/aiscr-codebase-review/SKILL.md`](.claude/skills/aiscr-codebase-review/SKILL.md) — load that repository-local file for the full workflow body, guardrails, and verification.
