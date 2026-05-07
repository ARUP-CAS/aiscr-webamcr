# Gemini CLI skills

([Czech](README.md))

```text
Language entry scope: This README_en.md is the sole operational instruction source for agents. README.md is the Czech human-facing twin; update both together when operational behaviour changes.
```

This directory is the committed Gemini workflow-skill surface for `aiscr-management`.

`python .agents/scripts/generate_workflow_skills.py` writes the standard `aiscr-*` `SKILL.md` trees here at the management hub repository root. The hub self-mirror under `.agents/local_configs/aiscr-management/` has been removed.

Sibling `local_configs/<repo>/.gemini/skills/` usually keep only the README pair unless the repo manifest opts into `ecosystem-sibling-workflow-surface`.

The directory also satisfies the Gemini `skills` `hub_committed_path` checks in `mandatory_vendor_doc_urls.toml` and `validate_agent_tool_feature_matrix.py`. See `agent_tool_feature_matrix.md`.

## Related sources

- [Gemini CLI — Skills](https://geminicli.com/docs/cli/skills/)
- `python .agents/scripts/generate_workflow_skills.py`
- **`.agents/canonical_configs/references/agent_tool_feature_matrix.md`**

[Czech version](README.md)
