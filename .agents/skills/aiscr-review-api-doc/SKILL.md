---
name: aiscr-review-api-doc
description: Align API specs and documentation in API-focused repos. Use when the
  user asks to align OpenAPI specs with docs, or define API doc governance.
license: CC-BY-4.0
author: AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
---

<!-- SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- aiscr:compiled=aiscr-review-api-doc -->
<!-- delivery-version: 083eb1bc1a0c628b2d6d48b806b6568be3f67ac2 2026-11-07T12:31:37+01:00 -->

<!-- aiscr:entry-scope -->

**Entry scope (compiled)**

- This `.agents/skills/` skill is self-contained; use the workflow body below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-review-api-doc — API documentation alignment

Align API specs and documentation in repositories that define or document an API.

**Position in the review structure.**
An optional lens of the codebase-review pass (**T13**, alongside the deployed-UI lens at T12); it is not a standalone review — it runs within a review pass and writes into the same report set.

**Applicability is declared by this repository, not decided elsewhere.**
Whether an API exists is a fact about this repository's internals, so it is declared in this repository's own `.agents/config/review_config.toml` through the per-analysis toggle — `enabled = false` with a short reason where no API is defined or documented.
Enrollment means eligibility for the review set, not that an API exists; do not add a second mechanism.

Consume `aiscr-review-conduct` through the invoking repository's delivered rule reader; this body owns the procedure and output destination.

## Phase awareness

This is an **operational execution skill**: its subject is aligning API specifications with documentation and governance, not spec-governed repository state.
It runs without gating on OpenSpec context and never invokes `/openspec-propose`.
Execution boundaries: align the specs and docs for the approved task; do not
change API behavior, and do not create new OpenSpec changes or promote backlog items.

## Context to load first

1. `AGENTS.md` — governance and scope
2. The target repository's API specs and consumer docs *(non-file)*

## Steps

### Entry and target confirmation

This workflow supports both execution tiers — **in-repo** and **hub-cockpit** — whose semantics are defined under *Workflow execution tiers* in the `aiscr-ecosystem-governance` governance rule.
The operator states the target; no new argument is added, and alignment edits land in the target repository's specifications and docs either way.
Alignment across an API repository and its consumer repositories is several targets, each its own confirmation gate.

Confirm the target API repository and, when known, the locations of its OpenAPI specifications, documentation, generated references, or main API documentation entry point (for example a Quarto site).
Before changing which source is canonical rather than merely aligning a derived source, present that choice to the user.

### Context

This workflow targets AIS CR repositories that define or document APIs (e.g. `aiscr-api-home` and related services), ensuring OpenAPI/REST specifications, human-authored documentation, and AI-generated help content are aligned and clearly governed.

### Goals

- Establish clear **sources of truth** for API behaviour and lifecycle, eliminate drift between specs, docs, and AI-facing prompts, and give contributors and agents reliable guidance for API changes and deprecation.

### Scope and assumptions

- In scope:
  - API specifications (OpenAPI, JSON/YAML files).
  - API documentation sites and README‑level docs.
  - Any prompts or config files that describe API endpoints for AI tools.
- Out of scope:
  - Changing underlying API behaviour; focus is on documentation and governance.
  - Building entirely new documentation infrastructure.
  - Storing API-specific endpoint details or internal policies in this reusable workflow; those stay in the target repository's specifications and docs.
- Assumptions:
  - The API repo has a documentation entry point (e.g.
    Quarto site, README, or OpenAPI spec).
    Without an OpenAPI/REST spec, treat the main documentation as user-facing canonical and any agent-facing config (e.g. `.agents/config/review_config.toml` with `live_endpoints`) as canonical for live URLs and verification.

### Ecosystem map and related artifacts

- The canonical list of API and consumer repos is the ecosystem map (in aiscr-management).
  When scoping work (which repos document an API, and which consume one), load the map and use it: a repo documenting an API is one whose *Purpose* names API documentation.
  **Note — management repo visibility:** `aiscr-management` may not be accessible outside a local environment with direct filesystem or CLI access; when running from a sibling-repo context without such access, the ecosystem map and other management-repo files will not be directly readable — use a locally propagated copy or ask a maintainer with local access.
- `ecosystem_map.md` is the single place that records which repos are in scope (the repos whose *Purpose* names API documentation, plus relevant consumers).
  Do not duplicate that list in this workflow; when the in-scope set changes, update the map.

### Execution approach

- Find OpenAPI specs, API docs, and prompts mentioning endpoints.
- Cross-check how endpoints are used in code and tests.
- Review governance and documentation changes for clarity and consistency.

### Procedure

#### Step 1 — Inventory API docs and specs

- Identify:
  - OpenAPI/REST specs (e.g. `openapi.yaml`, `openapi.json`).
  - API sections in `README*`, `AGENTS.md`, the active assistant entry doc, and dedicated docs.
  - Any `.agents/` prompts or config files that contain endpoint URLs or curl commands.
- Record the inventory as the **T13** report under `.agents/reports/review_reports/` in this repository's review report set, in the style that repository already uses for per-task reports — with the rest of the review pass, not in a separate file no review consumer reads.

Keep the findings section in the T13 report: apply the shared conduct for admission and its API-doc route for proven pre-existing observations (a separated section in this report contribution), and record the resolved API/documentation scope and any incomplete verification with the alignment result.

