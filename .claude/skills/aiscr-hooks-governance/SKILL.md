---
name: aiscr-hooks-governance
description: Review and harden AI-related automation and hooks in a repo. Use when
  the user asks to harden hooks, review automation, or tighten AI-related tooling.
disable-model-invocation: true
user-invocable: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-hooks-governance.md -->

# aiscr-hooks-governance

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-hooks-governance/SKILL.md`](.cursor/skills/aiscr-hooks-governance/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.claude/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Review and harden AI-related automation and hooks in a repo. Use when the user asks to harden hooks, review automation, or tighten AI-related tooling.

Review and harden AI-related automation and hooks in a repository.

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

Load [`.cursor/skills/aiscr-hooks-governance/SKILL.md`](.cursor/skills/aiscr-hooks-governance/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/hooks-governance.plan.md`

**Registry fallback:** Load openspec/specs/ai-automation-governance/spec.md first for the durable behavioral contract; choose Mode A (introduce new hooks) or Mode B (harden existing hooks); load `AGENTS.md`, `CLAUDE.md`, and `automation_recommendations.md` for governance context; inventory existing hooks, MCP servers, and skills; follow hooks-governance.plan.md for hardening workflow and validation.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
