## Context

`aiscr-webamcr` already has root governance (`AGENTS.md`, `CLAUDE.md`,
`CONTRIBUTING.md`, `CODEOWNERS`) and an existing `.agents/` review tree, but it
did not have an OpenSpec requirement surface. The repository also previously
treated `.cursor/`, `.claude/`, and `.codex/` as gitignored local tooling. Those
legacy vendor folders were removed, and the `.gitignore` entries were deleted so
hub-synchronized vendor surfaces can become tracked content.

The management hub already registers `aiscr-webamcr` in
`aiscr-management/.agents/local_configs/repos.toml` and holds the intended
baseline under `.agents/local_configs/aiscr-webamcr/`.

## Goals / Non-Goals

**Goals:**

- Introduce OpenSpec using the built-in `spec-driven` schema.
- Add a first durable contract for agent-governance alignment.
- Record bootstrap metadata in `.agents/local_overrides.toml`.
- Repair stale root-governance prose about gitignored vendor folders.
- Apply hub sync after a reviewed dry-run and explicit follow-up approval.

**Non-Goals:**

- Change Django application behavior.
- Modify hub `aiscr-management` files.
- Rework the existing `.agents/` review/audit tree.

## Decisions

### Use built-in `spec-driven` rather than hub `governance-driven`

The hub's `governance-driven` schema contains management-hub-specific context
and rules. `aiscr-webamcr` is an application repository, so the built-in
`spec-driven` schema is the better fit for a lightweight first adoption.

Alternative considered: copy the hub custom schema. Rejected because it would
pull hub-only references into a sibling web application.

### Keep vendor-surface population delegated to hub sync

The `.cursor/`, `.claude/`, `.codex/`, `.gemini/`, `.clinerules/`, and `.qodo/`
trees are materialized from the hub baseline after dry-run review and explicit
approval. The baseline children are applied through `sync_agent_configs.py`; the
specialized assets selected by the sync recipe are applied through the
orchestrator asset path logic so rules, skills, agents, and reference files are
also present.

Alternative considered: directly copy local_configs payloads into the target by
hand. Rejected because the synchronized assets should come through approved hub
sync code. The lower-level sync command alone is insufficient for full
effective-sync-surface rollout because it applies selected baseline children but
not specialized asset groups.

### Store alignment metadata locally

`.agents/local_overrides.toml` records the adopted schema, alignment date, and
hub revision. It is also the future place for explicit tracked-path overrides.

Alternative considered: document alignment only in OpenSpec artifacts. Rejected
because the bootstrap workflow expects target-side override metadata to be
machine-readable.

## Risks / Trade-offs

- **Risk:** OpenSpec adds a Node dev dependency to a repository whose package
  manifest otherwise manages frontend libraries.
  **Mitigation:** Keep the dependency pinned and expose narrow `openspec:*`
  scripts.
- **Risk:** Sync apply can overwrite local edits under vendor folders.
  **Mitigation:** Require dry-run review first and use target-scoped apply with
  other siblings excluded.
- **Risk:** Future sync apply could overwrite local edits under vendor folders.
  **Mitigation:** Require dry-run review and record intentional tracked drift in
  `.agents/local_overrides.toml`.

## Migration Plan

1. Add OpenSpec dependency and scripts.
2. Create the `openspec/` project config, change proposal, spec delta, design,
   and tasks.
3. Create `.agents/local_overrides.toml` bootstrap metadata.
4. Update stale `AGENTS.md` and `CLAUDE.md` vendor-folder guidance.
5. Run OpenSpec validation.
6. Run hub sync dry-run, obtain explicit approval, then run target-scoped sync
   apply with other siblings excluded.
7. Apply recipe-selected specialized assets so source and target vendor trees
   have matching file sets.

Rollback is straightforward: remove the new OpenSpec files and dependency
changes, restore the previous root-governance wording, and restore the removed
`.gitignore` entries if maintainers decide not to track vendor folders.

## Open Questions

- Whether the follow-up sync apply should be performed in this branch or in a
  separate branch after maintainers review the dry-run output.
