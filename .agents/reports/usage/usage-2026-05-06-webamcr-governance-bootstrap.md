# Usage Log - webamcr-governance-bootstrap

- **Date:** 2026-05-06
- **Agent/runtime:** Codex in the OpenAI API coding environment
- **Model/backend:** backend model id not exposed by the runtime
- **Subagents used:** none
- **MCP servers used:** none
- **Target repository:** `aiscr-webamcr`
- **Target branch:** `DN-agents-setup-review`
- **Hub baseline revision:** `5e329c8e15201be35353cd893f79cd612a3722e0`
- **OpenSpec change:** `webamcr-governance-bootstrap`
- **Bootstrap modes:** `bootstrap-mode-align` + `bootstrap-mode-introduce-openspec`
- **Packages executed:** `pkg.introduce-openspec.any`, `pkg.align.any`, `pkg.propagation-and-sync` dry-run followed by approved target-scoped apply, `pkg.validation`, `pkg.feedback-and-usage-log`

## Summary

Continued the approved governance-bootstrap run after the previous Claude
session stopped at the proposal artifact. Adopted the built-in OpenSpec
`spec-driven` schema, added the first `agent-governance` OpenSpec contract,
created target bootstrap metadata, and updated stale root-governance language
that still described `.cursor/` and `.claude/` as gitignored local-only folders.

The initial run deliberately stopped at hub configuration sync dry-run. After
maintainer review, the follow-up approved target-scoped apply populated or
refreshed `.cursor/`, `.claude/`, `.codex/`, `.gemini/`, `.clinerules/`, and
`.qodo/` from `aiscr-management/.agents/local_configs/aiscr-webamcr/`, with all
other registered siblings excluded.

A follow-up inspection found the lower-level sync command had applied only the
selected baseline children and not the specialized asset groups from
`webclass-ui-workflows`. The missing effective-sync-surface assets were then
applied using the orchestrator's `apply_asset_operations` function for
`aiscr-webamcr` only. After that corrective apply, source-vs-target file-set
counts matched exactly for `.cursor`, `.claude`, `.codex`, `.gemini`,
`.clinerules`, and `.qodo`.

## Impacted Paths

- `.gitignore` - user-prepared change removing old agent-folder ignore lines
- `package.json`
- `package-lock.json`
- `AGENTS.md`
- `CLAUDE.md`
- `.agents/local_overrides.toml`
- `.agents/reports/usage/usage-2026-05-06-webamcr-governance-bootstrap.md`
- `.agents/canonical_configs/references/`
- `.cursor/`, `.claude/`, `.codex/`, `.gemini/`, `.clinerules/`, `.qodo/`
- `openspec/config.yaml`
- `openspec/changes/webamcr-governance-bootstrap/`

## Verification

- `npx openspec validate --all` - passed (`change/webamcr-governance-bootstrap`)
- `npx openspec validate --specs --strict` - returned "No items found to validate" because no main specs exist yet; the change validation covers the active delta
- Hub dry-run, target-scoped by excluding other registered siblings:
  `.venv\Scripts\python.exe .agents/scripts/sync_agent_configs.py ApplyLocalConfigsToRepos --local-configs-path .agents/local_configs --repos-root .. --dry-run --exclude aiscr-digiarchiv-2 aiscr-webamcr-help aiscr-api-home aiscr-oao aiscr-amcr-home aiscr-home aiscr-rdf-vocabs`
- Dry-run result for `aiscr-webamcr`: `.cursor`, `.claude`, `.codex`,
  `.gemini`, and `.clinerules` are `NEW-M`; `.qodo` has content drift because
  the target lacks the hub README pair.
- Approved target-scoped apply:
  `.venv\Scripts\python.exe .agents/scripts/sync_agent_configs.py ApplyLocalConfigsToRepos --local-configs-path .agents/local_configs --repos-root .. --exclude aiscr-digiarchiv-2 aiscr-webamcr-help aiscr-api-home aiscr-oao aiscr-amcr-home aiscr-home aiscr-rdf-vocabs --no-confirm`
- Corrective specialized-asset apply for `aiscr-webamcr` only via
  `orchestrate_local_agent_sync.apply_asset_operations`.
- Source-vs-target vendor file-set parity after correction:
  `.cursor` 67/67, `.claude` 71/71, `.codex` 62/62, `.gemini` 115/115,
  `.clinerules` 41/41, `.qodo` 2/2.

## Follow-Up

Review and commit the resulting tracked vendor surfaces with the rest of the
bootstrap change. No sibling repo other than `aiscr-webamcr` was modified by the
apply.
