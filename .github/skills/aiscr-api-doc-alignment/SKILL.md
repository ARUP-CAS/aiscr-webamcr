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

## Embedded execution plan

### Plan: API Governance and Documentation Alignment

> **OpenSpec migration:** Persistent behavioral requirements for this workflow now live in the workflow contract summarized in this compiled skill. This `.plan.md` file remains the reusable execution and governance layer for aiscr-management. See the identifiers and references stated in this workflow.

#### Context

This plan targets AIS CR repositories that define or document APIs (for example `aiscr-api-home` and related services).
It ensures that:

- OpenAPI/REST specifications,
- human‑authored documentation,
- and AI‑generated help content

are aligned and clearly governed.

#### Goals

- Establish clear **sources of truth** for API behaviour and lifecycle.
- Eliminate drift between specs, docs, and AI‑facing prompts.
- Provide contributors and agents with reliable guidance for API changes and deprecation.

#### Scope and assumptions

- In scope:
  - API specifications (OpenAPI, JSON/YAML files).
  - API documentation sites and README‑level docs.
  - Any prompts or config files that describe API endpoints for AI tools.
- Out of scope:
  - Changing underlying API behaviour; focus is on documentation and governance.
  - Building entirely new documentation infrastructure.
- Assumptions:
  - The API repo has a documentation entry point (e.g. Quarto site, README, or OpenAPI spec). If there is no OpenAPI/REST spec file, treat the main documentation (e.g. Quarto sections per API) as user-facing canonical and any agent-facing config (e.g. `.agents/config/review_config.toml` with `live_endpoints`) as canonical for live URLs and verification.

#### Ecosystem map and related artifacts

- The canonical list of API and consumer repos is the identifiers and references stated in this workflow (in aiscr-management). When scoping work (e.g. which repos are docs/api or API consumers), load the map and use it. **Note — management repo visibility:** `aiscr-management` may not be accessible outside a local environment with direct filesystem or CLI access; when running from a sibling-repo context without such access, `ecosystem_map.md` and other management-repo files will not be directly readable — use a locally propagated copy or ask a maintainer with local access.
- The plan's `relatedRepos` frontmatter should match or be a subset of the map (docs/api + relevant consumers) and must be kept in sync when the in-scope repo set changes.

#### Execution approach

- Find OpenAPI specs, API docs, and prompts mentioning endpoints.
- Cross-check how endpoints are used in code and tests.
- Review governance and documentation changes for clarity and consistency.

#### Steps

##### Step 1 — Inventory API docs and specs

- Identify:
  - OpenAPI/REST specs (e.g. `openapi.yaml`, `openapi.json`).
  - API sections in `README*`, `AGENTS.md`, `CLAUDE.md`, and dedicated docs.
  - Any `.agents/` prompts or config files that contain endpoint URLs or curl commands.
- Optionally record the outcome in a short inventory (e.g. `.agents/reports/api-docs-specs-inventory.md`) for future runs and for mapping sources of truth in Step 2.

##### Step 2 — Map sources of truth

- Decide:
  - Which file(s) are **canonical** for:
    - endpoint definitions,
    - deprecation rules,
    - example requests/responses.
  - How other files should reference the canonical ones (links, short summaries, no duplication).
- If the repo has no OpenAPI/REST spec: treat the main API documentation (e.g. Quarto `.qmd` sections) as canonical for user-facing endpoint definitions and examples, and any `.agents/` config that lists live URLs and curl (e.g. `live_endpoints` in `review_config.toml`) as canonical for agent verification. Other files should link to or summarise these; avoid duplicating endpoint tables.

##### Step 3 — Align docs and specs

- Fix drift by:
  - Updating out‑of‑date URLs, parameters, or response shapes.
  - Removing or replacing duplicated endpoint descriptions with references to the canonical source.
  - Ensuring deprecation information is present in the canonical source and referenced elsewhere.

##### Step 4 — Define AI documentation generation rules

- In `AGENTS.md` or `CLAUDE.md`:
  - Define rules for AI‑generated API docs:
    - Always read the canonical source first (OpenAPI spec if present, otherwise the main API docs and agent live-endpoint config, e.g. `review_config.toml`).
    - Never invent endpoints or parameters not present in the canonical source.
    - When generating examples, ensure they match authentication and base URLs from the canonical source.
  - Optionally, create a dedicated AI prompt for generating or updating API docs with these rules.

##### Step 5 — Validation

- Check that:
  - all documents agree on base URLs, auth patterns, and endpoint paths,
  - deprecated endpoints are consistently marked across all views,
  - AI prompts reference the right canonical sources.
- If no OpenAPI/REST spec exists, validation is cross-check of base URLs, auth patterns, and paths across governance and docs, plus manual or curl-based checks as defined in the repo (e.g. AGENTS.md, review prompts).
- Optionally:
  - Run automated tools (for example OpenAPI validators) to ensure specs remain valid.

#### Validation

- Re-run the relevant validation tools:
  - OpenAPI or similar spec validators on all in-scope API definitions.
  - Link or build checks for the documentation site, if available.
- When no machine-readable spec exists: cross-check docs and config for consistent base URLs and auth; run any repo-defined verification (e.g. curl commands from `review_config.toml`).
- Review the changes:
  - Inspect diffs in API specs and related docs,
  - Confirm that responsibilities between specs, docs, and governance sections are clear and non-duplicative.

**Maintain ecosystem map and related artifacts (after run):**

- If the in-scope set of API/docs-api repos or consumer repos changed, flag the management hub's ecosystem map for a hub-side update; update this plan's `relatedRepos` to reflect the current set of docs/api and consumer repos.
- If the API doc alignment workflow context or outputs changed, update the identifiers and references stated in this workflow (API doc alignment row) and the aiscr-api-doc-alignment entry in the identifiers and references stated in this workflow so they stay consistent.

#### Notes / Adaptation per repo

- For documentation‑only repos (e.g. `aiscr-api-home`): the documentation site is user‑facing canonical. If an OpenAPI/REST spec exists, it is canonical for endpoint definitions; if not, the main API doc sections (e.g. Quarto) are canonical, and any `.agents/` live-endpoint config is canonical for verification. All other sources should defer via links or short summaries.
- For application repos that **consume** APIs (e.g. `aiscr-webamcr`, `aiscr-digiarchiv-2`), you may still apply this plan in a reduced form to document external dependencies clearly. Deliverable for consumer repos: add or update a short section (e.g. "External APIs" or "Externí API") in README and/or AGENTS.md that lists consumed APIs and points to the canonical documentation repo (e.g. aiscr-api-home) and its published docs; do not duplicate endpoint definitions.

#### Options (planning phase)

**Delivery (choose before any commit or push):**

- **(A)** Create a branch and open a **draft** PR for the changes (recommended).
- **(B)** Create a branch only (no PR).
- **(C)** Local changes only (no branch, no push).

Do not commit or push until the user has chosen.

#### Plan refinement / Autoupdate

After aligning API documentation and specs in one or more repos:

- Recommended if relevant: apply updates to this `.plan.md` (e.g. clearer mapping patterns between specs and docs, or typical pitfalls); validate changes accordingly and verbosely.
- Keep API‑specific details (exact endpoints, internal policies) in the respective repo’s docs and specs, not in the plan.
- If certain validation steps prove especially valuable or insufficient, adjust the `Steps` and `Validation` sections so future runs benefit from that experience.
- If, during repeated use, you find recurring issues in API‑related prompts or scripts (for example documentation generators), apply updates to those tools and validate accordingly (verbose validation).
