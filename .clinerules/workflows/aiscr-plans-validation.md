<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-plans-validation.md -->

# aiscr-plans-validation

Run the aiscr-management validation suite (plan schema, doc discovery, link check). Read-only; reports findings without modifying files.

**Route**: Load [`.claude/skills/aiscr-plans-validation/SKILL.md`](.claude/skills/aiscr-plans-validation/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-plans-validation/SKILL.md`](.cursor/skills/aiscr-plans-validation/SKILL.md) when Cursor reader body is preferred.

`.agents/plans/plans-validation.plan.md`
Run python .agents/scripts/run_validation_all.py (or individual scripts) per plan; no sync without approval.
