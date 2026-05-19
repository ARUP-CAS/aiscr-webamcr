---
name: aiscr-security-ai-usage
description: Apply and validate security- and privacy-aware AI usage rules. Use when
  the user asks to add AI usage rules, validate security/privacy for AI, or harden
  AI usage governance.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-security-ai-usage.md -->

# aiscr-security-ai-usage

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-security-ai-usage/SKILL.md`](.cursor/skills/aiscr-security-ai-usage/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.gemini/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Apply and validate security- and privacy-aware AI usage rules. Use when the user asks to add AI usage rules, validate security/privacy for AI, or harden AI usage governance.

Apply and validate security- and privacy-aware AI usage rules across AIS CR repositories.

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

Load [`.cursor/skills/aiscr-security-ai-usage/SKILL.md`](.cursor/skills/aiscr-security-ai-usage/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/security-ai-usage.plan.md`

**Registry fallback:** Load openspec/specs/security-privacy-ai-usage/spec.md first for the durable behavioral contract; identify sensitive data surfaces in code, configs, prompts, and logs; review existing AI usage rules in `AGENTS.md`, `CLAUDE.md`; define cross-repo principles for what can/cannot be sent to AI systems; update governance docs and prompts; validate compliance across repositories; follow security-ai-usage.plan.md for execution workflow.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