#### Step 2 — Map sources of truth

- Decide:
  - Which file(s) are **canonical** for endpoint definitions, deprecation rules, and example requests/responses?
  - How other files should reference the canonical ones (links, short summaries, no duplication).
- If no OpenAPI/REST spec exists: treat the main API documentation (e.g.
  Quarto `.qmd` sections) as canonical for user-facing endpoint definitions and examples, and any `.agents/` config listing live URLs and curl (e.g. `live_endpoints` in `review_config.toml`) as canonical for agent verification; other files link to or summarise these, not duplicate endpoint tables.

#### Step 3 — Align docs and specs

- Fix drift by:
  - Update out-of-date URLs, parameters, or response shapes.
  - Replace duplicated endpoint descriptions with references to the canonical source.
  - Ensure deprecation information is in the canonical source and referenced elsewhere.

#### Step 4 — Define AI documentation generation rules

- In `AGENTS.md` or the active assistant entry doc:
  - Define rules for AI‑generated API docs:
    - Read the canonical source first: the OpenAPI spec if present, else the main API docs and live-endpoint config (e.g. `review_config.toml`).
    - Never invent endpoints or parameters absent from the canonical source.
    - Match generated examples' authentication and base URLs to the canonical source.
  - Optionally, create a dedicated AI prompt for generating or updating API docs with these rules.

### Validation

- Check that base URLs, auth patterns, and endpoint paths agree across documents, that deprecated endpoints are marked consistently in every view, and that the AI documentation rules cite the right canonical sources.
- Re-run the relevant validation tools: OpenAPI or similar spec validators on all in-scope API definitions, plus link or build checks for the documentation site where one exists.
- When no machine-readable spec exists, cross-check docs and `.agents/` config for consistent base URLs, auth patterns, and paths, and run any repo-defined verification (e.g. `review_config.toml` curl commands or checks named in `AGENTS.md`).
- Review the changes: inspect diffs in API specs and related docs, and confirm that responsibilities between specs, docs, and governance sections are clear and non-duplicative.

**Maintain ecosystem map and related artifacts (after run):**

- If the in-scope set of API-documentation repos or consumer repos changed, flag the management hub's ecosystem map for a hub-side update so its *Purpose* column reflects the current set of API-documentation and consumer repos.

### Notes / Adaptation per repo

- For documentation-only repos (e.g. `aiscr-api-home`): the documentation site is user-facing canonical; if an OpenAPI/REST spec exists it is canonical for endpoint definitions, otherwise the main API doc sections (e.g.
  Quarto) are canonical and any `.agents/` live-endpoint config is canonical for verification — all other sources defer via links or short summaries.
- For application repos that **consume** APIs (e.g. `aiscr-webamcr`, `aiscr-digiarchiv-2`), you may still apply this workflow in a reduced form to document external dependencies clearly.
  Deliverable for consumer repos: add or update a short section (e.g.
  "External APIs" or "Externí API") in README and/or AGENTS.md that lists consumed APIs and points to the canonical documentation repo (e.g. aiscr-api-home) and its published docs; do not duplicate endpoint definitions.

### Execution using subagents

**Posture: registers `survey` and the `integration` lens.**
Locating specs, docs and the endpoints code and tests actually use is a survey.
Judging whether a spec and its documentation agree is the integration lens, which owns API and documentation contracts.
Assign the lens the survey and the specific pairs it signalled, not the whole repository.

The posture vocabulary, the declared return contracts, and the admission test are owned by `aiscr-quality-first-execution`.
Acquire one route per invocation: the delegate definition where it resolves, or the shared library ([common](../../../.agents/skills/_dispatch/common.md), the contract part, and the lens part) run as a pass in this session.
Reading both delivers the contract twice.

<!-- aiscr:gen:id=guardrails -->

## Iron Law

**IRON LAW:** `NEVER APPLY SPEC OR DOC CHANGES TO A SIBLING REPO WITHOUT FIRST PRESENTING A FULL DIFF TO THE USER AND RECEIVING EXPLICIT PER-REPO APPROVAL.`

No exceptions.
Every target repo is a separate confirmation gate.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The spec and docs are clearly out of sync — I'll just update" | Identify the source of truth first; present the delta before writing any file. |
| "This doc change is minor — no need to confirm the branch" | Every target repo change requires per-repo branch confirmation and explicit approval. |
| "The canonical spec is obvious" | Confirm the source of truth with the user before making any derived changes. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Source of truth (canonical spec) identified and confirmed by user.
- [ ] All derived doc changes presented as a diff before being applied.
- [ ] No target repo changes applied without per-repo branch confirmation and explicit approval.
- [ ] Management-hub `ecosystem_map.md` flagged for update if the set of API repos changed.

<!-- aiscr:endgen -->

## Governance

- Do **not** run high-impact scripts unless the user explicitly asks.
- Before applying changes to a target repo, state the branch and obtain user confirmation.

## Valid next steps

- Hand the alignment result to its owner; acting on remaining API changes is work outside this skill.
- `/aiscr-review-api-doc` — re-run this workflow for the next alignment pass.
- Read `.agents/canonical_workflows_context.md` and follow the **Usage** section before loading a different workflow's context.
