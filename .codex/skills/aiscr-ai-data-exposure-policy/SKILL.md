---
name: aiscr-ai-data-exposure-policy
description: Apply and validate security- and privacy-aware AI usage rules. Use when
  the user asks to add AI usage rules, validate security/privacy for AI, or harden
  AI usage governance.
---

<!-- aiscr:compiled=aiscr-ai-data-exposure-policy -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.codex/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-ai-data-exposure-policy — AI data exposure and privacy governance

Apply and validate security- and privacy-aware AI usage rules across AIS CR repositories.

**When to use vs alternatives:** Use this workflow when the task is **what may enter AI prompts, logs, and governance surfaces** (PII, secrets, internal URLs, cross-repo principles). For merging **validated Cursor/Codex/Claude sandbox templates into the workstation** with `--list` / `--dry-run` and explicit write confirmation, use **`/aiscr-workstation-assistant-sandbox`** instead (`workspace-safety-config` spec; execution plan remains `port-workspace-safety-config.plan.md`).

## Phase awareness

This skill operates within the **implement** phase of the OpenSpec lifecycle.
It is typically invoked as part of `/opsx:apply` or a standalone approved task.
Before executing, check for an active OpenSpec change or domain spec under
`openspec/`.
If one exists, load its context files as the primary authority.
If none exists for this domain, run `/opsx:propose`, stop for human approval,
and only continue after that change becomes the active context of the run.
It must not create new **governance-driven** OpenSpec changes directly, promote backlog items, or
escalate scope beyond the approved task boundary, except for the backlog-only handoff governed by
the workflow contract summarized in this compiled skill after explicit per-run approval (see **Report-to-backlog handoff** below).

## Report-to-backlog handoff

For **remaining actionable gaps** after the approved run (checklist or report) with redaction preserved, follow the workflow contract summarized in this compiled skill (*AI data exposure gaps hand off with redaction*).

1. Summarize gaps for backlog candidates without copying sensitive evidence; cite the approved report path.
2. Ask for **explicit per-run** approval to emit backlog items.
3. If approved, draft the backlog candidate body inline — candidate slug, a one-line summary, `**Source report:**` (the approved report path), and `**Finding keys:**` — without copying sensitive evidence, then stop. Promotion into the management hub's backlog (creating the OpenSpec backlog change and refreshing the backlog overview) is a separate, explicit hub action by a maintainer; this workflow does not create hub changes or auto-invoke hub commands.
4. Record backlog slugs in the checklist or summary, or state why no backlog item was created.

Do not promote or implement spawned backlog inside this skill.

## Context to load first

1. the workflow contract summarized in this compiled skill — behavioral requirements and architecture
2. the workflow contract summarized in this compiled skill — backlog emission contract (when emitting follow-ups)
3. `AGENTS.md` — governance, sensitive data surfaces, and scope
4. The current assistant entry doc for the tool in use (`CLAUDE.md`, `CODEX.md`, or `GEMINI.md`) — only if that surface adds extra AI-usage guidance beyond `AGENTS.md`
5. `.agents/README.md` — structure of `.agents/`
6. the embedded execution plan below — execution procedures

## Steps

1. Ask the user: target repo path, description of sensitive data surfaces (PII, tokens, internal URLs, etc.).
2. Identify all surfaces in the target repo where sensitive data might reach AI prompts or logs.
3. Review current AI usage rules in governance docs (`AGENTS.md`, the current assistant entry doc if relevant, and the canonical/shared rule files).
4. Define or update AI usage principles: what to redact, what placeholders to use, what is never permitted.
5. Update governance docs and prompts with clear AI usage rules.
6. Produce a checklist or report confirming adherence; flag any remaining gaps.

<!-- aiscr:gen:id=guardrails -->
## Iron Law

**IRON LAW:** `NEVER APPLY SECURITY OR PRIVACY RULES TO A SIBLING REPO WITHOUT A PER-REPO REVIEW OF EXISTING CONFIG AND EXPLICIT USER APPROVAL FOR THAT SPECIFIC REPO.`

No exceptions. Security rules are not universally portable — each repo has different sensitive surfaces.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The same rules apply to all repos" | Review each repo's existing governance docs and sensitive surfaces before applying. |
| "I'll propagate this to sibling repos as part of the workflow" | State branch per target repo; get explicit per-repo confirmation. |
| "Using placeholders is good enough" | Verify no real PII, tokens, or internal URLs appear anywhere in examples or prompts. |
<!-- aiscr:endgen -->

## Verification before completion

Before claiming this workflow complete, confirm:

- [ ] Per-repo review of existing governance docs completed for each target repo.
- [ ] Branch stated per target repo and user confirmed before applying changes.
- [ ] Checklist or report produced confirming adherence; gaps flagged.
- [ ] No real PII, tokens, or production URLs in any generated content.

## Governance

