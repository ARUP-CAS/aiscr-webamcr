<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-sibling-branch-audit.md -->

# aiscr-sibling-branch-audit

Audit local branches across sibling AIS CR repositories; fetch and prune remote-tracking refs locally, list detached or unpublished branches, produce a per-repo report. Never changes the remote.

**Route**: Load [`.claude/skills/aiscr-sibling-branch-audit/SKILL.md`](.claude/skills/aiscr-sibling-branch-audit/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-sibling-branch-audit/SKILL.md`](.cursor/skills/aiscr-sibling-branch-audit/SKILL.md) when Cursor reader body is preferred.

_No backing plan file;_ follow fallback and governance.
Load openspec/specs/sibling-branch-inventory/spec.md first for the durable behavioral contract; then run `python .agents/scripts/sibling_repos_branch_audit.py`; default report under `.agents/reports/local_sync_scratch/`; use `--stdout` or `--output` for custom location; never modifies remote.
