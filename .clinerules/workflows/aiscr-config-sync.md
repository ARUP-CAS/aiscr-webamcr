<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-config-sync.md -->

# aiscr-config-sync

Master script-first sync orchestration: sibling branch audit pre-flight, repo-policy evaluation (matrix + peer alignment), inspect drift, resolve direct bundle, dry-run proposals, guarded sync apply against sibling repos.

**Route**: Load [`.claude/skills/aiscr-config-sync/SKILL.md`](.claude/skills/aiscr-config-sync/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-config-sync/SKILL.md`](.cursor/skills/aiscr-config-sync/SKILL.md) when Cursor reader body is preferred.

`.agents/plans/config-sync.plan.md`
Load openspec/specs/agent-config-distribution/spec.md first for the durable contract; then run sibling_repos_branch_audit.py pre-flight, report_local_configs_sync_matrix.py for repo-policy checks, and follow config-sync.plan.md as the script-first execution runbook (human-approved apply only).
