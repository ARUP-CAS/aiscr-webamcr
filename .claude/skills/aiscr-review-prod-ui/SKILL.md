---
name: aiscr-review-prod-ui
description: Use when deployed UI or SEO verification is requested within a target
  codebase review. Verify public user-facing URLs in the optional T12 session.
license: CC-BY-4.0
author: AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
---

<!-- SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- aiscr:compiled=aiscr-review-prod-ui -->
<!-- delivery-version: 083eb1bc1a0c628b2d6d48b806b6568be3f67ac2 2026-11-07T12:31:37+01:00 -->

<!-- aiscr:entry-scope -->

**Entry scope (compiled)**

- This `.claude/skills/` skill is self-contained; use the workflow body below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-review-prod-ui — deployed UI / SEO for review_codebase

Run optional **live deployed** UI/SEO checks for any AIS CR repo whose **public users** load HTML over HTTPS, driven by the target repo's `review_config.toml`; outputs `deployed_ui_analysis.json` + `review_reports/T12.md`—**not** `github_pr_review.py`.

Consume `aiscr-review-conduct` through the invoking repo's delivered rule reader; this body owns the procedure and output destination.

## Phase awareness

This is an **operational execution skill**: its subject is verifying a deployed public UI and SEO against the target repo's allowlist, not spec-governed repository state.
It runs without gating on OpenSpec context and never invokes `/openspec-propose`.
Execution boundaries: verify the deployed UI and SEO for the approved run; do
not modify the deployed site or product code, and do not create new OpenSpec changes, promote backlog items, or escalate scope, except for the backlog-only handoff after explicit per-run approval (see **Report-to-backlog handoff** below).

## Report-to-backlog handoff

For **actionable T12-style** findings not resolved in the current approved run, follow the report-to-backlog handoff contract; the deployed-verification mapping obligation travels with the finding, and an existing backlog item is preferred when the finding duplicates static analysis.

1. After `review_reports/T12.md` (or equivalent) exists, prepare candidates with stable finding keys and the report path.
2. Ask for **explicit per-run** approval to emit backlog items.
3. If approved, branch on run context:

   - **Sibling or other non-hub run**: draft the same traceability fields inline — candidate slug, a one-line summary, `**Source report:**`, and `**Finding keys:**` — without copying sensitive evidence, then stop before any management-hub write.
     Emitting the item is a separate, explicit hub action by a maintainer; this workflow does not create hub changes or auto-invoke hub commands.
4. Name spawned slugs in the verification report or explain why none were emitted.

Do not promote or implement spawned backlog inside this skill.

## Context to load first

1. `AGENTS.md` — governance, scope, and safety rules
2. Target repo: `.agents/config/review_config.toml` (the `deployed_verify` allowlist and per-repo scope)

## Steps

### Context

This workflow lives in **aiscr-management** and defines an **optional** on-demand task (**T12** working name: `deployed_ui_analysis`) for AIS CR repositories that already have codebase-review set up (`.agents/config/review_config.toml`), whenever maintainers want to check **live** behaviour of **user-facing surfaces reachable over the public internet** (not only classic webapps).

**Eligible targets include:** any public **HTTP(S) HTML experience**, **always** via **allowlisted** URLs in config.
Pure backend APIs with no HTML surface are **out of scope** unless the repo also ships a public HTML UI or docs site included in `deployed_verify`.

