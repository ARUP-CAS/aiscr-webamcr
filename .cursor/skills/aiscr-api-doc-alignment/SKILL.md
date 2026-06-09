---
name: aiscr-api-doc-alignment
description: Align API specs and documentation in API-focused repos. Use when the
  user asks to align OpenAPI specs with docs, or define API doc governance.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-api-doc-alignment.md -->

# aiscr-api-doc-alignment

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

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

## Context to load first

1. `openspec/specs/api-specification-sync/spec.md` — behavioral requirements and architecture
2. `AGENTS.md` — governance and scope
3. `.agents/canonical_configs/references/ecosystem_map.md` — canonical list of API and consumer repos
4. `.agents/plans/api-doc-alignment.plan.md` — alignment workflow

## Steps

1. Ask the user: API repo path; optionally location of OpenAPI specs, docs, or main API doc entry point (e.g. Quarto site).
2. Inventory API docs and specs: find all OpenAPI/Swagger files, doc pages, and generated references.
3. Map sources of truth: identify which spec is canonical and which docs are derived.
4. Align docs and specs: update derived docs to match canonical spec (or vice versa, per user choice).
5. Define AI doc-generation rules in `AGENTS.md` or relevant governance file if applicable.
6. Validate API doc governance: confirm sources of truth are documented and references are correct.
7. If the set of API-related repos or local_configs changed, update `ecosystem_map.md` (use `/aiscr-ecosystem-mapper`).

## Iron Law

**IRON LAW:** `NEVER APPLY SPEC OR DOC CHANGES TO A SIBLING REPO WITHOUT FIRST PRESENTING A FULL DIFF TO THE USER AND RECEIVING EXPLICIT PER-REPO APPROVAL.`

No exceptions. Every target repo is a separate confirmation gate.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The spec and docs are clearly out of sync — I'll just update" | Identify the source of truth first; present the delta before writing any file. |
| "This doc change is minor — no need to confirm the branch" | All sibling repo changes require per-repo branch confirmation and explicit approval. |
| "The canonical spec is obvious" | Confirm the source of truth with the user before making any derived changes. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Source of truth (canonical spec) identified and confirmed by user.
- [ ] All derived doc changes presented as a diff before being applied.
- [ ] No sibling repo changes applied without per-repo branch confirmation and explicit approval.
- [ ] `ecosystem_map.md` updated via `/aiscr-ecosystem-mapper` if the set of API repos changed.

## Plan and workflow

`.agents/plans/api-doc-alignment.plan.md`

**Registry fallback:** Load openspec/specs/api-specification-sync/spec.md first for the durable behavioral contract; load `.agents/canonical_configs/references/ecosystem_map.md` for API repo list; inventory OpenAPI specs and docs per plan Step 1; map sources of truth per Step 2; follow api-doc-alignment.plan.md for alignment workflow and governance documentation.

## Governance

- Do **not** run high-impact scripts unless the user explicitly asks.
- Before applying changes to a sibling repo, state the branch and obtain user confirmation.
- Full workflow: `.agents/plans/api-doc-alignment.plan.md`

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow