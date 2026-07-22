<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-doc-hygiene-audit.md -->

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.clinerules/workflows/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Run a documentation hygiene audit on this repository (or a target repo). Identifies duplication, drift, token inefficiency, and broken links.

**Skill body (authoritative):** [`.claude/skills/aiscr-doc-hygiene-audit/SKILL.md`](.claude/skills/aiscr-doc-hygiene-audit/SKILL.md) — load that repository-local file for the full workflow body, guardrails, and verification.
