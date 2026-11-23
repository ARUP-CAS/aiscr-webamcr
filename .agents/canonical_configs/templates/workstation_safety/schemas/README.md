<!-- SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- delivery-version: 4ce7896238fe9996ccf1b0740cf3d6440d8d4d3f 2026-11-21T16:40:49+01:00 -->

# schemas – JSON Schema for workstation_safety

The schemas here validate selected JSON templates **before** [`setup_workstation_assistant_safety.py`](../../../../scripts/setup_workstation_assistant_safety.py) writes them.

| File | Validates |
| ---- | --------- |
| `claude_safety_snippet.schema.json` | `../claude_safety_snippet.json` |

The Codex template `../codex_user_config.toml` is checked via Python (`tomllib` plus required keys: `approval_policy` and top-level `sandbox_mode`), not JSON Schema in this folder.

When template fields change, update the matching schema and the script tests under `.agents/scripts/tests/`.
