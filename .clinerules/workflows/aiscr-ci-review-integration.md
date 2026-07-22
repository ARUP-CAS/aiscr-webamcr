<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-ci-review-integration.md -->

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.clinerules/workflows/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Integrate review_tools.py and related AI-review checks into CI for web application repos. Use when the user asks to add AI review to CI, wire review_tools into GitHub Actions, or standardise CI + AI review for webapps.

**Skill body (authoritative):** [`.claude/skills/aiscr-ci-review-integration/SKILL.md`](.claude/skills/aiscr-ci-review-integration/SKILL.md) — load that repository-local file for the full workflow body, guardrails, and verification.
