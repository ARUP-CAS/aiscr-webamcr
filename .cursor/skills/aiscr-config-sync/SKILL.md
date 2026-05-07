---
name: aiscr-config-sync
description: 'Master script-first sync orchestration: sibling branch audit pre-flight,
  repo-policy evaluation (matrix + peer alignment), inspect drift, populate local_configs,
  dry-run proposals, guarded sync apply against sibling repos.'
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-config-sync.md -->

# aiscr-config-sync

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Preferred flow:

- **Requirement authority** - `openspec/specs/agent-config-distribution/spec.md`
- **Sibling branch audit** - read-only pre-flight (`sibling_repos_branch_audit.py`); fetch/prune local remote-tracking refs; report unpublished/upstream-gone branches
- **Repo-policy evaluation** - `report_local_configs_sync_matrix.py` (fix `ERROR` lines); optional peer compare of resolved recipe/override policy across repos sharing the same `type` in `repos.toml`; `--strict` before commit or after repo-policy/asset-registry edits; after **human-approved** policy changes, `populate --apply --repos <repo>` then matrix `--strict`
- **Inspect** - branch, drift, and parity audit
- **Populate** - scope-aware local_configs preparation
- **Dry-run** - proposed sync batch
- **Apply** - explicit guarded sync

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

For every standard workflow's prescribed context order, see `.agents/canonical_configs/references/canonical_workflows_context.md` (meta skill **`aiscr-canonical-workflows-context`**).

1. `openspec/specs/agent-config-distribution/spec.md` - durable behavioral requirements and sync architecture
2. `AGENTS.md` - governance, sync rules, and scope
3. `CONTRIBUTING.md` and `AGENTS.md` - commit/push rules, branch naming, and sibling-repo change rules
4. `.agents/scripts/README.md` - how the script-first sync workflow works
5. `.agents/canonical_configs/references/specialized_sync_assets.toml` - registered specialized sync assets
6. `.agents/plans/config-sync.plan.md` - execution procedures and operator runbook

## Script-first sync flow

1. Run `python .agents/scripts/sibling_repos_branch_audit.py --repos-root ..` (default report under `.agents/reports/local_sync_scratch/`; `--stdout` or `--output` optional). Skill: `aiscr-sibling-branch-audit`. **Inspect does not replace this:** it does not fetch or enumerate unpublished or upstream-gone branches.
1.5. **Pull all sibling repos** - run `git -C ../<repo> pull` for every repo in `repos.toml` on its current branch when the workflow calls for clearing behind-origin drift before inspect.
2. **Repo-policy evaluation (before inspect):** Run `python .agents/scripts/report_local_configs_sync_matrix.py`. Resolve any `ERROR` output (unknown `asset_groups` or `extra_asset_ids`, unknown `sync_recipe`, or asset disallowed for `repo_type` per `sync_policy` and `repos.toml`). Optionally compare repos that share the same `type` and intended recipe family (`sync_recipe`, `asset_groups`, `extra_asset_ids`, material `drop_children` or `include_children`) and align only for clear unintentional drift or documented tiers. Before commit or after `repos.toml` or `specialized_sync_assets.toml` edits: `python .agents/scripts/report_local_configs_sync_matrix.py --strict`. After approved policy edits: `python .agents/scripts/orchestrate_local_agent_sync.py populate --apply --repos <repo> --repos-root ..`, then matrix `--strict` again. If the sibling workflow-mirror group was removed, **`populate` does not delete** old `.cursor/skills`, `.claude/skills`, `.codex/skills`, `.gemini/skills`, or `.gemini/skills` under `local_configs` - delete those trees manually if still present, then `--strict` again (`config-sync.plan.md`).
2.1. **Agent matrix or TOML (when those files change):** If **`mandatory_vendor_doc_urls.toml`** or **`agent_tool_feature_matrix.md`** was edited in the same change set as sync work, run **`python .agents/scripts/validate_agent_tool_feature_matrix.py`** and **`python .agents/scripts/validate_matrix_local_configs_cells.py`** before claiming inspect or dry-run readiness. **`report_local_configs_sync_matrix.py`** does not replace those checks - it validates repo-policy and sync-policy alignment, not every **(product, asset_type)** **`hub_committed_path`** cell.
2.5. **Copilot instructions drift:** Run `python .agents/scripts/report_copilot_instructions_drift.py --repos-root ..`; review `DIFFERS` or `MISSING` entries and open PRs as needed. This is advisory only. `.github/copilot-instructions.md` is committed directly in sibling repos rather than managed through the specialized-assets sync layer.
3. Run `python .agents/scripts/orchestrate_local_agent_sync.py inspect`.
4. If needed, run `populate` to prepare `local_configs/<repo>` from an approved source repo.
5. Run `python .agents/scripts/orchestrate_local_agent_sync.py dry-run`.
6. Use `sync_cleanup_review.md` or `specialized_asset_review.md` when judgment is needed.
7. Only after explicit approval: run `python .agents/scripts/orchestrate_local_agent_sync.py apply --approve ...`. **Note:** the orchestrator hard-blocks apply when any repo has `content` or `same-name-diff` blockers. When human-approved content overwrites are intended and the management version is known-newer, use the lower-level engine directly: `python .agents/scripts/sync_agent_configs.py ApplyLocalConfigsToRepos --local-configs-path .agents/local_configs --repos-root .. --no-confirm`.

**Optional drift gate:** save `inspect --output json` under **`.agents/reports/local_sync_scratch/`** (UTF-8 without BOM; folder is gitignored) and run `python .agents/scripts/check_sibling_config_drift.py <file>`. See `config-sync.plan.md` for the execution-layer runbook; sibling branch audit reports use the same scratch folder by default.

Matching paths are not enough: same-name intended mirrors must stay byte-identical.

## Iron Law

**IRON LAW:** `NEVER APPLY SYNC (orchestrate apply OR sync_agent_configs.py) WITHOUT COMPLETING DRY-RUN FIRST AND RECEIVING EXPLICIT USER APPROVAL.`

No exceptions. This overrides any "it's a small change" or "the diff looks safe" reasoning.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The repo policy looks fine" | Run `report_local_configs_sync_matrix.py` and inspect drift first. |
| "I'll just apply directly" | Complete dry-run and show diff to user before any apply. |
| "This repo is easy - no confirm needed" | State branch per target repo and obtain explicit confirmation. |
| "Matrix TOML changed but sync matrix --strict is enough" | Also run **`validate_agent_tool_feature_matrix.py`** and **`validate_matrix_local_configs_cells.py`** when **`mandatory_vendor_doc_urls.toml`** or matrix prose changed. |

## Verification before completion

Before claiming this workflow complete, confirm:

- [ ] Dry-run was run and reviewed before any apply step.
- [ ] Explicit user approval received before any `apply` or `sync_agent_configs.py` invocation.
- [ ] Branch stated per target repo and user confirmed before applying changes.
- [ ] `report_local_configs_sync_matrix.py --strict` passes after any repo-policy changes.
- [ ] If **`mandatory_vendor_doc_urls.toml`** or **`agent_tool_feature_matrix.md`** changed: `validate_agent_tool_feature_matrix.py` and `validate_matrix_local_configs_cells.py` pass.

## Plan and workflow

`.agents/plans/config-sync.plan.md`

**Registry fallback:** Load openspec/specs/agent-config-distribution/spec.md first for the durable contract; then run sibling_repos_branch_audit.py pre-flight, report_local_configs_sync_matrix.py for repo-policy checks, and follow config-sync.plan.md as the script-first execution runbook (human-approved apply only).

## Governance

- Do **not** auto-apply cross-repo sync. Recurring unattended work is for branch audit, inspect, and dry-run only.
- Do **not** silently edit repo sync policy; maintainers approve before `populate --apply` or commit.
- Before applying to a sibling repo, state the branch per target repo and obtain user confirmation.
- Always mirror new or updated config-sync entry-point files immediately to local_configs after editing them.
- Execution runbook: `.agents/plans/config-sync.plan.md`

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow