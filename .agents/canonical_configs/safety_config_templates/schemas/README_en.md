# schemas – JSON Schema for safety_config_templates

([Czech](README.md))

```text
Language entry scope: This README_en.md is the sole operational instruction source for agents. README.md is the Czech human-facing twin; update both together when operational behaviour changes.
```

The schemas here validate selected JSON templates **before** [`port_workspace_safety_config.py`](../../../scripts/port_workspace_safety_config.py) writes them.

| File | Validates |
| ---- | --------- |
| `claude_safety_snippet.schema.json` | `../claude_safety_snippet.json` |

The Codex template `../codex_user_config.toml` is checked via Python (`tomllib` plus required keys: `approval_policy` and top-level `sandbox_mode`), not JSON Schema in this folder.

When template fields change, update the matching schema and the script tests under `.agents/scripts/tests/`.

[Czech version](README.md)
