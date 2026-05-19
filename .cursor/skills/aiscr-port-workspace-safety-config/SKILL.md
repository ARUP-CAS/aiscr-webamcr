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
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

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

## Context to load first

1. `openspec/specs/workspace-safety-config/spec.md` — behavioral requirements and architecture
2. `AGENTS.md`
3. `.agents/scripts/README.md` — section **port_workspace_safety_config.py**
4. `.agents/plans/port-workspace-safety-config.plan.md` — execution procedures

## Steps

1. Ask: real home vs `--target-dir` for testing; optional `--backup`; any `--skip-cursor` / `--skip-codex` / `--skip-claude`.
2. Run `--list`, then `--dry-run` with the agreed flags; review output with the user.
3. After **explicit confirmation**, run again without `--dry-run`.
4. Do **not** run `sync_agent_configs.py` unless a separate approved plan says so.

## Iron Law

**IRON LAW:** `NEVER WRITE TO USER HOME CONFIG WITHOUT FIRST COMPLETING --dry-run AND RECEIVING EXPLICIT USER CONFIRMATION.`

No exceptions. Home config writes affect the user's entire environment — not just this repo.

## Note: package installs vs assistant sandbox

Cursor/Codex/Claude **workspace or sandbox** settings govern what the **assistant** can touch in the repo; they do **not** stop **`npm` / `pnpm` / `yarn` postinstall**, **`pip install`**, or **`docker build` / `docker pull`** from executing on the **developer machine** or CI worker. After **npm supply-chain** incidents, fix **lockfiles**, **registry pins**, and **org security** process — do **not** weaken sandbox, permission denies, or approval policy to make installs succeed.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The safety config looks fine to apply" | Always run `--dry-run` first and show the output to the user. |
| "It's the same template as before" | Run `--list` and `--dry-run` regardless; confirm before writing. |
| "I'll use --target-dir so it's safe" | Still requires `--dry-run` review and explicit confirmation. |

## Verification before completion

Before claiming this workflow complete, confirm:

- [ ] `--list` and `--dry-run` were run and output reviewed with the user.
- [ ] Explicit user confirmation received before the final write run.
- [ ] `sync_agent_configs.py` was **not** invoked (not part of this workflow).

## Plan and workflow

`.agents/plans/port-workspace-safety-config.plan.md`

**Registry fallback:** Load openspec/specs/workspace-safety-config/spec.md first for the durable behavioral contract; then run `.venv/Scripts/python.exe` `.agents/scripts/port_workspace_safety_config.py` (or `.venv/bin/python` on Unix) per `.agents/scripts/README.md` and `port-workspace-safety-config.plan.md` as the execution runbook; auto-installs missing `jsonschema`/`tomli-w` from `requirements-ci.txt` via `requirements_subset_install.py`; use `--backup` only if backups wanted; no sync without approval.

## Governance

- Config protection and workspace boundary: `AGENTS.md`, the current assistant entry doc for the tool in use when relevant, and `.agents/canonical_configs/governance_rules/workspace-boundary-safety.md`. Do not weaken safety config without explicit user intent.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow