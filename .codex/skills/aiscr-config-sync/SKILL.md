---
name: aiscr-config-sync
description: 'Master script-first sync orchestration: sibling branch audit pre-flight,
  repo-policy evaluation (matrix + peer alignment), inspect drift, populate local_configs,
  dry-run proposals, guarded sync apply against sibling repos.'
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-config-sync.md -->

# aiscr-config-sync

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-config-sync/SKILL.md`](.cursor/skills/aiscr-config-sync/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.codex/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Master script-first sync orchestration: sibling branch audit pre-flight, repo-policy evaluation (matrix + peer alignment), inspect drift, populate local_configs, dry-run proposals, guarded sync apply against sibling repos.

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

## Workflow routing

Load [`.cursor/skills/aiscr-config-sync/SKILL.md`](.cursor/skills/aiscr-config-sync/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/config-sync.plan.md`

**Registry fallback:** Load openspec/specs/agent-config-distribution/spec.md first for the durable contract; then run sibling_repos_branch_audit.py pre-flight, report_local_configs_sync_matrix.py for repo-policy checks, and follow config-sync.plan.md as the script-first execution runbook (human-approved apply only).

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