- Do **not** run high-impact scripts unless the user explicitly asks.
- When target is another repo, state the branch and obtain user confirmation before applying.
- Never include real PII, tokens, or production URLs in examples — use placeholders.
- Full workflow: the embedded execution plan below

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- Read the identifiers and references stated in this workflow and follow the **Usage** section before loading a different workflow's context.

## Embedded execution plan

### Plan: Security- and Privacy-Aware AI Usage

> **OpenSpec migration:** Persistent behavioral requirements for this workflow now live in the workflow contract summarized in this compiled skill. This `.plan.md` file remains the reusable execution and governance layer for aiscr-management. See the identifiers and references stated in this workflow.

#### Context

AIS CR repositories may process or reference sensitive data (personal data, internal identifiers, infrastructure details).
This plan coordinates how AI systems should be used with such data across repositories, without replacing formal security policies.

#### Goals

- Make security and privacy considerations **explicit** in AI-related workflows.
- Reduce the risk of leaking sensitive data via prompts, logs, or generated artefacts.
- Align per‑repo practices with organisation‑level security expectations.

#### Scope and assumptions

- In scope:
  - AI prompts, hooks, scripts, and configs that may touch sensitive data.
  - Governance documents that mention AI usage.
- Out of scope:
  - Formal legal or regulatory compliance frameworks (handled outside Git).
  - Low‑level security controls (firewalls, network configuration).
- Assumptions:
  - Each repo already has or can add a minimal section on AI usage in its governance docs.

#### Execution approach

- Locate AI-related docs and prompts that might reference sensitive data.
- Trace where secrets, credentials, or PII are handled in code/config.
- Review proposed governance and prompt changes for clarity and completeness.

#### Steps

##### Step 1 — Identify sensitive data surfaces

- For each target repo (or category of repos):
  - Identify:
    - types of data handled (e.g. personal data, internal IDs, infrastructure URLs),
    - where such data is stored (databases, files, environment variables),
    - any existing guidance on handling this data.

##### Step 2 — Review current AI usage rules

- Read:
  - `AGENTS.md`, `CLAUDE.md`, and similar files in each repo.
  - Any internal guidance recorded in `.agents/` prompts or reports.
- Determine:
  - whether AI usage rules are present,
  - whether they are consistent across repos.

##### Step 3 — Define cross-repo AI usage principles

- Draft a short set of principles, for example:
  - Do not paste raw production data into prompts or examples.
  - Abstract or anonymise data when demonstrating behaviour.
  - Redact secrets, tokens, and passwords from any logs or AI context.
  - For internal infrastructure details, use placeholders unless explicitly needed and allowed.
- Confirm these principles with security stakeholders where appropriate.

##### Step 4 — Update governance and prompts

- In relevant governance docs (`AGENTS.md`, `CLAUDE.md`) and key prompts:
  - Add or refine sections that:
    - state the AI usage principles,
    - provide examples of safe vs unsafe patterns,
    - define where to store any AI‑generated artefacts that may touch sensitive topics.
- Ensure that:
  - prompts which interact with live systems or logs include reminders about redaction and anonymisation,
  - automation scripts do not automatically send sensitive content to external services.

##### Step 5 — Validation

- Spot-check repositories for compliance:
  - prompts and docs uphold the principles,
  - no obvious examples of unsafe AI usage.
- Optionally:
  - Create a small checklist in `.agents/reports/` to track which repos have been updated and reviewed.

#### Validation

- For each in-scope repository:
  - Check that AI usage sections in `AGENTS.md`, `CLAUDE.md`, and key prompts reflect the agreed principles.
  - Review a small sample of recent AI-assisted changes or sessions (where logs are available) for obvious security/privacy issues.
- Perform targeted reviews where sensitive data handling is most likely; confirm that any checklists or tracking reports are up to date.

#### Notes / Adaptation per repo

- For repositories that only host public information (e.g. public websites), the rules may be lighter but should still be explicit.
- For repositories handling more sensitive data, consider stricter local policies and escalations (for example requiring human review for any AI‑assisted change touching certain domains).

#### Options (planning phase)

**Delivery (choose before any commit or push):**

- **(A)** Create a branch and open a **draft** PR for the changes (recommended).
- **(B)** Create a branch only (no PR).
- **(C)** Local changes only (no branch, no push).

Do not commit or push until the user has chosen.

#### Plan refinement / Autoupdate

After applying this plan across multiple repositories:

- Recommended if relevant: apply updates to this `.plan.md` (e.g. more precise AI usage principles or improved validation patterns); validate changes accordingly and verbosely.
- Keep repository‑specific security constraints in local governance docs; the plan should express cross‑repo principles.
- If new classes of risks are identified, add them to the `Steps` and `Notes` so future runs proactively address them.
- If you discover that specific prompts, scripts, or configurations systematically violate or ignore the agreed safe‑usage principles, apply updates to those underlying artefacts and validate accordingly (verbose validation).
