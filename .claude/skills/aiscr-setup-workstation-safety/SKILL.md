---
name: aiscr-setup-workstation-safety
description: Use when the user asks to prepare validated assistant safety settings
  for their workstation. Inspect and prepare the app-level configuration port; the
  operator runs the porting script.
license: CC-BY-4.0
author: AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
---

<!-- SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- aiscr:compiled=aiscr-setup-workstation-safety -->
<!-- delivery-version: b257a1a89279be5e17cda3c133aa77b8c4d2706c 2026-11-07T11:18:12+01:00 -->

<!-- aiscr:entry-scope -->

**Entry scope (compiled)**

- This `.claude/skills/` skill is self-contained; use the workflow body below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-setup-workstation-safety — workstation assistant sandbox templates

Carry the templates from `.agents/canonical_configs/templates/workstation_safety/` into the user's **app-level** tool configuration using [`setup_workstation_assistant_safety.py`](../../../.agents/scripts/setup_workstation_assistant_safety.py).
The templates and the port are **operator-gated**: the template tree is edit-denied for governed sessions and changes only through the staged operator patch, and the porting script is deny-floored in the shell namespaces — the governed session **inspects and prepares**, the **operator runs the port** in their own terminal.
The script may **`pip install`** pinned `jsonschema` and `tomli-w` if they are missing in the interpreter the operator uses.

**When to use vs alternatives:** Use this workflow for **`setup_workstation_assistant_safety.py`** and **local workstation assistant permissions/sandbox JSON**.
For **policies on sensitive data in AI prompts, logs, and governance docs across repositories**, there is no separate workflow to invoke: the conduct binds through the governance rules loaded in every session, and the per-repository assessment is a maintainer-run governance audit (`security-privacy-ai-usage` spec).

`setup_hub_clone.py` doctor is the report-only neighbour: it shares `workspace_safety_registry` and reports missing registry home targets, but must not write those files.
Do not treat doctor output as apply; sibling-repo config delivery remains a separate `sibling_governance_delivery.py` run, out of scope here.

## Phase awareness

This is an **operational execution skill**: its subject is porting the workstation assistant sandbox and safety configuration, not spec-governed repository state.
It does not gate on OpenSpec context and never invokes `/openspec-propose`.
Execution boundaries: apply the approved sandbox and safety configuration; never weaken sandbox, permission, or approval settings, and create no new OpenSpec changes or backlog promotions.

## Context to load first

1. `AGENTS.md`

## Steps

### Context

This workflow lives in **`aiscr-management`** (AIS CR management hub under the **ARUP‑CAS** GitHub organization).
It describes how to apply **repo templates** under `.agents/canonical_configs/templates/workstation_safety/` to the current user’s **app-level** tool configuration.

Merge targets are owned by **`workspace_safety_registry.py`** (single source of truth, shared with the bootstrap doctor): each registered template merges into its user-level destination — e.g. Codex `~/.codex/config.toml`, the Codex user execpolicy rules `~/.codex/rules/default.rules`, and Claude `~/.claude/settings.json` — or the corresponding path under `--target-dir`.
The Codex user rules target is a **text-region** merge: the managed region between the delimited markers is replaced wholesale (`replace-governed-unit`), and the forbidden floor stays in force over its allow rules because execpolicy composes most-restrictive-wins with no catch-all.
A union-merged deny list keeps entries the merge stops carrying, so deny-entry pruning is **stateless and reporting-based**: `--prune` reports every delivered deny entry the current templates no longer carry, and that report — with no machine-local record — is the review surface, its entries possibly operator-authored.
The script prints an optional manual Cursor Workspace Trust hint at the end of a run; Workspace Trust is a manual editor setting the port does not write.

Templates are validated with JSON Schema and Codex structure checks **before** any write.
The script [`.agents/scripts/setup_workstation_assistant_safety.py`](../../../.agents/scripts/setup_workstation_assistant_safety.py) may install missing Python packages from pinned [`requirements-ci.txt`](../../../requirements-ci.txt) lines via [`.agents/scripts/lib/requirements_subset_install.py`](../../../.agents/scripts/lib/requirements_subset_install.py); prefer the repo **`.venv`** when running.

Typical use is **maintainer or local workstation** alignment with canonical templates, not day-to-day edits inside application repositories (webapps, APIs, data tools, vocab repos).
Those repos may still copy the same script or templates via governance bootstrap or sync workflows when explicitly chosen.

