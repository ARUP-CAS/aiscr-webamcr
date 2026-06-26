---
name: aiscr-api-doc-alignment
description: Align API specs and documentation in API-focused repos. Use when the
  user asks to align OpenAPI specs with docs, or define API doc governance.
---

<!-- aiscr:compiled=aiscr-api-doc-alignment -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.github/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-api-doc-alignment — API documentation alignment

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

1. the workflow contract summarized in this compiled skill — behavioral requirements and architecture
2. `AGENTS.md` — governance and scope
3. The target repository's API specs and consumer docs (the repo this workflow runs in)
4. the embedded execution plan below — alignment workflow

## Steps

1. Ask the user: API repo path; optionally location of OpenAPI specs, docs, or main API doc entry point (e.g. Quarto site).
2. Inventory API docs and specs: find all OpenAPI/Swagger files, doc pages, and generated references.
3. Map sources of truth: identify which spec is canonical and which docs are derived.
4. Align docs and specs: update derived docs to match canonical spec (or vice versa, per user choice).
5. Define AI doc-generation rules in `AGENTS.md` or relevant governance file if applicable.
6. Validate API doc governance: confirm sources of truth are documented and references are correct.
7. If the set of API-related repos, sync policy, or direct-bundle API-doc assets changed, flag the management hub's `ecosystem_map.md` for a hub-side update.

<!-- aiscr:gen:id=guardrails -->
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
- [ ] Management-hub `ecosystem_map.md` flagged for update if the set of API repos changed.
<!-- aiscr:endgen -->

## Governance

- Do **not** run high-impact scripts unless the user explicitly asks.
- Before applying changes to a sibling repo, state the branch and obtain user confirmation.
- Full workflow: the embedded execution plan below

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- Read the identifiers and references stated in this workflow and follow the **Usage** section before loading a different workflow's context.
