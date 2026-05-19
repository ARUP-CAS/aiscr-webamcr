---
name: aiscr-port-workspace-safety-config
description: Merge validated Cursor, Codex, and Claude safety templates into user
  app-level config; dry-run first, explicit confirmation; may pip-install jsonschema/tomli-w;
  optional --backup and --target-dir; not sync_agent_configs.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-port-workspace-safety-config.md -->

# aiscr-port-workspace-safety-config

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-port-workspace-safety-config/SKILL.md`](.cursor/skills/aiscr-port-workspace-safety-config/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.gemini/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Merge validated Cursor, Codex, and Claude safety templates into user app-level config; dry-run first, explicit confirmation; may pip-install jsonschema/tomli-w; optional --backup and --target-dir; not sync_agent_configs.

Merge templates from `.agents/canonical_configs/safety_config_templates/` into the user’s **app-level** Cursor sandbox, Codex config, and Claude settings using [`port_workspace_safety_config.py`](.agents/scripts/port_workspace_safety_config.py). Run it from the repo virtualenv when present. The script may **`pip install`** pinned `jsonschema` and `tomli-w` if they are missing in the current interpreter.

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

Load [`.cursor/skills/aiscr-port-workspace-safety-config/SKILL.md`](.cursor/skills/aiscr-port-workspace-safety-config/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/port-workspace-safety-config.plan.md`

**Registry fallback:** Load openspec/specs/workspace-safety-config/spec.md first for the durable behavioral contract; then run `.venv/Scripts/python.exe` `.agents/scripts/port_workspace_safety_config.py` (or `.venv/bin/python` on Unix) per `.agents/scripts/README.md` and `port-workspace-safety-config.plan.md` as the execution runbook; auto-installs missing `jsonschema`/`tomli-w` from `requirements-ci.txt` via `requirements_subset_install.py`; use `--backup` only if backups wanted; no sync without approval.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
