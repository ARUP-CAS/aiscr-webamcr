---
name: aiscr-agent-vendor-introduction
description: 'Introduce or remediate an agent-tool vendor in the AIS CR hub: matrix/TOML,
  sync policy (AGENT_FOLDERS and repo-root REPO_ROOT_SYNC_IDS), parity, local_configs;
  optional cross-tool aiscr-* workflow registration when the session charter requires
  it.'
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-agent-vendor-introduction.md -->

# aiscr-agent-vendor-introduction

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

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

1. `openspec/specs/agent-vendor-onboarding/spec.md` — durable behavioral requirements and vendor architecture
2. `AGENTS.md`, `.agents/README.md` — governance and scope
3. `agent_tool_feature_matrix.md`, `mandatory_vendor_doc_urls.toml` — machine registry
4. `sync_policy.py` — `AGENT_FOLDERS` order, `REPO_ROOT_HUB_ENTRY_DOCS`, and `REPO_ROOT_SYNC_IDS`
5. `config-sync.plan.md` — sync vocabulary and special handling
6. `.agents/canonical_configs/governance_rules/aiscr-ecosystem-governance.md` when the **session charter** adds or renames a standard **`aiscr-*`** workflow (Phase 6)
7. `governance_stable_ids.md` — lookup `parity.*` ids enforced by `validate_tool_parity.py`
8. `.agents/plans/agent-vendor-introduction.plan.md` — execution procedures and phased workflow

## When to use

- New vendor path in the hub stack, or **brownfield** fix for drift / incomplete workflow-mirror surface / matrix churn.

## Plan and prompt

- **Plan:** `.agents/plans/agent-vendor-introduction.plan.md`
- **Prompt:** `.agents/prompts/agent_vendor_introduction.md`

## Mechanical truth (hub vs CI)

- **Matrix prose alone is not proof of completion.** Record evidence as passing validators and on-disk artefacts under **committed** paths (`local_configs`, hub-root entry docs, generated vendor trees).
- **Gitignored assistant roots** (common examples: entries under `/.cursor/`, tool-specific dirs in root `.gitignore`): clean clones and CI often have **no** repo-root tool directories. The **authoritative** hub baseline for parity is **`.agents/local_configs/<repo>/…`**. Do **not** infer completion from missing folders at the repo root alone—open **`local_configs`** and the matrix **hub paths** for that product.
- **Committed `aiscr-*` workflow skills:** Where the matrix + `canonical_workflows_context` map registry slugs to a product’s committed skills tree, `validate_tool_parity.py` enforces **`SKILL.md` per slug** under the **hub `local_configs`** path for that product (stable id **`parity.registry-slug-skills-complete`** among others). Run **`generate_workflow_skills.py`** with the **default `--tools`** so **every** generator-backed assistant root that emits those mirrors is updated—**narrow `--tools` only when the charter explicitly limits scope** and you accept stale trees for omitted tools.
- **Sibling repos:** The hub holds **full** baselines where parity and **`repos.toml`** require them. Siblings usually carry **subset** trees per **profile, sync recipes, and ESS**—do not copy the entire hub workflow surface into every sibling unless the **charter** or **`ecosystem-sibling-workflow-mirror`** (and related repo policy) explicitly requires it.

**Product registry semantics**

- `mandatory_vendor_doc_urls.toml` is now two machine layers:
  - `[[product]]`: onboarding metadata (`integration_class`, `sync_token`, `hub_entry_docs`, `review_validation_mode`, `subagent_mode`, `skill_mode`)
  - `[[entry]]`: per-asset matrix rows
- Keep the namespace split explicit:
  - `product id`: matrix/TOML id such as `gemini`
  - `governance_vendor_id`: generator/parity id such as `gemini`
  - `workflow_skill_tool`: `generate_workflow_skills.py` tool id when committed `aiscr-*` skills exist
- Do not rely on naming coincidence; declare the mapping in the product row.

**Vendor classes**

| Class | What it means |
| --- | --- |
| `agent_folders` | Standard folder-backed products with filesystem subagents and committed AIS CR skills when the matrix says so |
| `repo_root` | Repo-root trees and/or hub-root entry docs managed outside `AGENT_FOLDERS` |
| `review_only` | Qodo-like review/config-heavy vendors that may expose third-party skills without committed AIS CR skill mirrors |
| `digest_only` | Copilot-like root instruction/digest products with no synced tool tree baseline |

## Skills row by vendor class

Treat rows below as **patterns**; confirm each product against **`agent_tool_feature_matrix.md`** and TOML (names and paths drift).

| Pattern | Hub committed `aiscr-*` workflow skills when matrix says so? | Primary mechanism |
| --- | --- | --- |
| `AGENT_FOLDERS` products (see `sync_policy.AGENT_FOLDERS`) | Yes — every registry slug for mirrored roots | `generate_workflow_skills.py` + `validate_tool_parity.py` |
| Additional products whose **skills** row maps to the same registry under **`local_configs`** (any extra generator **tool** id) | Yes — same slugs under that product’s **`local_configs`** skills path | Same generator; **include that tool** in the regen (default `--tools` does this) |
| Products whose **skills** row is **N/A** or third-party marketplace installs | **No** — not the hub **`aiscr-*`** baseline | Matrix **`na_reason`** + TOML; no `generate_workflow_skills.py` for those rows unless charter says otherwise |
| Products with **rules / entry docs only** (no committed `aiscr-*` skills path) | **No** `aiscr-*` skills row | Paths per matrix/TOML; see **`REPO_ROOT_*`** / **`AGENT_FOLDERS`** as applicable |

## Matrix cell coverage (TOML vs disk)

- **Machine grid:** `mandatory_vendor_doc_urls.toml` is one row per **(product, asset_type)** matching **`agent_tool_feature_matrix.md`**. **`validate_agent_tool_feature_matrix.py`** checks each non-empty **`hub_committed_path`** against the management repo root (the single source of truth for hub assistant trees and other hub-only paths).
- **Sibling `local_configs`:** **`validate_matrix_local_configs_cells.py`** reads the same TOML and, for each **`repos.toml`** row, checks every **non-review** matrix path whose first segment matches a **`sync`** token (**.cursor**, **.claude**, **.codex**, **.gemini**, **.qodo**). It validates directories/files exist and minimal content (rules/agents/hooks files, **Gemini** triple, **Qodo** README pair). **`asset_type == review`** is **skipped** (review services are wired separately). Messages use **`parity.matrix-local-configs-vendor-cells`**. **Skills:** full **`aiscr-*`** registry closure remains **`validate_tool_parity.py`** on the hub; siblings keep a **`*/skills/`** README stub unless **`ecosystem-sibling-workflow-mirror`** ships real **`SKILL.md`** trees.
- **New vendor or new `REPO_ROOT_SYNC_IDS` token:** extend **`validate_matrix_local_configs_cells.py`** when new path shapes need extra checks; keep TOML **`hub_committed_path`** honest.
- **Gemini governance files:** after canonical **`governance_rules/<stem>.md`** or the governance stem registry changes, run **`python .agents/scripts/generate_governance_rules.py`**. The unified generator refreshes **`.gemini/context/<stem>.md`** and committed **`.gemini/settings.json`** **`context`** + advisory **`hooks`** (intent parity with Cursor/Claude via **`gemini_cli_hooks.py`** — stdout JSON only) in the hub root and sibling `local_configs` entries.

## TOML `hub_committed_path` — avoid silent deferrals

Keep **`agent_tool_feature_matrix.md`** and TOML aligned: if the matrix or vendor docs describe a **committed hub artefact**, the matching TOML row must name it in **`hub_committed_path`** (non-empty) so **`validate_agent_tool_feature_matrix.py`** exercises the check.

- **`workflow_registry_hub`:** Use the **same** machine registry path for **every** product row: **`.agents/canonical_configs/references/canonical_workflows_context.toml`** (plus **`repo_reference_path`** to the human **`.md`**). Do **not** leave **`hub_committed_path`** empty for non-`AGENT_FOLDERS` vendors while the matrix **Workflow registry (hub)** column still says “same” — that would skip the TOML existence check for those rows.

- **Review rows:** When customization reuses a surface already listed elsewhere, point **`hub_committed_path`** at it (e.g. **Codex** review → root **`AGENTS.md`**). **Claude Code** optional repo-root **`REVIEW.md`** may remain uncommitted in the hub — empty path is honest there; do not pretend a different file.
- **Gemini `subagents`:** Repo-local **`.gemini/agents/*.md`** (generated **`aiscr-*`** alongside Cursor/Claude/Codex) — not a “no files” deferral when vendor docs support project agents.

## Iron Law

**IRON LAW:** `NEVER CLAIM VENDOR INTRODUCTION COMPLETE WITHOUT ALL COMPLETION GATES FOR THAT VENDOR CLASS AND SESSION CHARTER.`

**Standard assistants (`AGENT_FOLDERS` vendors):** matrix + TOML, **`repos.toml` `sync`**, `local_configs`, **`validate_tool_parity.py`**.

**Repo-root vendors (no new `AGENT_FOLDERS` root):** **Full matrix** + TOML; separate **`REPO_ROOT_HUB_ENTRY_DOCS`** from **`REPO_ROOT_SYNC_IDS`** + `repos.toml` `sync`; hub root is the single source of truth. Do **not** invent a fake `AGENT_FOLDERS` root.

**Charter adds or renames a standard `aiscr-*` workflow:** complete **Cross-tool entry-point anti-drift** in `aiscr-ecosystem-governance.md` for **every** assistant integration listed there that maps to committed **`aiscr-*`** skills for this hub (matrix is authoritative for which roots apply).

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The matrix row is enough to call this done" | Run the **mechanical closure** commands; fix every reported `parity.*` / matrix / strict sync failure. |
| "I'll skip reading official docs — the matrix tells me the filenames" | Read vendor official docs **before** matrix/TOML edits and before authoring repo-local config; match official schemas. |
| "I'll run `sync_agent_configs.py apply` after the dry-run — the dry-run looked clean" | Explicit user approval is required before every apply, even after a clean dry-run. |
| "I'll register a new `aiscr-*` workflow without charter approval" | Phase 6 only when the **planning session** explicitly puts a new or renamed **`aiscr-*`** slug in scope. |
| "I'll run `generate_workflow_skills.py` with a short `--tools` list to save time" | Use **default `--tools`** for hub registry maintenance unless the charter documents a deliberate omission; dropping a tool skips that product’s committed **`aiscr-*`** mirrors. |
| "Repo root has no `<vendor>/skills` so workflow skills are missing" | Check **matrix hub path** under **`.agents/local_configs/<repo>/…`**; many roots are gitignored at repo root. |
| "Empty `hub_committed_path` is fine — the matrix table already says 'same'" | Non-empty path is required wherever the hub **commits** the artefact; empty skips the validator for that **(product, asset_type)** row. |

## Verification before completion

**Documentation and policy**

- [ ] `agent_tool_feature_matrix.md` — vendor column(s) correct; **Legend** hub paths match what generators and parity enforce.
- [ ] `mandatory_vendor_doc_urls.toml` — URLs and paths honest; docs read **before** committing vendor files.

**Sync registry**

- [ ] **`AGENT_FOLDERS` vendor:** `repos.toml` `sync` includes intended roots.
- [ ] **Repo-root vendor:** `REPO_ROOT_HUB_ENTRY_DOCS` vs `REPO_ROOT_SYNC_IDS` + `repos.toml` sync recipes / overrides; no entry docs under `local_configs`; no spurious `AGENT_FOLDERS` row.

**Mechanical closure (run from repo root, `.venv` on)**

- [ ] `python .agents/scripts/validate_agent_tool_feature_matrix.py` (add `--strict-url-check` before release merge if URLs changed).
- [ ] `python .agents/scripts/validate_matrix_local_configs_cells.py` (TOML × **`local_configs`** per **`sync`**; **`parity.matrix-local-configs-vendor-cells`**).
- [ ] `python .agents/scripts/report_local_configs_sync_matrix.py --strict`
- [ ] `python .agents/scripts/validate_tool_parity.py` (and `--strict` if branch policy requires it).
- [ ] If **`repos.toml` `sync`** tokens for tool folders changed: `python .agents/scripts/validate_assistant_runtime_gitignore.py`
- [ ] If **canonical governance fragments** or ecosystem stem changed: `python .agents/scripts/generate_governance_rules.py`
- [ ] After canonical **`governance_rules`** or the governance stem registry changes: `python .agents/scripts/generate_governance_rules.py` (Cursor/Claude/Copilot/Codex plus **`.gemini/context/`** and Gemini `settings.json` mirrors).
- [ ] If **registry slugs or canonical `workflow_skills/*.md` or `canonical_workflows_context.toml` changed:** `python .agents/scripts/generate_workflow_skills.py` (**default `--tools`**, or a documented `--slug` pass followed by a full regen before merge).

**Charter — cross-tool workflow (Phase 6 only)**

- [ ] Full cross-tool checklist in `aiscr-ecosystem-governance.md` for **each product row** the charter/matrix puts in scope (tables, mapping, Copilot digest when committed).

**Apply**

- [ ] `sync_agent_configs.py` / orchestrator **dry-run** reviewed; **no apply** without explicit user approval.

**Registry fallback:** Load openspec/specs/agent-vendor-onboarding/spec.md first for the durable contract; then agent_tool_feature_matrix.md, mandatory_vendor_doc_urls.toml, sync_policy.py; follow agent-vendor-introduction.plan.md as the phased execution workflow; no sync apply without approval.

## Governance

- Scope follows the **session charter** in the approved plan Options—not a fixed Mode switch.
- No sync **apply** without approval; `generate_workflow_skills.py` **dry-run** first when regenerating skills at scale.
- Canonical source: this file; regenerate vendor **`SKILL.md`** trees with `generate_workflow_skills.py` after edits.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow