# Subagenti Gemini CLI — `.gemini/agents/`

([English](README_en.md))

```text
Language entry scope: Agents MUST use README_en.md for operational instructions. This README.md is human-facing Czech only; align with the English twin when meaning changes.
```

**Vlastní subagenti** repozitáře: Markdown soubory s YAML frontmatter v **`.gemini/agents/*.md`** ([Creating custom subagents](https://geminicli.com/docs/core/subagents/)). **Vestavěné** subagenty CLI (`codebase_investigator`, `cli_help`, …) a globální přepisy: **`agents.overrides`** v **`settings.json`**.

**AIS CR hub:** Soubory **`aiscr-*`** generuje **`python .agents/scripts/generate_agent_definitions.py`** ze stejného SSOT jako **`.cursor/agents/`**, **`.claude/agents/`** a **`.codex/agents/`** (lze doplnit i ručně). Baseline synchronizace: **`repos.toml`** / **`sync_policy.py`**.

Oficiální dokumentace: [Subagents](https://geminicli.com/docs/core/subagents/). Mapa cest: **`agent_tool_feature_matrix.md`**, **`mandatory_vendor_doc_urls.toml`**.