**Reference implementations (webapps):** [aiscr-webamcr](https://github.com/ARUP-CAS/aiscr-webamcr) (Django, `webclient/`) and [aiscr-digiarchiv-2](https://github.com/ARUP-CAS/aiscr-digiarchiv-2) (Java/Spring + Angular + Thymeleaf).
Both use **T01–T11** today; **T07** is **static** frontend analysis only.
This workflow adds **live deployed** checks without replacing T07.
**Documentation or other public-site repos** can adopt the same **T12 + `deployed_verify`** pattern or a **session-based** equivalent per the canonical `aiscr-setup-governance` workflow.

**Not in scope:** GitHub PR review (`aiscr-review-pr.md`, `github_pr_review.py`).
**Do not** conflate this workflow with `aiscr-review-pr`.

Bootstrap and YAML shapes for new repos are set up through the management hub's governance-bootstrap workflow (its optional deployed-verification subsection).

### Scope and assumptions

**In scope**

- Orchestration instructions and output contracts (this workflow + skill `aiscr-review-prod-ui`).
- Execution via Playwright, browser/MCP tools, or **manual** checklist in the **target repo** checkout.
- Governance: allowlist, max pages, rate limiting, redaction, explicit approval before production.

**Out of scope**

- Search Console / ranking data; full-site crawl; visual regression baselines; cross-browser matrices.
- Mandatory automation script in `aiscr-management` (optional follow-up only).
- Changing sibling repos from this workflow's execution in management—adoption is a **separate PR per repo** with maintainer approval.
- Before any approved sibling adoption edit, state the target repository's current branch and obtain confirmation for that repository.

**Assumptions**

- Target repo has (or will add) optional **T12** + `deployed_verify:` in `review_config.toml` (set up via the management hub's governance-bootstrap workflow if missing).
- T12 is **on-demand** initially: **omit T12 from T11 `requires`** until maintainers promote it.

### Output artifacts

- Machine-readable: `.agents/analysis/deployed_ui_analysis.json`
- Human-readable: `.agents/reports/review_reports/T12.md` (or equivalent task ID)

See the production-UI verification capability contract for output schema and requirements.

### Focused review roles

- Map issues to their front-end or site implementation.
- Take a documentation-review stance when the public surface is primarily documentation or content.
- Perform focused security and accessibility/E2E analysis when findings require it.
- Take a governance-review stance for governance-boundary questions.

**Posture: registers `survey`.**
Tying rendered URLs to the repository paths that own them — templates and assets, SPA source, static site config, server headers, CDN rules — is a survey: a bounded trace whose inventory this session consumes without repeating it.
Assign it the URL set and the target checkout.
The stances above, the probing, and every conclusion about live behaviour stay in this session, because a delegate cannot drive a browser against an allowlisted deployment and a probe result is session-local evidence.

Acquire one route per invocation: the delegate definition where it resolves, or the shared library ([common](../../../.agents/skills/_dispatch/common.md), the contract part, and the lens part) run as a pass in this session.
Reading both delivers the contract twice.
Apply the shared conduct's observation route through the existing report-to-backlog handoff above.
The report cites the observation evidence, but no separate bug-store copy or unapproved backlog write is created for a proven pre-existing observation.

### Procedure

1. **Orient** — Confirm the target checkout and read its `AGENTS.md`, `.agents/config/review_config.toml`, and `.agents/config/review_cache.json`.
   Both execution tiers apply, with semantics defined under *Workflow execution tiers* in the `aiscr-ecosystem-governance` governance rule: the allowlist that bounds the crawl is that checkout's configuration, so the target is a repository in either tier and every artifact in step 4 lands in it.
   Follow that repo's **INITIALIZATION SEQUENCE** (e.g. **webamcr:** `codebase_review.py hash` / `status` as documented; **digiarchiv:** directory + hash steps as documented—**do not assume one global script path**).
   Enrolled siblings invoke this session through the canonical `aiscr-review-codebase` workflow, not a standalone prompt.
2. **Configure** — Read `deployed_verify:` (allowlisted `base_urls`, `max_pages`, `environments`); refuse production without **explicit** maintainer approval.
3. **Execute** — Run Tier 1; add Tier 2 only if policy allows.
   Use Playwright, browser/MCP, or a manual checklist; record `inconclusive_reasons` when an access boundary blocks a conclusion.
4. **Persist** — Write `deployed_ui_analysis.json` and `T12.md`; update `review_cache.json` for T12; add admitted findings to the typed findings sources and regenerate their Markdown twins per repo rules.
   Use the target repo's active review-output language — under `aiscr-review-codebase`, English by default with Czech source comments, docstrings, GitHub issue titles, and AIS CR domain identifiers verbatim.
5. **Map** — Tie URLs to repository paths (application templates and assets, SPA source, static site config, docs layout/theme, server header config, CDN rules—whatever owns the rendered experience).

### Validation

- JSON parses with required top-level keys (`schema_version`, `run_metadata`, `urls`, `issues`); the `T12.md` report written to the target repository exists when the task is claimed complete; no secrets in committed artefacts.

### Appendix: Adoption in aiscr-webamcr and aiscr-digiarchiv-2

**Per-repo PR (maintainer approval):**

1. In the target repository's `review_config.toml`, add task **T12** after T10, before T11:
   - `id: T12`, `name: deployed_ui_analysis`, `description: …`, `target_file: .agents/analysis/deployed_ui_analysis.json`, `priority: 12`.
2. Add **`deployed_verify:`** (short) e.g.:

   ```yaml
   deployed_verify:
     default_environment: staging
     max_pages: 15
     base_urls:
       staging:
         - "https://allowed-staging-host.example/"
     crawl_notes: "Do not add production URLs without maintainer approval."
   ```

3. Add a **`## DEPLOYED UI / SEO VERIFICATION (T12)`** section to the repo's review documentation, with per-task instructions (the registry stays in the target repository's `review_config.toml`).
4. **Do not** add T12 to T11 `requires` until policy mandates it.
5. Narrative-output language follows the target repo's active codebase-review output language: for repos governed by `aiscr-review-codebase`, the canonical **English-default with the Czech verbatim quotation carve-out** (Czech source comments, docstrings, GitHub issue titles, and AIS CR domain identifiers preserved); repos with their own rules follow those.

### Notes / Adaptation per repo

- Repos **without** user-facing public HTML: **skip** this workflow (or omit `deployed_verify`)—it does not replace API contract tests or private staging-only checks unless those URLs are deliberately allowlisted and reachable.
- **Docs, marketing, or static sites:** use the same **`deployed_verify` + artefact** discipline; task-based repos may use **T12**; **session-based** repos adapt as a **session type** per `aiscr-setup-governance`, keeping the same JSON/report output shape.

<!-- aiscr:gen:id=guardrails -->

## Iron Law

**IRON LAW:** `NEVER CRAWL PRODUCTION URLS WITHOUT EXPLICIT USER CONFIRMATION. DEFAULT IS STAGING. PRODUCTION REQUIRES EXPLICIT APPROVAL EVEN FOR READ-ONLY CHECKS.`

No exceptions.
Read-only does not mean risk-free for production crawls.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "Production is functionally equivalent to staging — I'll skip the confirmation" | Always confirm; production requires explicit approval per run. |
| "The target URL is publicly accessible — no need for confirmation" | Publicly accessible does not mean approved; confirm before any production run. |
| "I'll just crawl a few pages to start" | No production crawl without explicit approval; default to staging. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Target repo path and staging vs production confirmed before any crawl.
- [ ] No production URLs crawled without explicit user approval.
- [ ] Outputs written to designated paths (`deployed_ui_analysis.json`, `review_reports/T12.md`).
- [ ] Sensitive URLs and tokens redacted from all output.

<!-- aiscr:endgen -->

## Governance

- Do not confuse with **PR review** (`aiscr-review-pr`).
- No crawl without allowlist/caps; redact sensitive URLs and tokens.

## Valid next steps

- Hand the deployed UI/SEO verification report to its owner; fixing findings is work outside this skill.
- `/aiscr-review-prod-ui` — re-run this workflow for the next deployed verification pass.
- Read `.agents/canonical_workflows_context.md` and follow the **Usage** section before loading a different workflow's context.
