---
name: aiscr-overhead-optimizer
description: Turn sanitized shared usage evidence and measured plugin overhead into
  reactive optimization findings. Use when the user wants to identify rarely used
  skills or agents and estimate the cost of currently enabled extras safely.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-overhead-optimizer.md -->

# aiscr-overhead-optimizer

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

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

## Context to load first

1. `openspec/specs/plugin-coverage/spec.md` - reactive recommendation behavior and telemetry rules
2. `openspec/specs/overhead-measurement/spec.md` - measured overhead methodology
3. `AGENTS.md` - governance and scope
4. `.agents/README.md` - structure of `.agents/`
5. `.agents/scripts/README.md` - script documentation and CLI reference
6. `.agents/canonical_configs/references/plugin_enablement_and_fallback.md` - fallback and plugin-catalog context

## Steps

1. Confirm skill-usage monitoring is wired for each vendor in scope using
   `python .agents/scripts/skill_usage_hooks.py --root <repo>` (status is part of
   `validation_suite`). Do not install or modify hook entries unless the user
   explicitly asked you to follow documented `--apply` steps.

2. Export sanitized local telemetry from workstation-local raw NDJSON into the
   committed cumulative stats artifact:

   ```bash
   python .agents/scripts/aggregate_skill_usage.py --export --source-id <alias>
   ```

3. Review the derived observed summary from `skill-usage/stats.json`:

   ```bash
   python .agents/scripts/aggregate_skill_usage.py --merge --n-sessions 10 --print
   ```

4. Measure current plugin/skill/agent overhead with observed calibration enabled:

   ```bash
   python .agents/scripts/measure_workflow_overhead.py --dry-run --with-observed --output json
   ```

5. Compare merged usage against the measured plugin entries per vendor and prepare
   reactive findings:
   - list skills/agents absent from measured contributors' last N session windows
   - include the estimated per-session baseline tokens from plugin overhead
   - mark any vendor with no telemetry surface as `unmeasured`, not zero-use

## Iron Law

**IRON LAW:** `NEVER DISABLE, UNINSTALL, OR RECONFIGURE A USER'S VENDOR TOOLS, SKILLS, AGENTS, OR PLUGINS AS PART OF THIS WORKFLOW. PRESENT FINDINGS, SAVINGS ESTIMATES, AND IMPACT; WAIT FOR EXPLICIT USER INSTRUCTION BEFORE ANY ENVIRONMENT CHANGE.`

No exceptions. Reactive optimization is analysis, not auto-remediation.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "No measured session used this skill, so I can remove it now" | Present the finding with its estimated savings and confidence envelope; the user decides. |
| "Raw local telemetry is already on disk, so I can commit it with the report" | Export sanitized stats only; never commit raw NDJSON (gitignored `<repo>/.venv/aiscr-skill-usage/raw/`, or `AISCR_SKILL_USAGE_RAW_DIR`). |
| "Copilot has no telemetry, so it is safe to show 0 invocations" | Mark vendors with no hook surface as `unmeasured` and state the reason. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Findings were based on sanitized committed stats, not raw local telemetry files.
- [ ] Vendors without a telemetry surface are reported as `unmeasured`.
- [ ] Every disable or cleanup idea includes an estimated savings figure and remains advisory.
- [ ] No workstation config was changed during the workflow.

## Plan and workflow

_No backing plan file;_ follow fallback and governance.

**Registry fallback:** Load openspec/specs/plugin-coverage/spec.md and openspec/specs/overhead-measurement/spec.md first; confirm hook wiring with `python .agents/scripts/skill_usage_hooks.py --root <repo>`; export sanitized local snapshots with `python .agents/scripts/aggregate_skill_usage.py --export --source-id <alias>`, merge shared evidence with `--merge`, and compare it against `python .agents/scripts/measure_workflow_overhead.py --with-observed --output json` to identify unused or extra per-vendor skills/agents without changing workstation config automatically.

## Governance

- Usage monitoring is hub policy (committed Cursor hooks + `skill_usage_hooks.py` checks); this workflow documents status and commands only and must not silently alter workstation config.
- `.agents/reports/overhead/skill-usage/stats.json` is the committed sanitized telemetry artifact; never commit raw NDJSON.
- Coordinate proactive "minimum required set" questions with `/aiscr-plugins-enablement`.
- Full workflow: combine `aggregate_skill_usage.py` with `measure_workflow_overhead.py`; the OpenSpec specs remain the authority.

## Valid next steps

- `/aiscr-plugins-enablement` -- evaluate proactive minimum-required plugin sets for a named workflow
- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete