## 1. OpenSpec Setup

- [x] 1.1 Add `@fission-ai/openspec` and `openspec:*` npm scripts.
- [x] 1.2 Initialize `openspec/` with the `spec-driven` schema.
- [x] 1.3 Create the `webamcr-governance-bootstrap` proposal.
- [x] 1.4 Create the `agent-governance` spec delta.
- [x] 1.5 Create design notes for the bootstrap approach.

## 2. Governance Alignment

- [x] 2.1 Create `.agents/local_overrides.toml` with bootstrap metadata.
- [x] 2.2 Update `AGENTS.md` to describe tracked hub-synchronized vendor surfaces.
- [x] 2.3 Update `CLAUDE.md` to remove the stale "repo does not commit `.cursor/` or `.claude/`" claim.
- [x] 2.4 Keep vendor-surface apply gated behind reviewed dry-run output.
- [x] 2.5 Apply the approved target-scoped hub sync for `aiscr-webamcr`.
- [x] 2.6 Apply missing specialized assets selected by the `webclass-ui-workflows` sync recipe.

## 3. Verification

- [x] 3.1 Run `npx openspec validate --all`.
- [x] 3.2 Run hub `sync_agent_configs.py ApplyLocalConfigsToRepos` in dry-run mode and review expected vendor-surface writes.
- [x] 3.3 Re-run validation after the approved sync apply.
- [x] 3.4 Confirm target git status contains only expected bootstrap files, synced vendor surfaces, and user-approved `.gitignore` changes.
- [x] 3.5 Verify source-vs-target vendor file sets match for `.cursor`, `.claude`, `.codex`, `.gemini`, `.clinerules`, and `.qodo`.
- [x] 3.6 Record usage-log close-out for the governance bootstrap session.
