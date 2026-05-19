<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-ci-scriptification.md -->

# aiscr-ci-scriptification

Scriptify prompts/plans into reproducible scripts and run validation and hygiene in CI without agent calls. Use when the user asks to scriptify automation, run validation in CI without AI, replace agent steps with scripts, or design script-first CI.

**Route**: Load [`.claude/skills/aiscr-ci-scriptification/SKILL.md`](.claude/skills/aiscr-ci-scriptification/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-ci-scriptification/SKILL.md`](.cursor/skills/aiscr-ci-scriptification/SKILL.md) when Cursor reader body is preferred.

`.agents/plans/ci-scriptification.plan.md`
Load openspec/specs/ci-plan-scriptification/spec.md for requirements, architecture, and capability categories; browse current automation layout (prompts, plans, scripts, CI workflows); evaluate scriptifiable parts using the spec's four capability categories; define script-only steps for CI (validation, dry-run checks); follow ci-scriptification.plan.md for cleanup, documentation updates, and testing strategy.
