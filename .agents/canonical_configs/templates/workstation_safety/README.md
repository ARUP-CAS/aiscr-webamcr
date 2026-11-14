<!-- SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- delivery-version: c35418343fe8896348732bd54f8256de17338f8d 2026-11-07T14:33:16+01:00 -->

# workstation_safety – user-level safety templates

This directory holds **templates** for user-level (app-level) assistant configuration related to **sandboxing and workspace boundaries**.
These are not project-root repo files; targets are typically under the user home directory.
Templates carry only evidence-backed safety settings: a vendor gets a template here when a setting is portable and improves on that vendor's own default — Codex and Claude Code from the start, Cursor and Gemini re-admitted by the agent-safety floor change on documented, probe-verified permission surfaces.

## What consumes this

- **`setup_workstation_assistant_safety.py`** – merges each registered template into its user-home destination; the target list, governed units and reconciliation policies live in `workspace_safety_registry.py` (keeps bootstrap doctor checks aligned).
  Codex uses the current top-level `sandbox_mode`; an existing legacy `[sandbox].mode` is migrated and `[windows].sandbox` is preserved (the merge prints an advisory for the native Windows `elevated` sandbox but never changes it).

Workflow: [`aiscr-setup-workstation-safety.md`](../../workflows/aiscr-setup-workstation-safety.md).
Workspace-boundary governance: `AGENTS.md`, `.agents/canonical_configs/governance_rules/aiscr-workspace-boundary-safety.md`.

## Files in this directory

| File | Purpose |
| ---- | ------- |
| `codex_user_config.toml` | Template for user Codex `config.toml` (`approval_policy`, top-level `sandbox_mode`). |
| `codex_user_rules.rules` | Template for Codex `~/.codex/rules/default.rules` — the irreversible-operation and destructive-state deny floor (the curated `codex_forbidden` set) in rendered `prefix_rule(..., decision = "forbidden")` form, each rule carrying its own threat/benefit justification, so the floor binds a Codex session opened outside any governed repository. The operator-reserved entry points (the staged-patch apply tool, the port itself) carry no rule here: they name tooling that exists only inside governed trees, which the repository-layer rules file covers, and the apply tool's interactive-terminal gate is the structural backstop for any other reach. Delivered as a delimited managed region: the merge replaces the region wholesale and preserves operator-authored rules outside it byte-for-byte. No catch-all exists in execpolicy, so this deny set is the only floor the file provides; composing it with the repository-layer rules file is most-restrictive-wins and order-independent. |
| `cursor_cli_config.json` | Template for Cursor `~/.cursor/cli-config.json` – the full irreversible and destructive-state shell deny set (the same floor the repository project file carries for the CLI actor, minus the operator-reserved entry points that are withheld at this layer) plus the pinned `approvalMode: allowlist`, so CLI sessions outside any repository refuse everything not allowed and keep the deny layer that survives `--force`. The write/read path tokens are carried only in the repository project file: they were refuted on the CLI actor's file tools (FA-24) and are recorded as such. |
| `gemini_user_settings.json` | Template for Gemini `~/.gemini/settings.json` – the yolo-mode lock (`security.disableYoloMode: true`, the one key documented to hold even against a command-line flag) and the pinned tool allowlist (the shell not admitted; a drifted recipient list is narrowed on apply), merged while preserving the operator's auth and personal keys. The runtime is not drivable by this operator, so the template rests on configuration plus documentation. |
| `kilo_user_config.jsonc` | Template for Kilo `~/.config/kilo/kilo.jsonc` – the **permission block delivered as a unit**: the hardened read patterns (environment, key and credential files denied rather than asked, the `.env.example` exception retired), the full shell floor (verb allows without `printenv`, the developer working set at both layers, deny catch-all, redirection catch, and the irreversible, drive-root and recovery-path deny sets; the operator-reserved entry points are withheld at this layer), the fetch keys set to ask, `external_directory: deny` and the runaway-loop deny. The merge replaces the permission block wholesale — the maps are last-match-wins, so a per-key union would let recipient allow entries survive ahead of template denies — while preserving every other recipient key (the provider block with its credentials, display and model settings). |
| `claude_safety_snippet.json` | Partial for Claude `settings.json` – `sandbox` (with `excludedCommands` for the Windows interpreter shapes that cannot be sandboxed), the machine-scope `permissions.deny` list (system and home paths, the full irreversible and destructive-state shell floor with the operator-reserved entry points withheld at this layer, filesystem-server tool denies, and workstation control-surface edit denies), the workspace-anchored credential-pattern rules that also protect a non-repo session's own working directory, and the pinned workstation mode pair (`defaultMode: auto`, known and desired; bypass mode disabled). The script merges with any existing file. The Claude sandbox runs on macOS/Linux/WSL2, not native Windows. The relative sibling-repository allowlist lives in the repository settings file, not here: relative paths in user-level settings resolve against an arbitrary session's starting directory, so they are a project-layer concept by nature. The command entries carried here include the developer working set at both layers — toolchains, language package managers, build/test/lint runners, VCS and hosted-VCS writes, HTTP clients, and local container workflows — with generic OS shells, remote-shell/copy clients, system package managers and the shell file-write shapes deliberately excluded. The repository and workstation layers receive the same relief set because the runtime merges the workstation allows into a governed checkout; the deny floor and the catch-all remain in force, and an unlisted shape is refused rather than prompted. |

## `schemas/` subdirectory

JSON Schema and notes: [schemas/README.md](schemas/README.md).

## Editing and risks

- Scripts **validate** JSON against `schemas/`, Codex TOML shape, and the rules template with `codex execpolicy check --rules` (the runtime's own parser) before writing; invalid templates abort before any write.
- Agents must not modify safety-related user config (sandbox, deny lists) unless the user strictly orders it; see `AGENTS.md` and `.agents/canonical_configs/governance_rules/aiscr-workspace-boundary-safety.md`.
- Keep sandbox and deny defaults tight.
  The developer working set is declared at both layers, because the runtime merges the workstation allows into a governed checkout; repo-anchored shapes (the script tree, the change folders) remain `repository`-layer entries, and the catch-all refuses anything outside the carried set.
- The operator-reserved entry points (`run_operator_patch.py`, `setup_workstation_assistant_safety.py`) are withheld from these templates on a recorded reachability assessment: they name tooling that exists only inside governed trees, which the repository layer covers where the tooling exists, and the apply tool's interactive-terminal gate is the structural backstop for any other reach.
  A workstation-layer deny naming them requires re-recording that assessment or the deny-floor narrowing check reports the gap.

## Operation scope

Broad live-infrastructure grants for Terraform, OpenTofu, kubectl, Helm, and Ansible are excluded from both default layers.
Projects opt in for named environments and operations through their native permission and governance surfaces.
Local container development remains available; persistent-volume destruction carries direct brakes, with argument-position gaps recorded in the safety registry.
Broad clean brakes can also refuse dry-run inspection.

Command admission does not grant task authority.
Scripts, runtimes, APIs, and hosted workflows retain the same effect-based obligations.
The basic rules are visible in the generated `AGENTS.md` entry and normal assistant rule readers.
This permission port does not install global instructions; conduct loading outside those entry surfaces remains unestablished.
