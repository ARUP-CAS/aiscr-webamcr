<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-incident-postmortem.md -->

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.clinerules/workflows/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Document an incident or postmortem for an AIS CR service using the structured template. Produces a Czech Markdown report under .agents/reports/incidents/.

**Skill body (authoritative):** [`.claude/skills/aiscr-incident-postmortem/SKILL.md`](.claude/skills/aiscr-incident-postmortem/SKILL.md) — load that repository-local file for the full workflow body, guardrails, and verification.
