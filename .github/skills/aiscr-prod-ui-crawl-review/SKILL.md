---
name: aiscr-prod-ui-crawl-review
description: Deployed UI/SEO verification for user-facing public URLs in a target
  review_codebase workflow (optional T12/session); not GitHub PR review.
---

<!-- aiscr:compiled=aiscr-prod-ui-crawl-review -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.github/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-prod-ui-crawl-review — deployed UI / SEO for review_codebase

Run optional **live deployed** checks for any AIS CR repo whose **public users** load HTML over HTTPS (webapp, docs site, static site, etc.), driven by the target repo's `review_config.yaml`. Outputs: `deployed_ui_analysis.json` + `review_reports/T12.md` (typical)—**not** `review_pr.py`.

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
5. Target repo: `.agents/config/review_config.yaml` (the `deployed_verify` allowlist and per-repo scope)

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
