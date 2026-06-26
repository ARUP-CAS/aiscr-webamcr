# AIS CR — repository guidance for GitHub Copilot

This file is the **required repository digest for GitHub Copilot** in AIS CR repositories that use Copilot for workflow context. It is **committed directly** in each such repo. The hub repo **`aiscr-management`** holds the canonical reference; from the hub run `python .agents/scripts/report_copilot_instructions_drift.py --repos-root ..` as an **advisory** check to compare sibling checkouts and recommend PRs when they drift.

<!-- aiscr:stop-anchor -->

## Entry scope

- Stay in this Copilot surface first; do not open parallel vendor trees by default just in case.
- Use `.github/copilot-instructions.md` plus shared governance docs before touching `.cursor/`, `.claude/` or `.codex/`.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.
- When a target directory has both `README.md` and `README_en.md`, prefer the English counterpart for operational reading.

## Vendor-specific entry points (read this first)

AIS CR mirrors the same **`aiscr-*` workflow slugs** into **separate config roots**, because **each product loads its own tree**—there is no single universal skills file:

| Product / runtime | Typical entry (when mirrored in this repo) |
| --- | --- |
| **GitHub Copilot** | **This file** (`copilot-instructions.md`) for governance context, plus **`.github/skills/aiscr-*/SKILL.md`** self-contained Agent Skills (Copilot CLI + cloud agent) for the `aiscr-*` workflows. |
| **Cursor** | `.cursor/skills/`, `.cursor/rules/`, `.cursor/agents/` |
| **Claude Code** | `.claude/skills/`, `.claude/commands/`, `.claude/agents/` |
| **Codex** | `.codex/skills/`, etc. |

So: **this digest does not substitute** for mirrored **`skills/`** under `.cursor/`, `.claude/`, `.codex/` when you are working **in those products**—open the matching tree and its `README_en.md` pointer when that pair exists (see **Fallback** in `.agents/canonical_configs/references/canonical_workflows_context.md` when a tool is absent). When you are working **in Copilot**, use this digest and shared kernel docs below.

## Shared kernel (governance)

- **`AGENTS.md`** — scope, planning-first workflow, script approval, sibling-repo rules.
- **`.cursor/rules/`** — generated Cursor rule stubs for this repo (when present); canonical bodies live under **`.agents/canonical_configs/governance_rules/`** (for example **`aiscr-ecosystem-governance.md`**, **`aiscr-workspace-boundary-safety.md`**).
- **Planning and usage** — non-trivial work in the management hub follows a **single-loop** planning phase with human approval before mutating steps; record **one** end-of-run usage log entry for significant tasks (see **`aiscr-planning-core.md`**, **`aiscr-usage-logging.md`**, and **`aiscr-model-logging.md`** under `.agents/canonical_configs/governance_rules/`).

## Where workflows live

- **Reusable plans:** `.agents/plans/*.plan.md` (schema and validation in-repo).
- **Skillset / workflow map:** `.agents/canonical_configs/references/aiscr_skillset_mapping.md` and **`canonical_workflows_context.md`** (prescribed context per workflow). Read `canonical_workflows_context.md` and follow its **Usage** section to load context in order before executing a standard workflow.
- **OpenSpec requirement layer:** `openspec/specs/` for persistent capability contracts and `openspec/changes/` for change-scoped artifacts.
- **Scripts:** `.agents/scripts/` - do **not** run `sync_agent_configs.py`, `orchestrate_local_agent_sync.py` **apply**, or other high-impact automation without explicit human approval and an approved plan.
- **Overhead workflow:** `aiscr-overhead-analysis` uses `.agents/scripts/measure_workflow_overhead.py` for measured workflow, plugin, recommendation, and snapshot-diff output (modes per `canonical_workflows_context.md`).

## OpenSpec

This repo now versions OpenSpec artifacts directly:

- Capability specs: `openspec/specs/<domain>/spec.md`
- Change artifacts: `openspec/changes/<change>/`
- Repo config and schema selection: `openspec/config.yaml`

