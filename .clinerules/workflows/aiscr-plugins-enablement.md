<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-plugins-enablement.md -->

# aiscr-plugins-enablement

Enable relevant plugins and document fallbacks when unavailable. Use when the user asks to enable plugins, document plugin fallbacks, update the plugin/fallback catalog, or audit installed plugins for AIS CR relevance.

**Route**: Load [`.claude/skills/aiscr-plugins-enablement/SKILL.md`](.claude/skills/aiscr-plugins-enablement/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-plugins-enablement/SKILL.md`](.cursor/skills/aiscr-plugins-enablement/SKILL.md) when Cursor reader body is preferred.

`.agents/plans/plugins-enablement.plan.md`
Load openspec/specs/plugin-coverage/spec.md first for the durable behavioral contract; catalog plugins by assistant product (Cursor MCP, Claude skills, Codex skills) and use case (docs, GitHub, Figma, Elastic, Hugging Face); document enablement steps and verification; define fallback matrix for when plugins are unavailable; update automation_recommendations.md or create plugin_enablement_and_fallback.md; follow plugins-enablement.plan.md for Mode A/B/C workflow and 5-class relevance audit.
