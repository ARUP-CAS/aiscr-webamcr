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
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

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

## Context to load first

1. `openspec/specs/overhead-measurement/spec.md` - behavioral requirements and methodology
2. `AGENTS.md` - governance and scope
3. `.agents/README.md` - structure of `.agents/`
4. `.agents/scripts/README.md` - script documentation and CLI reference
5. `.agents/canonical_configs/references/vendor_load_profiles.toml` - vendor baseline registry

## Steps

1. Run the whole-workflow report in dry-run mode first:

   ```bash
   python .agents/scripts/measure_workflow_overhead.py --dry-run
   ```

2. Review the workflow totals and plugin overhead sections. Use JSON when you need
   machine-readable detail:

   ```bash
   python .agents/scripts/measure_workflow_overhead.py --dry-run --output json
   ```

3. If committed sanitized stats exist at
   `.agents/reports/overhead/skill-usage/stats.json`, repeat with observed calibration:

   ```bash
   python .agents/scripts/measure_workflow_overhead.py --dry-run --with-observed --output json
   ```

4. Use diff or optimization output when the task is comparative:

   ```bash
   python .agents/scripts/measure_workflow_overhead.py --diff older.json newer.json --dry-run
   python .agents/scripts/measure_workflow_overhead.py --recommendations --dry-run
   ```

5. If the output looks correct, write the persisted report:

   ```bash
   python .agents/scripts/measure_workflow_overhead.py
   ```

## Iron Law

**IRON LAW:** `NEVER RECOMMEND DISABLING, REMOVING, OR UNINSTALLING AGENTS, SKILLS, OR PLUGINS WITHOUT FIRST PRESENTING A FULL IMPACT ANALYSIS TO THE USER. ANALYSIS ONLY; EXECUTION REQUIRES EXPLICIT APPROVAL.`

No exceptions. Presenting a finding is not the same as executing the removal.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The script is read-only so I can skip the dry-run" | Always run `--dry-run` first to confirm the measured shape before writing reports. |
| "Observed mode is more complete, so I should always enable it" | Use `--with-observed` only when committed sanitized stats exist; the default mode must stay standalone. |
| "This vendor looks expensive, so I can tell the user to disable its extras now" | Report the measured overhead and likely savings; do not make workstation changes. |

## Verification before completion

Before claiming this workflow complete:

- [ ] `--dry-run` output reviewed before any persisted report was produced.
- [ ] Any `--with-observed` run consumed committed sanitized stats only.
- [ ] Diff or recommendation output, when requested, came from `measure_workflow_overhead.py`.
- [ ] No files were modified during the evaluation beyond the intended report output.

## Plan and workflow

_No backing plan file;_ follow fallback and governance.

**Registry fallback:** Load openspec/specs/overhead-measurement/spec.md first for the durable behavioral contract; then run `python .agents/scripts/measure_workflow_overhead.py --dry-run` to preview the whole-workflow model; add `--with-observed` only when committed sanitized snapshots exist under `.agents/reports/overhead/skill-usage/`; use `--output json`, `--diff <older> <newer>`, or `--recommendations` as needed.

## Governance

- Script is **read-only** until the final report write; no approval required for analysis.
- Opening raw NDJSON under the gitignored sink (see `.agents/scripts/skill_usage_paths.py`) is out of scope unless the user explicitly asks to debug writers or resolver paths; rely on `skill_usage_hooks.py` status and sanitized exports for operational evidence.
- Do not run high-impact scripts (`sync_agent_configs.py`) as part of this workflow.
- Full workflow: See spec for requirements; use script directly for execution.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-overhead-optimizer` -- turn shared usage evidence into reactive optimization findings