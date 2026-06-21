# Claude Code configuration

([Czech](README.md))

```text
Language entry scope: This README_en.md is the sole operational instruction source for agents. README.md is the Czech human-facing twin; update both together when operational behaviour changes.
```

This directory is the **committed hub-root Claude Code delivery surface** for the AIS CR management hub. It is the single source of truth for the assets it carries (rules, skills, agents, hooks, settings). Sibling repositories receive selected assets through direct-bundle sync resolved from `.agents/sync/` policy via `orchestrate_local_agent_sync.py inspect → dry-run → apply --approve`. The historical `.agents/local_configs/<repo>/.claude/` payload-mirror layout has been retired and must not be recreated.

<!-- aiscr:stop-anchor -->
The load path below remains a supporting aid; the `Entry scope` and `Read First` sections stay normative.

```mermaid
flowchart TD
  scope["Stay in .claude/ first"]
  entry["Read CLAUDE.md and AGENTS.md"]
  routing["Use governance_by_tool.md and agent_tool_feature_matrix.md for topic routing"]
  workflows["Open .claude/skills/ for workflow entry points"]

  scope --> entry
  entry --> routing
  routing --> workflows
```

## Entry scope

- Stay in this `.claude/` tree and its direct pointers first.
- Do not open parallel `.cursor/`, `.codex/`, or `.gemini/` trees by default “just in case”.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.
- Use this English counterpart for operational reading; `README.md` remains the Czech primary pair.

## Read First

- `CLAUDE.md`
- `AGENTS.md`
- `.agents/canonical_configs/references/governance_by_tool.md`
- `.agents/canonical_configs/references/agent_tool_feature_matrix.md`

## Notes

- Local workflow entry points live in `.claude/skills/`.
- The legacy `commands/` surface keeps only a README pointer.
- Per-user exceptions belong in `settings.local.json`.

[Czech version](README.md)
