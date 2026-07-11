---
name: aiscr-prod-ui-crawl-review
description: Deployed UI/SEO verification for user-facing public URLs in a target
  review_codebase workflow (optional T12/session); not GitHub PR review.
disable-model-invocation: true
---

<!-- aiscr:compiled=aiscr-prod-ui-crawl-review -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.gemini/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-prod-ui-crawl-review — deployed UI / SEO for review_codebase

Run optional **live deployed** checks for any AIS CR repo whose **public users** load HTML over HTTPS (webapp, docs site, static site, etc.), driven by the target repo's `review_config.toml`. Outputs: `deployed_ui_analysis.json` + `review_reports/T12.md` (typical)—**not** `review_pr.py`.

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

For **actionable T12-style** deployed UI/SEO findings that are not resolved in the current approved run, follow the workflow contract summarized in this compiled skill (*Deployed UI findings hand off to backlog*). Prefer citing an existing backlog item when the finding duplicates static analysis or an existing backlog entry.

1. After `review_reports/T12.md` (or equivalent) exists, prepare candidates with stable finding keys and the report path.
2. Ask for **explicit per-run** approval to emit backlog items.
3. If approved, draft the backlog candidate body inline — candidate slug, a one-line summary, `**Source report:**` (the approved report path), and `**Finding keys:**` — without copying sensitive evidence, then stop. Promotion into the management hub's backlog (creating the OpenSpec backlog change and refreshing the backlog overview) is a separate, explicit hub action by a maintainer; this workflow does not create hub changes or auto-invoke hub commands.
4. Name spawned slugs in the verification report or explain why none were emitted.

Do not promote or implement spawned backlog inside this skill.

## Context to load first

1. the workflow contract summarized in this compiled skill - behavioral requirements and architecture (Tier 1/2 model)
2. the workflow contract summarized in this compiled skill - backlog emission contract (when emitting follow-ups)
3. `AGENTS.md` - governance, scope, and safety rules
4. the embedded execution plan below - execution procedures and target repo variations
5. Target repo: `.agents/config/review_config.toml` (the `deployed_verify` allowlist and per-repo scope)

## Steps

1. Confirm **target repo path** (checkout). Confirm **staging vs production**; production requires explicit approval.
2. Follow that repo’s **INITIALIZATION SEQUENCE** (e.g. **aiscr-webamcr:** `review_tools.py`; **aiscr-digiarchiv-2:** directory + hash steps as documented—see plan appendix). Enrolled siblings drive this via the canonical `aiscr-codebase-review` workflow, not a standalone prompt.
3. Read `deployed_verify:` (or adopt the allowlist template via governance bootstrap if missing—separate change/PR).
4. Execute checks per plan (Tier 1; Tier 2 if policy allows); record `inconclusive_reasons` when blocked (auth, bot wall).
5. Write outputs in the target repo's active codebase-review output language. For repos governed by `aiscr-codebase-review`, that is the canonical **English-default with the Czech verbatim quotation carve-out** (source comments, docstrings, GitHub issue titles, and AIS CR domain identifiers stay Czech). For repos with their own review-output language rules, follow those.

<!-- aiscr:gen:id=guardrails -->
## Iron Law

**IRON LAW:** `NEVER CRAWL PRODUCTION URLS WITHOUT EXPLICIT USER CONFIRMATION. DEFAULT IS STAGING. PRODUCTION REQUIRES EXPLICIT APPROVAL EVEN FOR READ-ONLY CHECKS.`

No exceptions. Read-only does not mean risk-free for production crawls.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "Production is functionally equivalent to staging — I'll skip the confirmation" | Always confirm; production crawl requires explicit approval per run. |
| "The target URL is publicly accessible — no need for confirmation" | Publicly accessible does not mean approved for crawling; confirm before any production run. |
| "I'll just crawl a few pages to start" | No crawl of any scope on production without explicit approval; default to staging. |

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

Full workflow: the embedded execution plan below

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- Read the identifiers and references stated in this workflow and follow the **Usage** section before loading a different workflow's context.

## Embedded execution plan

### Plan: Deployed UI / SEO verification for review_codebase (user-facing public URLs)

> **OpenSpec migration:** Persistent behavioral requirements for this workflow now live in the workflow contract summarized in this compiled skill. This `.plan.md` file remains the reusable execution and governance layer for aiscr-management. See the identifiers and references stated in this workflow.

#### Context

This plan lives in **aiscr-management** and defines an **optional** on-demand task (**T12** working name: `deployed_ui_analysis`) for AIS CR repositories that already have codebase-review set up (`.agents/config/review_config.toml`), whenever maintainers want to check **live** behaviour of **user-facing surfaces reachable over the public internet** (not only classic webapps).

**Eligible targets include:** full-stack webapps, public documentation or marketing sites, static frontends, and any other **HTTP(S) HTML experience** end users or the public can load without private network access—**always** via **allowlisted** URLs in config. Pure backend APIs with no HTML surface are **out of scope** unless the repo also ships a public HTML UI or docs site you intentionally include in `deployed_verify`.

