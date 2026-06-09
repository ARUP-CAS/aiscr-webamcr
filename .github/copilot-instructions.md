# AIS CR — repository guidance for GitHub Copilot

This file is a **Tier-1 digest** for GitHub Copilot in AIS CR repositories. It is propagated via `specialized_sync_assets.toml` (`github-copilot-instructions`) when `.sync-manifest.json` includes the asset group `shared-github-copilot-instructions`. It is **not** a per-workflow substitute for Cursor skills, Claude commands, or Codex skills; see the **Fallback** column in `.agents/canonical_configs/references/canonical_workflows_context.md` for manual steps when those tools are not used.

## Governance (read first)

- **`AGENTS.md`** — scope, planning-first workflow, script approval, sibling-repo rules.
- **`.cursor/rules/`** — canonical Cursor rules for this repo (when present); ecosystem repos often have **`ecosystem-cursor-governance.mdc`** and **`workspace-boundary-safety.mdc`**.
- **Planning and usage** — non-trivial work in the management hub follows a **single-loop** planning phase with human approval before mutating steps; record **one** end-of-run usage log entry for significant tasks (see `.cursor/rules/planning-and-usage-logging.mdc` and `.cursor/rules/model-logging.mdc` where mirrored).

## Where workflows live

- **Reusable plans:** `.agents/plans/*.plan.md` (schema and validation in-repo).
- **Skillset / workflow map:** `.agents/canonical_configs/references/aiscr_skillset_mapping.md` and **`canonical_workflows_context.md`** (prescribed context per workflow).
- **Scripts:** `.agents/scripts/` — do **not** run `sync_agent_configs.py`, `orchestrate_local_agent_sync.py` **apply**, or other high-impact automation without explicit human approval and an approved plan.

## Secrets and boundaries

- Do not commit secrets or paste production PII into prompts.
- Stay inside the workspace unless the user explicitly requests otherwise; state impact for out-of-workspace work (see workspace boundary rules in `.cursor/rules/` when present).

## Adding a new standard **aiscr-** workflow

When this repo uses Copilot instructions, update **this file** so new workflows are discoverable: mention the slug, point to the plan under `.agents/plans/`, and align with the **cross-tool** checklist in **`ecosystem-cursor-governance.mdc`** (Cursor skill, Claude command, Codex skill, By-tool table, skillset mapping, and Copilot digest when the asset group is enabled).
