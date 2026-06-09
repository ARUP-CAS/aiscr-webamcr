<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-overhead-evaluator.md -->

# aiscr-overhead-evaluator

Measure and report the whole-workflow token cost of the current agent/tool setup. Use when the user asks to evaluate overhead, measure context load, compare workflow costs, or produce optimization-oriented overhead reports.

**Route**: Load [`.claude/skills/aiscr-overhead-evaluator/SKILL.md`](.claude/skills/aiscr-overhead-evaluator/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-overhead-evaluator/SKILL.md`](.cursor/skills/aiscr-overhead-evaluator/SKILL.md) when Cursor reader body is preferred.

_No backing plan file;_ follow fallback and governance.
Load openspec/specs/overhead-measurement/spec.md first for the durable behavioral contract; then run `python .agents/scripts/measure_workflow_overhead.py --dry-run` to preview the whole-workflow model; add `--with-observed` only when committed sanitized snapshots exist under `.agents/reports/overhead/skill-usage/`; use `--output json`, `--diff <older> <newer>`, or `--recommendations` as needed.
