<!-- SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- delivery-version: b257a1a89279be5e17cda3c133aa77b8c4d2706c 2026-11-07T11:18:12+01:00 -->

# schemas – JSON Schema for workstation_safety

The schemas here validate selected JSON templates **before** [`setup_workstation_assistant_safety.py`](../../../../scripts/setup_workstation_assistant_safety.py) writes them.

| File | Validates |
| ---- | --------- |
| `claude_safety_snippet.schema.json` | `../claude_safety_snippet.json` |

The Codex template `../codex_user_config.toml` is checked via Python (`tomllib` plus required keys: `approval_policy` and top-level `sandbox_mode`), not JSON Schema in this folder.

When template fields change, update the matching schema and the script tests under `.agents/scripts/tests/`.
