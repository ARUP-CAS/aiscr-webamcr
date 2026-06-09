---
name: aiscr-api-doc-alignment
description: Align API specs and documentation in API-focused repos. Use when the
  user asks to align OpenAPI specs with docs, or define API doc governance.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-api-doc-alignment.md -->

# aiscr-api-doc-alignment

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-api-doc-alignment/SKILL.md`](.cursor/skills/aiscr-api-doc-alignment/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.gemini/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Align API specs and documentation in API-focused repos. Use when the user asks to align OpenAPI specs with docs, or define API doc governance.

Align API specs and documentation in API-focused repositories.

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

Load [`.cursor/skills/aiscr-api-doc-alignment/SKILL.md`](.cursor/skills/aiscr-api-doc-alignment/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/api-doc-alignment.plan.md`

**Registry fallback:** Load openspec/specs/api-specification-sync/spec.md first for the durable behavioral contract; load `.agents/canonical_configs/references/ecosystem_map.md` for API repo list; inventory OpenAPI specs and docs per plan Step 1; map sources of truth per Step 2; follow api-doc-alignment.plan.md for alignment workflow and governance documentation.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
