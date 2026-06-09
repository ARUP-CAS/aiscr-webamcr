# Codex subagenti

([English](README_en.md))

```text
Language entry scope: Agents MUST use README_en.md for operational instructions. This README.md is human-facing Czech only; align with the English twin when meaning changes.
```

Tato složka drží volitelné soubory `.toml` pro [Codex subagenty](https://developers.openai.com/codex/subagents/). V hubu může být i prázdná; committed adresář ale držíme kvůli stabilnímu `hub_committed_path` v `mandatory_vendor_doc_urls.toml`.

## Co zde platí

- Subagenti doplňují `AGENTS.md`, `CODEX.md` a `.codex/GOVERNANCE.md`.
- Každý `aiscr-*.toml` má zůstat registry-driven a zarovnaný s kanonickými definicemi v `.agents/canonical_configs/agents/`.
- Mirror musí zůstat byte-identický s `.agents/local_configs/<repo>/.codex/agents/`.

## Související zdroje

- `.agents/canonical_configs/references/agent_tool_feature_matrix.md`
- `.agents/canonical_configs/references/subagent_vanilla_templates_and_mapping.md`
- `.agents/scripts/generate_agent_definitions.py`
