---
name: aiscr-hooks-governance
description: Review and harden AI-related automation and hooks in a repo. Use when
  the user asks to harden hooks, review automation, or tighten AI-related tooling.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-hooks-governance.md -->

# aiscr-hooks-governance

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

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

## Context to load first

1. `openspec/specs/ai-automation-governance/spec.md` — behavioral requirements and governance contracts
2. `AGENTS.md` — governance and scope
3. `.agents/README.md` — structure of `.agents/`
4. `.agents/canonical_configs/references/automation_recommendations.md` — current automation recommendations
5. `.agents/canonical_configs/references/plugin_enablement_and_fallback.md` — plugin and fallback matrix
6. `.agents/plans/hooks-governance.plan.md` — execution procedures and operator runbook

## Steps

1. Ask the user: target repo path, scope (hooks only, skills only, or all automation).
2. Inventory existing automation and hooks (PreToolUse, PostToolUse, etc.) in the target repo.
3. Compare with governance docs (`AGENTS.md`, `CONTRIBUTING.md`, and the relevant assistant entry doc if present) and `automation_recommendations.md`.
4. Identify risky, redundant, or non-compliant automation; classify as Critical / Important / Optional.
5. Design and propose hardening changes; present findings before applying anything.
6. Apply approved changes; validate hook behaviour (e.g. trigger a test run).

## Iron Law

**IRON LAW:** `NEVER APPLY HOOK CHANGES WITHOUT FIRST PRESENTING ALL FINDINGS. PRESENT THE COMPLETE FINDINGS LIST FIRST; APPLY ONLY AFTER EXPLICIT USER CONFIRMATION.`

No exceptions. Presenting findings is always before applying; there is no shortcut path.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The fix is obvious — I'll apply it before presenting the full findings" | Present the complete findings list first; apply nothing until the user confirms. |
| "The hook exits 0 so it's compliant" | Verify all four portability requirements: portable (Python 3 or POSIX shell), non-blocking (exit 0), agent-agnostic, concurrency-safe; exit 0 alone is not sufficient. |
| "The user asked me to harden hooks — I'll apply changes directly to the sibling repo" | State the branch per target repo and obtain explicit user confirmation before applying any change to a sibling repo. |

## Verification before completion

Before claiming this workflow complete:

- [ ] All hooks in the target repo verified as: portable (Python 3 or POSIX shell), non-blocking (exit 0), agent-agnostic, concurrency-safe (no shared-state writes).
- [ ] Findings presented to user before applying any changes.
- [ ] Approved changes applied and validated (test trigger or `run_validation_all.py`).
- [ ] Branch stated per target repo and user confirmed before applying changes.
- [ ] `automation_recommendations.md` updated if new hook patterns were identified.

## Plan and workflow

`.agents/plans/hooks-governance.plan.md`

**Registry fallback:** Load openspec/specs/ai-automation-governance/spec.md first for the durable behavioral contract; choose Mode A (introduce new hooks) or Mode B (harden existing hooks); load `AGENTS.md`, `CLAUDE.md`, and `automation_recommendations.md` for governance context; inventory existing hooks, MCP servers, and skills; follow hooks-governance.plan.md for hardening workflow and validation.

## Governance

- Do **not** run high-impact scripts (`sync_agent_configs.py`) unless the user explicitly asks.
- Present findings first; apply changes only after user confirmation.
- When target is another repo, state the branch and obtain user confirmation before applying.
- Requirement authority: `openspec/specs/ai-automation-governance/spec.md`
- Execution runbook: `.agents/plans/hooks-governance.plan.md`

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow