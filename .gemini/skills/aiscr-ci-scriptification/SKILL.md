---
name: aiscr-ci-scriptification
description: Scriptify prompts/plans into reproducible scripts and run validation
  and hygiene in CI without agent calls. Use when the user asks to scriptify automation,
  run validation in CI without AI, replace agent steps with scripts, or design script-first
  CI.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-ci-scriptification.md -->

# aiscr-ci-scriptification

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-ci-scriptification/SKILL.md`](.cursor/skills/aiscr-ci-scriptification/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.gemini/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Scriptify prompts/plans into reproducible scripts and run validation and hygiene in CI without agent calls. Use when the user asks to scriptify automation, run validation in CI without AI, replace agent steps with scripts, or design script-first CI.

Evaluate which prompts, plans, or skills can be turned into reproducible scripts; define script-first CI steps that run validation and hygiene without agent calls.

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

Load [`.cursor/skills/aiscr-ci-scriptification/SKILL.md`](.cursor/skills/aiscr-ci-scriptification/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/ci-scriptification.plan.md`

**Registry fallback:** Load openspec/specs/ci-plan-scriptification/spec.md for requirements, architecture, and capability categories; browse current automation layout (prompts, plans, scripts, CI workflows); evaluate scriptifiable parts using the spec's four capability categories; define script-only steps for CI (validation, dry-run checks); follow ci-scriptification.plan.md for cleanup, documentation updates, and testing strategy.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
