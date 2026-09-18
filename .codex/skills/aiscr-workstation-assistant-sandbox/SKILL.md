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

- This `.codex/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
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

## Embedded execution plan

### Plan: Port workspace safety config

> **OpenSpec migration:** Persistent behavioral requirements for this workflow now live in the workflow contract summarized in this compiled skill. This `.plan.md` file remains the reusable execution and governance layer for aiscr-management. See the identifiers and references stated in this workflow.

#### Context

This plan lives in **`aiscr-management`** (AIS CR management hub under the **ARUP‑CAS** GitHub organisation). It describes how to apply **repo templates** under repository-local governance material when present to the current user’s **app-level** tool configuration:

- **Cursor:** merge into `~/.cursor/sandbox.json` (or under `--target-dir`)
- **Codex:** merge into `~/.codex/config.toml`
- **Claude:** merge into `~/.claude/settings.json` (sandbox and permissions rules per script)

Templates are validated with JSON Schema and Codex structure checks **before** any write. The script [`.agents/scripts/port_workspace_safety_config.py`](../../../.agents/scripts/port_workspace_safety_config.py) may install missing Python packages using pinned lines from [`requirements-ci.txt`](../../../requirements-ci.txt) via [`.agents/scripts/requirements_subset_install.py`](../../../.agents/scripts/requirements_subset_install.py); prefer the repo **`.venv`** when running.

Typical use is **maintainer or local workstation** alignment with canonical templates, not day-to-day edits inside application repositories (webapps, APIs, data tools, vocab repos). Those repos may still copy the same script or templates via governance bootstrap or sync workflows when explicitly chosen.

#### Goals

- Preview merges with `--list` and `--dry-run`, then apply only after **explicit user confirmation**.
- Preserve user-specific keys where the merge logic allows; fail fast if existing target files are invalid JSON/TOML.
- Optional timestamped backups with `--backup` only when the user requests them.

#### Scope and assumptions

- **In scope:**
  - Running `port_workspace_safety_config.py` from `aiscr-management` (or a clone that contains the same repository-local governance material when present layout).
  - Reads and validation of templates under repository-local governance material when present before writes.
- **Out of scope:**
  - `sync_agent_configs.py`, sibling-repo writes, or propagating `.cursor`/`.claude`/`.codex` between repos unless a **separate** human-approved plan covers it.
  - Changing **protected** safety keys without explicit user intent (sandbox, permission denies, approval policy); see **Config protection** below.
  - **Weakening** sandbox, permission denies, or approval policy so that `npm install`, `pnpm install`, or similar succeeds after a **supply-chain** or malware concern — use lockfile/registry remediation and org security process instead; assistant sandbox does not control package lifecycle scripts on the host.
  - Treating shared pre-commit cache cleanup as a reason to relax sandbox defaults broadly; solve that with the narrow repo-local `run_pre_commit_local.py` wrapper exception instead.
- **Assumptions:**
  - Python 3 is available; a venv (prefer repo `.venv`) is used when possible so `pip install` from `requirements_subset_install.py` targets the intended environment.
- **Config protection:** Treat safety-related user config as **protected** unless the user strictly orders changes: do not weaken sandbox, permission denies, or approval policy. See `AGENTS.md`, `CLAUDE.md`, and the applicable governance rules.

#### Goals and steps (single-loop planning)

- **Goals:** As in **## Goals** above.
- **Ordering:** Complete context load and target/flag confirmation (**Steps 1–2**) before `--list` / `--dry-run` (**Step 3**). **Step 4** (apply) is **blocked** until the user explicitly confirms after reviewing dry-run output. **Step 5** (verification) follows a successful apply or documents dry-run-only completion.
- **Parallelism:** Clarification of flags or scripts may run alongside dry-run review; it does **not** replace human confirmation before writes.

#### Impacts

- **Paths affected (on apply):** `~/.cursor`, `~/.codex`, `~/.claude`, or paths under `--target-dir` when used for isolated testing.
- **Repositories:** Source templates and script live in **aiscr-management** (or equivalent checkout); this workflow does **not** mutate sibling AIS CR repositories.
- **Dependencies:** Optional `pip install` of subset packages (e.g. `jsonschema`, `tomli-w`) per `requirements-ci.txt` when imports are missing.
- **Risks:** Incorrect target directory or skipped dry-run can overwrite home config; mitigated by mandatory dry-run review and explicit confirmation before non-dry-run runs.
- **Governance files:** Executing this plan does not by itself require edits to `.cursor/rules/**` or `AGENTS.md`; treat any such changes as a separate task unless explicitly in scope.

#### Evaluation/recommendation

- **Recommend to proceed** when the user intends to align local Cursor/Codex/Claude safety-related config with validated templates and accepts home-directory (or `--target-dir`) writes after review.
- **Defer** if the target machine, venv, or approval to touch app-level config is unclear.
- **Reconsider scope** if the user actually needs **config sync across sibling repos** (`sync_agent_configs.py` / `orchestrate_local_agent_sync.py`); use the **config-sync** workflow instead with its own approved plan.

#### Execution approach

- Reason about script flags, `--target-dir` testing, `requirements_subset_install` behaviour, and verification commands (**script-first** for deterministic checks).
- Optionally cross-check against workspace-boundary and config-protection rules when scope or safety impact is ambiguous.

This does **not** replace reading `AGENTS.md`, `CLAUDE.md`, and the applicable governance rules.

#### Steps

##### Step 1 — Load context

- Read `AGENTS.md`, repository-local script documentation when present (section **port_workspace_safety_config.py**), this plan, and the applicable governance rules.

##### Step 2 — Confirm target and flags

- Confirm **default user home** vs **`--target-dir`** for isolated testing.
- Confirm optional **`--backup`** and any **`--skip-cursor`**, **`--skip-codex`**, **`--skip-claude`**.

##### Step 3 — List and dry-run (script-first)

From the repository root:

```text
Windows: .venv\Scripts\python.exe .agents/scripts/port_workspace_safety_config.py --list
Windows: .venv\Scripts\python.exe .agents/scripts/port_workspace_safety_config.py --dry-run
Unix: .venv/bin/python .agents/scripts/port_workspace_safety_config.py --list
Unix: .venv/bin/python .agents/scripts/port_workspace_safety_config.py --dry-run
```

Add `--target-dir`, `--backup`, or `--skip-*` as agreed. Review stdout/stderr with the user before any apply.

##### Step 4 — Apply after confirmation

- Only after **explicit user confirmation**, run the same command line **without** `--dry-run`.
- Do **not** run `sync_agent_configs.py` or other high-impact sync as part of this workflow unless a separate human-approved plan covers it.

##### Step 5 — Verify outcome

- Confirm exit code **0** and expected “merged” / “would merge” messages per target.
- **Efficiency:** Prefer one dry-run pass before apply; avoid redundant full merges.

#### Validation

- **Exit code** — `port_workspace_safety_config.py` exits 0 after successful dry-run or merge; non-zero on invalid existing JSON/TOML or template validation failure.
- **Dry-run discipline** — Confirm `--dry-run` output was reviewed and the user explicitly approved a non-dry-run run before any write.
- **Scope** — No `sync_agent_configs.py` or sibling-repo mutations as part of this plan unless covered by a separate approved plan.
- **Propagation** — N/A for a typical home-config port run. If templates or script sources in the repo were edited, follow normal PR workflow and validation for `.agents/**` changes (e.g. CI plan validation) as applicable.
- **Review** — Optional: `.venv\Scripts\python.exe -m unittest discover -s .agents/scripts/tests -p "test_port_workspace_safety_config.py" -v` (or `.venv/bin/python ...` on Unix)
- **Plan hygiene** — After editing this plan file, run `python .agents/scripts/validate_plans.py --strict` from repo root and fix reported issues.

#### Notes / Adaptation per repo

- **aiscr-management:** Primary home for templates and script; use repo `.venv` when invoking Python.
- **Other AIS CR repos:** If the same script and templates are present after bootstrap or sync, adapt paths relative to that repo root; still require dry-run and confirmation before writing outside the repo.
- **CI / headless:** This workflow assumes an interactive or explicit confirmation step; automated apply without human review is out of scope.

#### Options (planning phase)

**Delivery (choose before any commit or push):**

- **(A)** Create a branch and open a **draft** PR for any repo changes (recommended when templates or scripts were modified).
- **(B)** Create a branch only (no PR).
- **(C)** Local changes only (no branch, no push).

Do not commit or push until the user has chosen.

**Dry-run or read-only first:** Always run `--list` and `--dry-run` before a non-dry-run apply; only apply after the user confirms the preview.

**High-impact scripts:** This workflow is **not** an approval to run `sync_agent_configs.py` or `orchestrate_local_agent_sync.py apply`; obtain a separate approved plan for those.

**Sibling-repo branch:** N/A for the default workflow (writes are under user app home or `--target-dir`). If the task expands to changing another repo, state the branch per target repo and obtain confirmation before applying.

#### References

- Script: [`.agents/scripts/port_workspace_safety_config.py`](../../../.agents/scripts/port_workspace_safety_config.py)
- Dependencies helper: [`.agents/scripts/requirements_subset_install.py`](../../../.agents/scripts/requirements_subset_install.py)
- Templates: [repository-local governance material when present](../../../.agents/canonical_configs/safety_config_templates/README_en.md)

## Bundled scripts

The enrollment bundle installs these repository-local runtime scripts:

- `.agents/scripts/port_workspace_safety_config.py`
- `.agents/scripts/workspace_safety_registry.py`
- `.agents/scripts/requirements_subset_install.py`
- `.agents/scripts/log_utils.py`
- repository-local governance material when present
