<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-security-ai-usage.md -->

# aiscr-security-ai-usage

Apply and validate security- and privacy-aware AI usage rules. Use when the user asks to add AI usage rules, validate security/privacy for AI, or harden AI usage governance.

**Route**: Load [`.claude/skills/aiscr-security-ai-usage/SKILL.md`](.claude/skills/aiscr-security-ai-usage/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-security-ai-usage/SKILL.md`](.cursor/skills/aiscr-security-ai-usage/SKILL.md) when Cursor reader body is preferred.

`.agents/plans/security-ai-usage.plan.md`
Load openspec/specs/security-privacy-ai-usage/spec.md first for the durable behavioral contract; identify sensitive data surfaces in code, configs, prompts, and logs; review existing AI usage rules in `AGENTS.md`, `CLAUDE.md`; define cross-repo principles for what can/cannot be sent to AI systems; update governance docs and prompts; validate compliance across repositories; follow security-ai-usage.plan.md for execution workflow.
