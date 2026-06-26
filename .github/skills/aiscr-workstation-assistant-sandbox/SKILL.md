---
name: aiscr-workstation-assistant-sandbox
description: Merge validated Codex and Claude safety templates into user app-level
  config; dry-run first, explicit confirmation; may pip-install jsonschema/tomli-w;
  optional --backup and --target-dir; not orchestrate_local_agent_sync apply nor retired
  sync_agent_configs operator path.
---

<!-- aiscr:compiled=aiscr-workstation-assistant-sandbox -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.github/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-workstation-assistant-sandbox — workstation assistant sandbox templates

Merge templates from repository-local governance material when present into the user’s **app-level** Codex config and Claude settings using [`port_workspace_safety_config.py`](../../../.agents/scripts/port_workspace_safety_config.py). Run it from the repo virtualenv when present. The script may **`pip install`** pinned `jsonschema` and `tomli-w` if they are missing in the current interpreter.

**When to use vs alternatives:** Use this workflow for **`port_workspace_safety_config.py`** and **local workstation assistant permissions/sandbox JSON**. For **policies on sensitive data in AI prompts, logs, and governance docs across repositories**, use **`/aiscr-ai-data-exposure-policy`** instead (`security-privacy-ai-usage` spec).

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

1. the workflow contract summarized in this compiled skill — behavioral requirements and architecture
2. `AGENTS.md`
3. repository-local script documentation when present — section **port_workspace_safety_config.py**
4. the embedded execution plan below — execution procedures

## Steps

1. Ask: real home vs `--target-dir` for testing; optional `--backup`; any `--skip-codex` / `--skip-claude`.
2. Run `--list`, then `--dry-run` with the agreed flags; review output with the user.
3. After **explicit confirmation**, run again without `--dry-run`.
4. Do **not** run `orchestrate_local_agent_sync.py` `apply --approve` or treat the retired `sync_agent_configs.py` module as an operator workflow unless a separate approved plan says so.

<!-- aiscr:gen:id=guardrails -->
## Iron Law

**IRON LAW:** `NEVER WRITE TO USER HOME CONFIG WITHOUT FIRST COMPLETING --dry-run AND RECEIVING EXPLICIT USER CONFIRMATION.`

No exceptions. Home config writes affect the user's entire environment — not just this repo.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The safety config looks fine to apply" | Always run `--dry-run` first and show the output to the user. |
| "It's the same template as before" | Run `--list` and `--dry-run` regardless; confirm before writing. |
| "I'll use --target-dir so it's safe" | Still requires `--dry-run` review and explicit confirmation. |
<!-- aiscr:endgen -->

## Verification before completion

Before claiming this workflow complete, confirm:

- [ ] `--list` and `--dry-run` were run and output reviewed with the user.
- [ ] Explicit user confirmation received before the final write run.
- [ ] `orchestrate_local_agent_sync.py` / retired `sync_agent_configs.py` sibling sync was **not** invoked (not part of this workflow).

## Governance

- Config protection and workspace boundary: `AGENTS.md`, the current assistant entry doc for the tool in use when relevant, and the applicable governance rules. Do not weaken safety config without explicit user intent.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- Read the identifiers and references stated in this workflow and follow the **Usage** section before loading a different workflow's context.
