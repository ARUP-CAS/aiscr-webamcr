---
name: aiscr-doc-hygiene-audit
description: Run a documentation hygiene audit on this repository (or a target repo).
  Identifies duplication, drift, token inefficiency, and broken links. Use the aiscr-doc-auditor
  subagent for the analysis phase.
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-doc-hygiene-audit.md -->

# aiscr-doc-hygiene-audit

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-doc-hygiene-audit/SKILL.md`](.cursor/skills/aiscr-doc-hygiene-audit/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.codex/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Run a documentation hygiene audit on this repository (or a target repo). Identifies duplication, drift, token inefficiency, and broken links. Use the aiscr-doc-auditor subagent for the analysis phase.

Run a documentation hygiene audit and optionally apply safe, governance-aligned fixes.

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

Load [`.cursor/skills/aiscr-doc-hygiene-audit/SKILL.md`](.cursor/skills/aiscr-doc-hygiene-audit/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/doc-hygiene-audit.plan.md`

**Registry fallback:** Load openspec/specs/documentation-consistency/spec.md first for the durable behavioral contract; then run `python .agents/scripts/doc_discovery.py --output json` and `python .agents/scripts/link_check.py` for deterministic inventory; follow doc-hygiene-audit.plan.md for report-only or report+safe-fixes mode execution.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