### Goals

- Inspect template integrity and workstation drift read-only, then hand the operator the exact apply command.
- The operator previews with `--list` and `--dry-run` and runs the apply themselves; the governed session never runs the porting script.
- Preserve user-specific keys where the merge logic allows; fail fast on invalid JSON/TOML in existing target files.
- Optional timestamped backups with `--backup` on user request.

### Scope and assumptions

- **In scope:**
  - Running `setup_workstation_assistant_safety.py` from `aiscr-management` (or a clone that contains the same `.agents/canonical_configs/templates/workstation_safety/` layout).
  - Reads and validation of `.agents/canonical_configs/templates/workstation_safety/` before writes.
- **Out of scope:**
  - Sibling-repo writes or propagating `.cursor`/`.claude`/`.codex` between repos without a **separate** human-approved sibling-governance-delivery run.
  - Changing **protected** safety keys (sandbox, permission denies, approval policy) without explicit user intent; see **Config protection** below.
  - **Weakening** sandbox, permission denies, or approval policy so that `npm install`, `pnpm install`, or similar succeeds after a **supply-chain** or malware concern — use lockfile/registry remediation and org security process instead; assistant sandbox does not control package lifecycle scripts.
  - Treating shared pre-commit cache cleanup as a reason to relax sandbox defaults broadly; use the narrow repo-local `run_pre_commit_local.py` wrapper exception instead.
- **Execution tiers:** Only the **in-repo** tier applies. `--target-dir` designates a workstation assistant directory for isolated testing, not a repository, so there is no repository target for the **hub-cockpit** tier to bind to and the writes land in the user's home, not a checkout.
  Tier semantics are defined under *Workflow execution tiers* in the `aiscr-ecosystem-governance` governance rule.
- **Assumptions:**
  - Python 3 is available; prefer repo `.venv` so `pip install` from `requirements_subset_install.py` targets the intended environment.
- **Config protection:** Treat safety-related user config as **protected** unless the user strictly orders changes: do not weaken sandbox, permission denies, or approval policy.
  See `AGENTS.md`, the assistant entry doc for the tool in use, and the `aiscr-workspace-boundary-safety` rule.

### Impacts

- **Paths affected (on apply):** every user-home destination registered in `workspace_safety_registry.py`, or paths under `--target-dir` for isolated testing.
- **Repositories:** Source templates and script live in **aiscr-management** (or equivalent checkout); it does **not** mutate sibling AIS CR repositories.
- **Dependencies:** Optional `pip install` of subset packages (e.g. `jsonschema`, `tomli-w`) per `requirements-ci.txt` on missing imports.
- **Risks:** An incorrect target directory or skipped dry-run can overwrite home config; mitigated by the operator-run apply after dry-run review, with the deny floor keeping the governed session out of the write path.
- **Governance files:** Executing this workflow does not by itself require edits to `.cursor/rules/**` or `AGENTS.md`; treat any such changes as a separate task unless explicitly in scope.

### Evaluation/recommendation

- **Recommend to proceed** when the user intends to align local assistant safety config with validated templates and accepts home-directory (or `--target-dir`) writes after review.
- **Defer** if the target machine, venv, or approval to touch app-level config is unclear.
- **Reconsider scope** if the user actually needs **governed config delivery across sibling repos** (`sibling_governance_delivery.py`); use the hub-run **sibling governance delivery** workflow, with its own approval gates.
  Do not use `setup_hub_clone.py` doctor as a write path for home targets.

### Execution approach

- Reason about flags, `--target-dir` testing, `requirements_subset_install` behaviour, and verification commands (**script-first** for deterministic checks).
- Optionally cross-check against workspace-boundary and config-protection rules when scope or safety impact is ambiguous.
- Clarifying flags or script behaviour may run alongside dry-run review, but never replaces the human confirmation required before any write.

This does **not** replace reading `AGENTS.md`, the current assistant entry doc for the tool in use, and the `aiscr-workspace-boundary-safety` rule.

### Procedure

#### Step 1 — Load context

- Read `AGENTS.md`, this workflow, and the `aiscr-workspace-boundary-safety` rule; the port script's inspection output documents its own flags.

#### Step 2 — Confirm target and flags

