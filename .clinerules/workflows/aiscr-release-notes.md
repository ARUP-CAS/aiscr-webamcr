<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-release-notes.md -->

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.clinerules/workflows/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Generate semantic, issue/PR-aligned release notes for a target AIS CR repository. Stores output in .agents/reports/release-notes/. Optionally updates the GitHub release body (opt-in, requires user approval).

**Skill body (authoritative):** [`.claude/skills/aiscr-release-notes/SKILL.md`](.claude/skills/aiscr-release-notes/SKILL.md) — load that repository-local file for the full workflow body, guardrails, and verification.
