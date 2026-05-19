---
name: aiscr-sibling-branch-audit
description: Audit local branches across sibling AIS CR repositories; fetch and prune
  remote-tracking refs locally, list detached or unpublished branches, produce a per-repo
  report. Never changes the remote.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-sibling-branch-audit.md -->

# aiscr-sibling-branch-audit

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-sibling-branch-audit/SKILL.md`](.cursor/skills/aiscr-sibling-branch-audit/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.gemini/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Audit local branches across sibling AIS CR repositories; fetch and prune remote-tracking refs locally, list detached or unpublished branches, produce a per-repo report. Never changes the remote.

Run a safe, read-only audit of local branches in sibling AIS CR repositories: fetch and prune remote-tracking refs (local only), list unpublished or upstream-gone branches, and produce a report.

## Phase awareness

This skill operates within the **implement** phase of the OpenSpec lifecycle.
It is typically invoked as part of `/opsx:apply` or a standalone approved task.
Before executing, check for an active OpenSpec change or domain spec under
`openspec/`.
If one exists, load its context files as the primary authority.
If none exists for this domain, run `/opsx:propose`, stop for human approval,
and only continue after that change becomes the active context of the run.
It must not create new OpenSpec changes directly, promote backlog items, or
escalate scope beyond the approved task boundary.

## Workflow routing

Load [`.cursor/skills/aiscr-sibling-branch-audit/SKILL.md`](.cursor/skills/aiscr-sibling-branch-audit/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

_No backing plan file;_ follow fallback and governance.

**Registry fallback:** Load openspec/specs/sibling-branch-inventory/spec.md first for the durable behavioral contract; then run `python .agents/scripts/sibling_repos_branch_audit.py`; default report under `.agents/reports/local_sync_scratch/`; use `--stdout` or `--output` for custom location; never modifies remote.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
