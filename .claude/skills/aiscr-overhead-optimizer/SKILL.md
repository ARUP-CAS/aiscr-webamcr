---
name: aiscr-overhead-optimizer
description: Turn sanitized shared usage evidence and measured plugin overhead into
  reactive optimization findings. Use when the user wants to identify rarely used
  skills or agents and estimate the cost of currently enabled extras safely.
disable-model-invocation: true
user-invocable: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-overhead-optimizer.md -->

# aiscr-overhead-optimizer

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-overhead-optimizer/SKILL.md`](.cursor/skills/aiscr-overhead-optimizer/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.claude/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Turn sanitized shared usage evidence and measured plugin overhead into reactive optimization findings. Use when the user wants to identify rarely used skills or agents and estimate the cost of currently enabled extras safely.

Use sanitized shared usage evidence plus measured plugin/skill/agent overhead to
identify extras that appear unused across recent measured session windows.
This workflow is advisory only: it does not disable or reconfigure any workstation.

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

Load [`.cursor/skills/aiscr-overhead-optimizer/SKILL.md`](.cursor/skills/aiscr-overhead-optimizer/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

_No backing plan file;_ follow fallback and governance.

**Registry fallback:** Load openspec/specs/plugin-coverage/spec.md and openspec/specs/overhead-measurement/spec.md first; confirm hook wiring with `python .agents/scripts/skill_usage_hooks.py --root <repo>`; export sanitized local snapshots with `python .agents/scripts/aggregate_skill_usage.py --export --source-id <alias>`, merge shared evidence with `--merge`, and compare it against `python .agents/scripts/measure_workflow_overhead.py --with-observed --output json` to identify unused or extra per-vendor skills/agents without changing workstation config automatically.

## Valid next steps

- `/aiscr-plugins-enablement` -- evaluate proactive minimum-required plugin sets for a named workflow
- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