- Confirm **default user home** vs **`--target-dir`** for isolated testing.
- Confirm optional **`--backup`** and any per-target **`--skip-*`** from `workspace_safety_registry.py`.

#### Step 3 — Inspect (script-first, read-only)

The governed session does **not** run the porting script, not even `--list` or `--dry-run` — the deny floor covers every invocation shape.
Inspect with the read-only neighbours:

- Template integrity and registry consistency: the safety-config registry validator (`validate_workspace_safety_registry.py`), bundled so it runs from any checkout carrying this workflow, and, in a hub checkout only, `validate_command_allowlist_alignment.py`, which reads the curated command sources the hub alone carries.
- Workstation drift, effective governed lists and deny-entry carriage: `report_workstation_safety_posture.py --verbose` (read-only, bundled) — each target's effective allow and deny lists from the declared merge of current content and template, plus the stateless deny-entry carriage: what template and delivered config carry, and the surplus a prune would report for operator review.
- Workstation drift and missing home targets: `setup_hub_clone.py` doctor, a hub-checkout-only report-only neighbour — not part of the bundle, so a sibling reader does not receive it.
- Direct reading of the operator-patch protected templates to summarize a port's effect.

Summarize the findings and prepare the exact apply command line.

#### Step 4 — The operator applies

- Hand the operator the prepared command line.
  The operator runs `--list` and `--dry-run` first, reviews that output, then runs the apply in their own interactive terminal.
  The preview and dry-run precede any write outside the repository, and the confirmation follows a reviewed dry-run rather than standing in for one — reviewing it is not optional.
  The governed session cannot produce that preview, because the deny floor covers every invocation shape; the operator alone can satisfy it.
- The governed session never executes the porting script — the deny floor refuses it; the refusal is the design, not an obstacle to route around.
- Do **not** run high-impact sync as part of this workflow without a separate human-approved sibling-governance-delivery run.
- This workflow does not authorize `sibling_governance_delivery.py apply --approve`.

#### Step 5 — Verify outcome

- Ask the operator for the port's stdout/stderr (or exit code) and confirm the expected "merged" messages per target.
- Re-run the Step 3 read-only inspection and confirm the reported drift is gone.
- **Efficiency:** one inspection pass before and one after the operator's port; avoid redundant re-checks.

#### Step 6 — Template withdrawal and deny-entry prune (when templates lose deny rules)

When a template change withdraws deny rules — e.g. a reachability-based narrowing to the repository layer — the retired rules must leave both the templates and the delivered user-level configurations.
Deny-entry pruning is **stateless and reporting-based**: the current templates are the single source of truth, no machine-local deny-entry record exists, and the procedure resolves on every workstation from its delivered state:

- The registry, template and README changes land through staged operator patches.
  No apply is needed **before** the withdrawal — nothing need be recorded for the rules to become prunable.
- The operator runs one apply **after** the patches, refreshing the replace-governed targets (the Kilo permission block, the Codex rules region) wholesale from the withdrawn templates.
- The operator previews `--prune --dry-run`: the report lists every delivered deny entry the current templates no longer carry — retired contributions and operator-authored entries look the same, so the report is the review surface and every listed entry is read before removal.
- The operator runs `--prune` to remove those reviewed entries from the union-merged deny lists (Claude, Cursor).
- Inspect the carriage before and after with `report_workstation_safety_posture.py --verbose`: the surplus is the difference between the delivered state and the current templates, and an empty surplus is the completion signal.

### Validation

- **Operator apply** — the porting script's run is executed by the operator, not the governed session; the session's role ends at inspection, preparation, and post-port verification.
- **Dry-run discipline** — the operator reviews `--list` and `--dry-run` output before the write; the governed session does not execute either.
- **Prune discipline** — `--prune` runs only from the operator's terminal after a reviewed `--prune --dry-run`.
  Governed-key retirement is exact against the contribution manifest; deny-entry removal is stateless and reporting-based — it removes exactly the entries the reviewed report listed, and those entries may be operator-authored, so the review is not optional.
- **Scope** — No sibling-repo mutations as part of this workflow without a separate approved sibling-governance-delivery run.
- **Propagation** — N/A for a typical home-config port run.
  If templates or script sources in the repo were edited, follow the staged operator-patch flow for the template tree and the repository's validation suite for `.agents/**` changes.
