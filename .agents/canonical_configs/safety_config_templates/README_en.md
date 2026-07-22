# safety_config_templates – user-level safety templates

([Czech](README.md))

```text
Language entry scope: This README_en.md is the sole operational instruction source for agents. README.md is the Czech human-facing twin; update both together when operational behaviour changes.
```

This directory holds **templates** for user-level (app-level) Codex and Claude Code configuration related to **sandboxing and workspace boundaries**. These are not project-root repo files; targets are typically under the user home directory. The retained templates carry only evidence-backed safety settings: redundant vendor defaults and non-portable, no-benefit overrides are omitted, so the former Cursor sandbox and Gemini snippet templates were removed.

## What consumes this

- **`port_workspace_safety_config.py`** – merges templates into `~/.codex/config.toml` and `~/.claude/settings.json` (merge rules and validation: [scripts/README_en.md](../../scripts/README_en.md)); target list: `workspace_safety_registry.py` (keeps bootstrap doctor checks aligned). Codex uses the current top-level `sandbox_mode`; an existing legacy `[sandbox].mode` is migrated and `[windows].sandbox` is preserved (the merge prints an advisory for the native Windows `elevated` sandbox but never changes it).

Workflow plan: [port-workspace-safety-config.plan.md](../../plans/port-workspace-safety-config.plan.md). Workspace-boundary governance: `AGENTS.md`, `.agents/canonical_configs/governance_rules/aiscr-workspace-boundary-safety.md`.

## Files in this directory

| File | Purpose |
| ---- | ------- |
| `codex_user_config.toml` | Template for user Codex `config.toml` (`approval_policy`, top-level `sandbox_mode`). |
| `claude_safety_snippet.json` | Partial for Claude `settings.json` – `sandbox`, sample `permissions.deny`, and a narrow allow-list for the repo-local `run_pre_commit_local.py` wrapper; the script merges with any existing file. The Claude sandbox runs on macOS/Linux/WSL2, not native Windows. |

## `schemas/` subdirectory

JSON Schema and notes: [schemas/README_en.md](schemas/README_en.md).

## Editing and risks

- Scripts **validate** JSON against `schemas/` and Codex TOML shape before writing; invalid templates abort before any write.
- Agents must not modify safety-related user config (sandbox, deny lists) unless the user strictly orders it; see `AGENTS.md` and `.agents/canonical_configs/governance_rules/aiscr-workspace-boundary-safety.md`.
- Keep sandbox and deny defaults tight. Shared pre-commit cache issues should be handled by approving only the repo-local `run_pre_commit_local.py` wrapper as a narrow exception, not by weakening these templates.

[Czech version](README.md)
