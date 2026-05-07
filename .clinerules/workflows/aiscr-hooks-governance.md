<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-hooks-governance.md -->

# aiscr-hooks-governance

Review and harden AI-related automation and hooks in a repo. Use when the user asks to harden hooks, review automation, or tighten AI-related tooling.

**Route**: Load [`.claude/skills/aiscr-hooks-governance/SKILL.md`](.claude/skills/aiscr-hooks-governance/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-hooks-governance/SKILL.md`](.cursor/skills/aiscr-hooks-governance/SKILL.md) when Cursor reader body is preferred.

`.agents/plans/hooks-governance.plan.md`
Load openspec/specs/ai-automation-governance/spec.md first for the durable behavioral contract; choose Mode A (introduce new hooks) or Mode B (harden existing hooks); load `AGENTS.md`, `CLAUDE.md`, and `automation_recommendations.md` for governance context; inventory existing hooks, MCP servers, and skills; follow hooks-governance.plan.md for hardening workflow and validation.
