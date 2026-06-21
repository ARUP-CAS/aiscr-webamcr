# schemas – JSON Schema pro safety_config_templates

([English](README_en.md))

```text
Language entry scope: Agents MUST use README_en.md for operational instructions. This README.md is human-facing Czech only; align with the English twin when meaning changes.
```

Schémata v této složce validují vybrané JSON šablony **před tím**, než je zapíše [`port_workspace_safety_config.py`](../../../scripts/port_workspace_safety_config.py).

| Soubor | Platí pro |
| ------ | --------- |
| `claude_safety_snippet.schema.json` | `../claude_safety_snippet.json` |

Codex šablona `../codex_user_config.toml` se kontroluje strukturou v Pythonu (`tomllib` + ověření povinných klíčů: `approval_policy` a top-level `sandbox_mode`), nikoli JSON Schema v této složce.

Při rozšíření polí v šablonách aktualizujte příslušné schéma a testy skriptů v `.agents/scripts/tests/`.
