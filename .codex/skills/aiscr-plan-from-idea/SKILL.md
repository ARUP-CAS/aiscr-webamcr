---
name: aiscr-plan-from-idea
description: Promote one OpenSpec backlog proposal into the governance-driven planning
  flow by running a governed structured exploration pass before the formal planning
  phase, then produce OpenSpec artifacts (proposal, specs, design, tasks), refresh
  backlog overview, and hard-stop before implementation unless the user explicitly
  starts a separate apply/implementation workflow afterward.
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-plan-from-idea.md -->

# aiscr-plan-from-idea

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-plan-from-idea/SKILL.md`](.cursor/skills/aiscr-plan-from-idea/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.codex/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Promote one OpenSpec backlog proposal into the governance-driven planning flow by running a governed structured exploration pass before the formal planning phase, then produce OpenSpec artifacts (proposal, specs, design, tasks), refresh backlog overview, and hard-stop before implementation unless the user explicitly starts a separate apply/implementation workflow afterward.

Turn one specific OpenSpec backlog proposal into a formal AIS CR planning flow
that promotes it into a governance-driven OpenSpec change using concrete CLI
commands, keeps the repo's planning-first approval gate, and stops once the
full OpenSpec change is ready for implementation.

**Workflow boundary (read first):** In scope — a governed structured
exploration pass, the formal planning conversation, human approval, promotion
of the same slug to governance-driven `proposal.md` / `specs/` / `design.md` /
`tasks.md`, `openspec status`, and `generate_backlog_overview.py`. Out of
scope for this skill - implementing `tasks.md`, editing application or
non-change product files, running `/opsx:apply` / `openspec-apply-change`, or
continuing "because the change is ready." Those require an **explicit** separate
user request or a different workflow after this skill ends. Earlier approval
for planning or promotion does not carry forward to that later boundary.

## Phase awareness

This skill operates at the **explore/plan boundary** of the OpenSpec lifecycle.
It creates or promotes OpenSpec change artifacts with AIS CR governance gates.
It begins with a governed structured exploration pass that clarifies problem
framing, likely impacts, trade-offs, open questions, and readiness signals
before the formal planning phase.
After completing its workflow, it hands off to `/opsx:*` CLI seeds for execution.
It must not initiate implementation or cross into the apply phase.
Crossing the later `plan -> implement` boundary requires fresh
post-promotion approval specific to the promoted change; earlier approval for
planning or promotion does not carry forward.
Check for an existing OpenSpec change for this slug before promoting a new one.

## Workflow routing

Load [`.cursor/skills/aiscr-plan-from-idea/SKILL.md`](.cursor/skills/aiscr-plan-from-idea/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

_No backing plan file;_ follow fallback and governance.

**Registry fallback:** Read `openspec/changes/<slug>/proposal.md` from the named backlog proposal first; run one governed structured exploration pass; run one formal planning phase using that exploration output; wait for approval; promote the same slug into a governance-driven OpenSpec change; refresh `.agents/backlog-overview.md`; stop before implementation and offer `/opsx:continue <slug>` or `/opsx:apply <slug>` based on readiness.

## Valid next steps

- `/opsx:continue <slug>` -- continue refining the promoted change's artifacts when more decision capture is needed
- `/opsx:apply <slug>` -- start implementing the tasks in the promoted change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive a completed change after implementation
- `/aiscr-note-idea <slug>` -- capture a related idea as a new backlog item
