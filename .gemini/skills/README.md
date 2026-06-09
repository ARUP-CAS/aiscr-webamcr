# Dovednosti Gemini CLI

([English](README_en.md))

```text
Language entry scope: Agents MUST use README_en.md for operational instructions. This README.md is human-facing Czech only; align with the English twin when meaning changes.
```

Tato složka je commitovaný povrch workflow dovedností Gemini pro `aiscr-management`.

`python .agents/scripts/generate_workflow_skills.py` zapisuje standardní stromy `aiscr-*` / `SKILL.md` sem do kořene management hubu. Vlastní zrcadlo `.agents/local_configs/aiscr-management/` bylo odstraněno.

V sibling `local_configs/<repo>/.gemini/skills/` obvykle zůstává jen README pár, pokud manifest daného repa výslovně nepovolí `ecosystem-sibling-workflow-surface`.

Adresář také plní kontroly Gemini `skills` `hub_committed_path` v `mandatory_vendor_doc_urls.toml` a `validate_agent_tool_feature_matrix.py`. Viz `agent_tool_feature_matrix.md`.

## Související zdroje

- [Gemini CLI — Skills](https://geminicli.com/docs/cli/skills/)
- `python .agents/scripts/generate_workflow_skills.py`
- **`.agents/canonical_configs/references/agent_tool_feature_matrix.md`**