- **Review** — Optional: `python -m unittest discover -s .agents/scripts/tests -p "test_setup_workstation_assistant_safety.py" -v`
- **Workflow-source hygiene** — After editing this workflow file, run `python .agents/scripts/validate_tool_parity.py --strict` from repo root and fix reported issues.

### Notes / Adaptation per repo

- **aiscr-management:** Primary home for templates and script; use repo `.venv` for Python.
- **Other AIS CR repos:** If the same script and templates are present after bootstrap or sync, adapt paths to that repo root; require dry-run and confirmation before writing outside the repo.
- **CI / headless:** This workflow assumes an interactive or explicit confirmation; automated apply without human review is out of scope.

### References

- Script: [`.agents/scripts/setup_workstation_assistant_safety.py`](../../../.agents/scripts/setup_workstation_assistant_safety.py)
- Dependencies helper: [`.agents/scripts/lib/requirements_subset_install.py`](../../../.agents/scripts/lib/requirements_subset_install.py)
- Templates: [`.agents/canonical_configs/templates/workstation_safety/README.md`](../../../.agents/canonical_configs/templates/workstation_safety/README.md)

### Execution using subagents

**Posture: declines.**
This workflow delegates nothing: every inspection step names a read-only script, and the deny floor covers every invocation shape of the porting script, so only the operator can produce the preview or the apply.

The posture vocabulary, the default that governs a workflow declaring none, the declared return contracts, and the admission test are owned by `aiscr-quality-first-execution`.

<!-- aiscr:gen:id=guardrails -->

## Iron Law

**IRON LAW:** `NEVER EXECUTE THE WORKSTATION PORT FROM A GOVERNED SESSION. THE OPERATOR RUNS IT IN THEIR OWN TERMINAL AFTER REVIEWING THE DRY-RUN.`

No exceptions.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The safety config looks fine to apply" | Inspect with the read-only validators and hand the operator the command; never run the port. |
| "It's the same template as before" | The template tree is operator-patch protected — if it changed, the change came through a staged patch; verify that instead. |
| "The deny blocked my --dry-run, I'll work around it" | The refusal is the design. Inspect with the read-only neighbours and let the operator run the script. |

<!-- aiscr:endgen -->

## Verification before completion

Before claiming this workflow complete, confirm:

- [ ] Read-only inspection ran and its findings were summarized for the operator.
- [ ] The exact apply command line was handed to the operator, who ran the port themselves.
- [ ] Post-port verification confirmed the reported drift is gone.
- [ ] If a template withdrawal was in scope, the patches landed before the apply, the prune ran from a reviewed dry-run, and `report_workstation_safety_posture.py --verbose` shows an empty surplus.
- [ ] `sibling_governance_delivery.py` sibling sync was **not** invoked — not part of this workflow.

## Governance

- Config protection and workspace boundary: `AGENTS.md`, the assistant entry doc for the tool in use when relevant, and the `aiscr-workspace-boundary-safety` rule.
  Do not weaken safety config without explicit user intent.
- The agent-side phases (inspect, prepare, verify) are read-only; the apply belongs to the operator, enforced mechanically by the deny floor on the porting script.
  Prefer the repository venv when the operator runs it; the script may install only its pinned missing dependencies.
  Do not combine it with sibling sync apply without a separately approved task.

## Valid next steps

- Confirm the applied sandbox and safety configuration with its owner; acting further is separate work.
- `/aiscr-setup-workstation-safety` — re-run this workflow when the safety configuration changes.
- Read `.agents/canonical_workflows_context.md` and follow the **Usage** section before loading a different workflow's context.

## Bundled scripts

The enrollment bundle installs these repository-local runtime scripts:

- `.agents/scripts/setup_workstation_assistant_safety.py`
- `.agents/scripts/lib/__init__.py`
- `.agents/scripts/lib/workspace_safety_registry.py`
- `.agents/scripts/lib/requirements_subset_install.py`
- `.agents/scripts/lib/repo_layout.py`
- `.agents/scripts/lib/log_utils.py`
- `.agents/scripts/lib/proc_utils.py`
- `.agents/scripts/report_workstation_safety_posture.py`
- `.agents/scripts/validate_workspace_safety_registry.py`
- `.agents/scripts/lib/redacting_reader.py`
- `.agents/scripts/lib/vendor_matrix_registry.py`
- `.agents/canonical_configs/templates/workstation_safety`
