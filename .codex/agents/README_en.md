# Codex subagents

([Czech](README.md))

```text
Language entry scope: This README_en.md is the sole operational instruction source for agents. README.md is the Czech human-facing twin; update both together when operational behaviour changes.
```

This directory holds optional `.toml` files for [Codex subagents](https://developers.openai.com/codex/subagents/). The hub may still be empty; the committed directory exists so `hub_committed_path` in `mandatory_vendor_doc_urls.toml` remains stable.

## Rules Here

- Subagents supplement `AGENTS.md`, `CODEX.md`, and `.codex/GOVERNANCE.md`.
- Each `aiscr-*.toml` file must stay registry-driven and aligned with the canonical definitions under `.agents/canonical_configs/agents/`.
- The mirror must stay byte-identical with `.agents/local_configs/<repo>/.codex/agents/`.

## Related Sources

- `.agents/canonical_configs/references/agent_tool_feature_matrix.md`
- `.agents/canonical_configs/references/subagent_vanilla_templates_and_mapping.md`
- `.agents/scripts/generate_agent_definitions.py`

[Czech version](README.md)
