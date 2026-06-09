---
name: aiscr-overhead-evaluator
description: Measure and report the whole-workflow token cost of the current agent/tool
  setup. Use when the user asks to evaluate overhead, measure context load, compare
  workflow costs, or produce optimization-oriented overhead reports.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-overhead-evaluator.md -->

# aiscr-overhead-evaluator

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-overhead-evaluator/SKILL.md`](.cursor/skills/aiscr-overhead-evaluator/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.gemini/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Measure and report the whole-workflow token cost of the current agent/tool setup. Use when the user asks to evaluate overhead, measure context load, compare workflow costs, or produce optimization-oriented overhead reports.

Measure and estimate the whole-workflow token cost of the current assistant/tool
setup: vendor baseline, workflow body, explicit transitive references, runtime
surcharge, and plugin/skill/agent overhead. Produce Markdown or JSON reports
under `.agents/reports/overhead/`.

## Phase awareness

This skill operates within the **implement** phase of the OpenSpec lifecycle.
It is typically invoked as part of `/opsx:apply` or a standalone approved task.
Before executing, check for an active OpenSpec change or domain spec under
`openspec/`.
If one exists, load its context files as the primary authority.
If none exists for this domain, run `/opsx:propose`, stop for human approval,
and only continue after that change becomes the active context of the run.
It must not create new OpenSpec changes directly, promote backlog items, or
escalate scope beyond the approved task boundary.

## Workflow routing

Load [`.cursor/skills/aiscr-overhead-evaluator/SKILL.md`](.cursor/skills/aiscr-overhead-evaluator/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

_No backing plan file;_ follow fallback and governance.

**Registry fallback:** Load openspec/specs/overhead-measurement/spec.md first for the durable behavioral contract; then run `python .agents/scripts/measure_workflow_overhead.py --dry-run` to preview the whole-workflow model; add `--with-observed` only when committed sanitized snapshots exist under `.agents/reports/overhead/skill-usage/`; use `--output json`, `--diff <older> <newer>`, or `--recommendations` as needed.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-overhead-optimizer` -- turn shared usage evidence into reactive optimization findings
