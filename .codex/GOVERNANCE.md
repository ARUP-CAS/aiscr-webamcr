# Codex — governance pointers (read these; do not duplicate)

- `CODEX.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md` (repo root)
- `.agents/canonical_configs/references/governance_by_tool.md` → open `.cursor/rules/*.mdc` by topic
- `.agents/canonical_configs/references/agent_tool_feature_matrix.md`, `mandatory_vendor_doc_urls.toml`
- Other tool roots (when in `repos.toml`): `.claude/` (`CLAUDE.md`), `.gemini/` (`GEMINI.md`, `.gemini/context/`); sync like this tree — see `repos.toml`, `AGENTS.md`.
- Operating default for this repo: stay inside the configured sandbox and use the repo virtualenv when present unless the user explicitly says otherwise or an exception is necessary and approved.
