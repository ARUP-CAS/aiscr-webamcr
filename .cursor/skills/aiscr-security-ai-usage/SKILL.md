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
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

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

## Context to load first

1. `openspec/specs/security-privacy-ai-usage/spec.md` — behavioral requirements and architecture
2. `AGENTS.md` — governance, sensitive data surfaces, and scope
3. The current assistant entry doc for the tool in use (`CLAUDE.md`, `CODEX.md`, or `GEMINI.md`) — only if that surface adds extra AI-usage guidance beyond `AGENTS.md`
4. `.agents/README.md` — structure of `.agents/`
5. `.agents/plans/security-ai-usage.plan.md` — execution procedures

## Steps

1. Ask the user: target repo path, description of sensitive data surfaces (PII, tokens, internal URLs, etc.).
2. Identify all surfaces in the target repo where sensitive data might reach AI prompts or logs.
3. Review current AI usage rules in governance docs (`AGENTS.md`, the current assistant entry doc if relevant, and the canonical/shared rule files).
4. Define or update AI usage principles: what to redact, what placeholders to use, what is never permitted.
5. Update governance docs and prompts with clear AI usage rules.
6. Produce a checklist or report confirming adherence; flag any remaining gaps.

## Iron Law

**IRON LAW:** `NEVER APPLY SECURITY OR PRIVACY RULES TO A SIBLING REPO WITHOUT A PER-REPO REVIEW OF EXISTING CONFIG AND EXPLICIT USER APPROVAL FOR THAT SPECIFIC REPO.`

No exceptions. Security rules are not universally portable — each repo has different sensitive surfaces.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The same rules apply to all repos" | Review each repo's existing governance docs and sensitive surfaces before applying. |
| "I'll propagate this to sibling repos as part of the workflow" | State branch per target repo; get explicit per-repo confirmation. |
| "Using placeholders is good enough" | Verify no real PII, tokens, or internal URLs appear anywhere in examples or prompts. |

## Verification before completion

Before claiming this workflow complete, confirm:

- [ ] Per-repo review of existing governance docs completed for each target repo.
- [ ] Branch stated per target repo and user confirmed before applying changes.
- [ ] Checklist or report produced confirming adherence; gaps flagged.
- [ ] No real PII, tokens, or production URLs in any generated content.

## Plan and workflow

`.agents/plans/security-ai-usage.plan.md`

**Registry fallback:** Load openspec/specs/security-privacy-ai-usage/spec.md first for the durable behavioral contract; identify sensitive data surfaces in code, configs, prompts, and logs; review existing AI usage rules in `AGENTS.md`, `CLAUDE.md`; define cross-repo principles for what can/cannot be sent to AI systems; update governance docs and prompts; validate compliance across repositories; follow security-ai-usage.plan.md for execution workflow.

## Governance

- Do **not** run high-impact scripts unless the user explicitly asks.
- When target is another repo, state the branch and obtain user confirmation before applying.
- Never include real PII, tokens, or production URLs in examples — use placeholders.
- Full workflow: `.agents/plans/security-ai-usage.plan.md`

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow