---
name: aiscr-release-notes
description: Generate semantic, issue/PR-aligned release notes for a target AIS CR
  repository. Stores output in .agents/reports/release-notes/. Optionally updates
  the GitHub release body (opt-in, requires user approval).
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-release-notes.md -->

# aiscr-release-notes

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-release-notes/SKILL.md`](.cursor/skills/aiscr-release-notes/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.codex/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Generate semantic, issue/PR-aligned release notes for a target AIS CR repository. Stores output in .agents/reports/release-notes/. Optionally updates the GitHub release body (opt-in, requires user approval).

Generate semantic, issue/PR-aligned release notes for a target AIS CR repository in GitHub Wiki-compatible Markdown.

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

Load [`.cursor/skills/aiscr-release-notes/SKILL.md`](.cursor/skills/aiscr-release-notes/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/release-notes.plan.md`

**Registry fallback:** Load openspec/specs/release-documentation/spec.md first for the durable behavioral contract; gather target repo, mode (single release vs supplement missing vs date-range), and output scope; discover releases and `.github/release.yml` config; collect PRs, commits, and linked issues per release; group by semantic categories; write to `.agents/reports/release-notes/`; optionally push to GitHub release body with user approval and propagation scope (single/range/all).

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
