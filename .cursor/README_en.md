# Cursor configuration

([Czech](README.md))

```text
Language entry scope: This README_en.md is the sole operational instruction source for agents. README.md is the Czech human-facing twin; update both together when operational behaviour changes.
```

This directory is the **committed hub-root Cursor delivery surface** for the AIS CR management hub. It is the single source of truth for the assets it carries (rules, skills, agents, hooks). Sibling repositories receive selected assets through direct-bundle sync resolved from `.agents/sync/` policy via `orchestrate_local_agent_sync.py inspect → dry-run → apply --approve`. The historical `.agents/local_configs/<repo>/.cursor/` payload-mirror layout has been retired and must not be recreated.

<!-- aiscr:stop-anchor -->
The load path below remains a supporting aid; the `Entry scope` and `Read First` sections stay normative.

```mermaid
flowchart TD
  scope["Stay in .cursor/ first"]
  rules["Read AGENTS.md and .cursor/rules/"]
  routing["Use governance_by_tool.md and agent_tool_feature_matrix.md for topic routing"]
  workflows["Open .cursor/skills/ for workflow entry points"]

  scope --> rules
  rules --> routing
  routing --> workflows
```

## Entry scope

- Stay in this `.cursor/` tree and its direct pointers first.
- Do not open parallel `.claude/`, `.codex/`, or `.gemini/` trees without a clear reason.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.
- Use this English counterpart for operational reading; `README.md` remains the Czech primary pair.

## Read First

- `AGENTS.md`
- `.cursor/rules/`
- `.agents/canonical_configs/references/governance_by_tool.md`
- `.agents/canonical_configs/references/agent_tool_feature_matrix.md`

## Notes

- Workflow entry points live in `.cursor/skills/`.
- Long-form governance belongs in the canonical rule surfaces, not in this README.

[Czech version](README.md)