**Reference implementations (webapps):** [aiscr-webamcr](https://github.com/ARUP-CAS/aiscr-webamcr) (Django, `webclient/`) and [aiscr-digiarchiv-2](https://github.com/ARUP-CAS/aiscr-digiarchiv-2) (Java/Spring + Angular + Thymeleaf). Both use **T01–T11** today; **T07** is **static** frontend analysis only. This plan adds **live deployed** checks without replacing T07. **Documentation or other public-site repos** can adopt the same **T12 + `deployed_verify`** pattern or a **session-based** equivalent per `repository_setup.md`.

**Not in scope:** GitHub PR review (`review-pr.plan.md`, `review_pr.py`). **Do not** conflate this workflow with `aiscr-review-pr`.

Bootstrap and YAML shapes for new repos are set up through the management hub's governance-bootstrap workflow (its optional deployed-verification subsection).

#### Scope and assumptions

**In scope**

- Orchestration instructions and output contracts (this plan + skill `aiscr-prod-ui-crawl-review`).
- Execution via Playwright, browser/MCP tools, or **manual** checklist in the **target repo** checkout.
- Governance: allowlist, max pages, rate limiting, redaction, explicit approval before production.

**Out of scope**

- Search Console / ranking data; full-site crawl; visual regression baselines; cross-browser matrices.
- Mandatory automation script in `aiscr-management` (optional follow-up only).
- Changing sibling repos from this plan's execution in management—adoption is a **separate PR per repo** with maintainer approval.

**Assumptions**

- Target repo has (or will add) optional **T12** + `deployed_verify:` in `review_config.toml` (set up via the management hub's governance-bootstrap workflow if missing).
- T12 is **on-demand** initially: **omit T12 from T11 `requires`** until maintainers promote it.

#### Output artifacts

- Machine-readable: `.agents/analysis/deployed_ui_analysis.json`
- Human-readable: `.agents/reports/review_reports/T12.md` (or equivalent task ID)

See the workflow contract summarized in this compiled skill for output schema and requirements.

#### Focused review roles

- Map issues to the repo's front-end or site implementation.
- Use **aiscr-management-doc-auditor** when the public surface is primarily documentation or content.
- Perform focused security and accessibility/E2E analysis when findings require it.
- Use **aiscr-governance-reviewer** for governance-boundary questions.

#### Steps

1. **Orient** — Read target `AGENTS.md`, `.agents/config/review_config.toml`, `.agents/config/review_cache.json`. Follow that repo's **INITIALIZATION SEQUENCE** (e.g. **webamcr:** `review_tools.py hash` / `status` as documented; **digiarchiv:** directory + hash steps as documented—**do not assume one global script path**).
2. **Configure** — Read `deployed_verify:` (allowlisted `base_urls`, `max_pages`, `environments`). Refuse production without **explicit** maintainer approval for this run.
3. **Execute** — Run Tier 1; add Tier 2 only if policy allows. Use Playwright in the target repo, browser/MCP, or manual checklist for auth-walled flows.
4. **Persist** — Write `deployed_ui_analysis.json` and `T12.md`; update `review_cache.json` for T12; add `bugs.md` / backlog entries per repo rules.
5. **Map** — Tie URLs to repository paths (application templates and assets, SPA source, static site config, docs layout/theme, server header config, CDN rules—whatever owns the rendered experience).

#### Validation

- JSON parses; required top-level keys present (`schema_version`, `run_metadata`, `urls`, `issues`).
- `T12.md` exists when task claimed complete.
- No secrets in committed artefacts.

#### Appendix: Adoption in aiscr-webamcr and aiscr-digiarchiv-2

**Per-repo PR (maintainer approval):**

1. In `review_config.toml`, add task **T12** after T10, before T11:

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

3. Add a **`## DEPLOYED UI / SEO VERIFICATION (T12)`** section to the repo's review documentation, with per-task instructions (the registry stays in `review_config.toml`).

4. **Do not** add T12 to T11 `requires` until policy mandates it.

5. Narrative-output language follows the target repo's active codebase-review output language. For repos governed by `aiscr-codebase-review`, use the canonical **English-default with the Czech verbatim quotation carve-out** (preserve Czech source comments, docstrings, GitHub issue titles, and AIS CR domain identifiers). For repos with their own review-output language rules, follow those.

#### Notes / Adaptation per repo

- Repos **without** any user-facing public HTML: **skip** this workflow (or omit `deployed_verify`)—it does not replace API contract tests or private staging-only checks unless those URLs are deliberately allowlisted and reachable as agreed.
- **Docs, marketing, or static sites:** use the same **`deployed_verify` + artefact** discipline; task-based repos may use **T12**; **session-based** repos adapt as a **session type** (e.g. after release or when live site changes) per `repository_setup.md`—keep the same JSON/report output shape where practical.

#### Options (planning phase)

**Delivery:** default local only. Stage, commit, or push only on direct user order; if remote delivery is explicitly requested, use `agents/<agent-name>/<topic>` per [AGENTS.md](../../../AGENTS.md) and ask before creating or switching branches. **Sibling writes:** state branch per target repo and obtain confirmation before editing **aiscr-webamcr** or **aiscr-digiarchiv-2`.
