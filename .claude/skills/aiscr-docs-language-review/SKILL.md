---
name: aiscr-docs-language-review
description: Run language and typo review of repo docs; user-facing Czech, agent-facing
  English, README_en equivalents, report language split, GFM formatting. Use when
  the user asks to review docs language, fix typos, add README English versions, or
  align with GitHub Markdown.
disable-model-invocation: true
user-invocable: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-docs-language-review.md -->

# aiscr-docs-language-review

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-docs-language-review/SKILL.md`](.cursor/skills/aiscr-docs-language-review/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.claude/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Run language and typo review of repo docs; user-facing Czech, agent-facing English, README_en equivalents, report language split, GFM formatting. Use when the user asks to review docs language, fix typos, add README English versions, or align with GitHub Markdown.

Run a detailed language and typo review of all repository documentation: user-facing docs in Czech, agent-facing in English, README English equivalents, and GitHub-compatible Markdown formatting.

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

Load [`.cursor/skills/aiscr-docs-language-review/SKILL.md`](.cursor/skills/aiscr-docs-language-review/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/docs-language-review.plan.md`

**Registry fallback:** Load openspec/specs/docs-language-quality/spec.md first for the durable behavioral contract; run `python .agents/scripts/doc_discovery.py` to inventory docs; classify by audience (user-facing = Czech, agent-facing = English); define README English equivalent strategy; review language and typos per target language; add/update `README_en.md` files; align GitHub Flavored Markdown formatting; run `link_check.py`, `validate_plans.py`, PyMarkdown scan; follow docs-language-review.plan.md for execution workflow.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
