<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-overhead-optimizer.md -->

# aiscr-overhead-optimizer

Turn sanitized shared usage evidence and measured plugin overhead into reactive optimization findings. Use when the user wants to identify rarely used skills or agents and estimate the cost of currently enabled extras safely.

**Route**: Load [`.claude/skills/aiscr-overhead-optimizer/SKILL.md`](.claude/skills/aiscr-overhead-optimizer/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-overhead-optimizer/SKILL.md`](.cursor/skills/aiscr-overhead-optimizer/SKILL.md) when Cursor reader body is preferred.

_No backing plan file;_ follow fallback and governance.
Load openspec/specs/plugin-coverage/spec.md and openspec/specs/overhead-measurement/spec.md first; confirm hook wiring with `python .agents/scripts/skill_usage_hooks.py --root <repo>`; export sanitized local snapshots with `python .agents/scripts/aggregate_skill_usage.py --export --source-id <alias>`, merge shared evidence with `--merge`, and compare it against `python .agents/scripts/measure_workflow_overhead.py --with-observed --output json` to identify unused or extra per-vendor skills/agents without changing workstation config automatically.
