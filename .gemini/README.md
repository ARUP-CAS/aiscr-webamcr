# Kontext Gemini CLI

([English](README_en.md))

```text
Language entry scope: Agents MUST use README_en.md for operational instructions. This README.md is human-facing Czech only; align with the English twin when meaning changes.
```

Následující load path je podpůrná pomůcka; normativní popis toho, kde v tomto hubu leží Gemini surface, zůstává v odstavcích výše.

```mermaid
flowchart TD
  entry["Začni v kořenovém GEMINI.md"]
  task{"Jaký surface řešíš?"}
  cli["Použij .gemini/settings.json, context/, skills/ a agents/"]
  review["Použij .gemini/config.yaml a styleguide.md"]
  mapping["Mapování cest hledej v agent_tool_feature_matrix.md a mandatory_vendor_doc_urls.toml"]

  entry --> task
  task -->|CLI nebo project context| cli
  task -->|Code Assist review| review
  cli --> mapping
  review --> mapping
```

**`GEMINI.md`** v **kořeni repozitáře** je vstupní dokument pro Gemini (stejná role jako **`AGENTS.md`** / **`CLAUDE.md`**). **Není** pod **`.agents/local_configs/`** - je to **hub-root entry doc** (viz **`sync_policy.REPO_ROOT_HUB_ENTRY_DOCS`**).

Adresář **`.gemini/`** drží projektovou konfiguraci CLI a Code Assist (**`settings.json`**, hooky; **`config.yaml`** / **`styleguide.md`** pro PR review Code Assist; volitelně **`skills/`**, vlastní subagenty **`agents/*.md`**). Baseline je v **`.agents/local_configs/<repo>/.gemini/`** pro sync, i když mají **`.gemini/`** v **`.gitignore`**. U hubu **aiscr-management** je **`.gemini/`** v **kořeni repozitáře** a **`validate_tool_parity.py`** / **`validate_agent_tool_feature_matrix.py`** kontrolují `hub_committed_path` tam (vlastní zrcadlo **`local_configs/aiscr-management/`** bylo odstraněno). U **sibling** řádků v `local_configs` patří **`settings.json`**, **`config.yaml`** a **`styleguide.md`**; celé stromy **`.gemini/skills/aiscr-*`** jsou **jen na hubu**, pokud není zapnuté **`ecosystem-sibling-workflow-mirror`**. Audit: **`python .agents/scripts/validate_matrix_local_configs_cells.py`**.

Oficiální dokumentace: [Gemini CLI](https://geminicli.com/docs/), [Gemini Code Assist](https://developers.google.com/gemini-code-assist/docs/overview). Přehled cest a odkazů: **`agent_tool_feature_matrix.md`**, **`mandatory_vendor_doc_urls.toml`**.
