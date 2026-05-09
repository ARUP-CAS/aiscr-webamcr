---
name: aiscr-agent-vendor-introduction
description: 'Introduce or remediate an agent-tool vendor in the AIS CR hub: matrix/TOML,
  sync policy (AGENT_FOLDERS and repo-root REPO_ROOT_SYNC_IDS), parity, direct bundles;
  optional cross-tool aiscr-* workflow registration when the session charter requires
  it.'
disable-model-invocation: true
user-invocable: true
argument-hint: <vendor>
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-agent-vendor-introduction.md -->

# aiscr-agent-vendor-introduction

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-agent-vendor-introduction/SKILL.md`](.cursor/skills/aiscr-agent-vendor-introduction/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.claude/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Introduce or remediate an agent-tool vendor in the AIS CR hub: matrix/TOML, sync policy (AGENT_FOLDERS and repo-root REPO_ROOT_SYNC_IDS), parity, direct bundles; optional cross-tool aiscr-* workflow registration when the session charter requires it.

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

Load [`.cursor/skills/aiscr-agent-vendor-introduction/SKILL.md`](.cursor/skills/aiscr-agent-vendor-introduction/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/agent-vendor-introduction.plan.md`

**Registry fallback:** Load openspec/specs/agent-vendor-onboarding/spec.md first for the durable contract; then agent_tool_feature_matrix.md, mandatory_vendor_doc_urls.toml, sync_policy.py; follow agent-vendor-introduction.plan.md as the phased execution workflow; no sync apply without approval.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