Copilot-specific OpenSpec prompts are generated under `.github/prompts/opsx-*.prompt.md`, and mirrored OpenSpec skills live under `.github/skills/openspec-*/`. AIS CR `aiscr-*` workflows are delivered as self-contained Copilot Agent Skills under `.github/skills/aiscr-*/SKILL.md` (read by the Copilot CLI and the cloud coding agent), not as prompt files. OpenSpec is the `what` layer for migrated workflows; `AGENTS.md` and the canonical governance docs remain the `how` and approval layer.

### OpenSpec Mode Transfer Gating

When using OpenSpec workflows (`/opsx:*` commands), agents MUST follow mode transfer gating rules:

- **Iron Law:** `NEVER TREAT ARTIFACT COMPLETION AS IMPLICIT APPROVAL TO IMPLEMENT`
- **Mode boundaries requiring explicit approval:**
  - Explore → Plan: When exploration concludes
  - Plan → Implement: When planning artifacts are complete
  - Any → Archive: When archiving a change
- **Hard stop:** After completing planning artifacts, stop and offer `/opsx:apply <slug>` - do not silently continue

See `.agents/canonical_configs/governance_rules/aiscr-planning-core.md` section 1.5 for full requirements.

## Ecosystem-wide workflows (hub)

Cross-repo config sync, **`validate_tool_parity` / manifest maintenance**, and updates to `asset_manifest.toml` are **normally run from the `aiscr-management` repository** (local clone next to sibling repos or via GitHub / `gh`). At the hub, parity checks commonly cover **each** generated **skills/** tree under the assistant-integration roots registered for workflow parity (paths typically include **.cursor/skills/**, **.claude/skills/**, **.codex/skills/**) so slugs stay aligned across vendors; that does **not** mean Copilot executes those folders the same way Cursor does. In Cursor, see **`.cursor/rules/aiscr-ecosystem-hub-workflow-routing.mdc`** when present for the short routing summary (canonical body: **`aiscr-ecosystem-hub-workflow-routing.md`**). This digest does not replace the **per-assistant** skill surfaces enrolled for the target repository.

## Secrets and boundaries

- Do not commit secrets or paste production PII into prompts.
- Stay inside the workspace unless the user explicitly requests otherwise; state impact for out-of-workspace work (see workspace boundary rules in `.cursor/rules/` when present).

## Adding a new standard **aiscr-** workflow

When this repo uses Copilot instructions, update **this file** so new workflows are discoverable: mention the slug, point to the plan under `.agents/plans/`, and align with the **cross-assistant** checklist in **`.agents/canonical_configs/governance_rules/aiscr-ecosystem-governance.md`** (matching entries under `.cursor/skills/`, `.claude/skills/`, `.codex/skills/`, `.gemini/skills/`, and `.github/skills/aiscr-*/`, By-assistant-product table, skillset mapping, and this Copilot digest when the asset group is enabled).

- **`aiscr-agent-vendor-introduction`** - Plan: `.agents/plans/agent-vendor-introduction.plan.md`; prompt: `.agents/prompts/agent_vendor_introduction.md`; for onboarding or fixing a vendor integration against `agent_tool_feature_matrix.md`, `mandatory_vendor_doc_urls.toml`, `sync_policy.py` (`AGENT_FOLDERS` + `REPO_ROOT_SYNC_IDS`), and `config-sync.plan.md`. Scope follows the **session charter**; cross-assistant **`aiscr-*`** registration runs only when the charter adds or renames that workflow (see `aiscr-ecosystem-governance.md` under `.agents/canonical_configs/governance_rules/`).
- **`aiscr-workflow-review`** - Plan: `.agents/plans/workflow-review.plan.md`; spec: `openspec/specs/workflow-review/spec.md`; reviews one standard workflow's role, usefulness, overlap, governance fit, and lifecycle outcome, then updates `workflow_review_state.toml` and `.agents/workflow-reviews.md` while routing findings through OpenSpec.
- **`aiscr-overhead-analysis`** - No backing plan; spec-first workflow for `openspec/specs/overhead-measurement/spec.md` and `openspec/specs/plugin-coverage/spec.md`. Preferred script entry point: `.agents/scripts/measure_workflow_overhead.py` (`--dry-run`, `--diff`, `--recommendations`); outputs under `.agents/reports/overhead/`; advisory only — include impact analysis before suggesting cleanup.
