<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-port-workspace-safety-config.md -->

# aiscr-port-workspace-safety-config

Merge validated Cursor, Codex, and Claude safety templates into user app-level config; dry-run first, explicit confirmation; may pip-install jsonschema/tomli-w; optional --backup and --target-dir; not sync_agent_configs.

**Route**: Load [`.claude/skills/aiscr-port-workspace-safety-config/SKILL.md`](.claude/skills/aiscr-port-workspace-safety-config/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-port-workspace-safety-config/SKILL.md`](.cursor/skills/aiscr-port-workspace-safety-config/SKILL.md) when Cursor reader body is preferred.

`.agents/plans/port-workspace-safety-config.plan.md`
Load openspec/specs/workspace-safety-config/spec.md first for the durable behavioral contract; then run `.venv/Scripts/python.exe` `.agents/scripts/port_workspace_safety_config.py` (or `.venv/bin/python` on Unix) per `.agents/scripts/README.md` and `port-workspace-safety-config.plan.md` as the execution runbook; auto-installs missing `jsonschema`/`tomli-w` from `requirements-ci.txt` via `requirements_subset_install.py`; use `--backup` only if backups wanted; no sync without approval.
