<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-docs-language-review.md -->

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.clinerules/workflows/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Run language and typo review of repo docs; user-facing Czech, agent-facing English, README_en equivalents, report language split, GFM formatting. Use when the user asks to review docs language, fix typos, add README English versions, or align with GitHub Markdown.

**Skill body (authoritative):** [`.claude/skills/aiscr-docs-language-review/SKILL.md`](.claude/skills/aiscr-docs-language-review/SKILL.md) — load that repository-local file for the full workflow body, guardrails, and verification.
