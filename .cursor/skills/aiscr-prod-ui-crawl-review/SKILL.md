---
name: aiscr-prod-ui-crawl-review
description: Deployed UI/SEO verification for user-facing public URLs in a target
  review_codebase workflow (optional T12/session); not GitHub PR review.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-prod-ui-crawl-review.md -->

# aiscr-prod-ui-crawl-review

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Run optional **live deployed** checks for any AIS CR repo whose **public users** load HTML over HTTPS (webapp, docs site, static site, etc.) using `review_codebase.md` + `review_config.yaml`. Outputs: `deployed_ui_analysis.json` + `review_reports/T12.md` (typical)—**not** `review_pr.py`.

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

1. `openspec/specs/production-ui-verification/spec.md` - behavioral requirements and architecture (Tier 1/2 model)
2. `AGENTS.md` - governance, scope, and safety rules
3. `.agents/plans/prod-ui-crawl-review.plan.md` - execution procedures and target repo variations
4. Target repo: `.agents/prompts/review_codebase.md` and `.agents/config/review_config.yaml`

## Steps

1. Confirm **target repo path** (checkout). Confirm **staging vs production**; production requires explicit approval.
2. Follow that repo’s **INITIALIZATION SEQUENCE** (e.g. **aiscr-webamcr:** `review_tools.py`; **aiscr-digiarchiv-2:** steps in its prompt—see plan appendix).
3. Read `deployed_verify:` (or adopt template from `repository_setup.md` if missing—separate change/PR).
4. Execute checks per plan (Tier 1; Tier 2 if policy allows); record `inconclusive_reasons` when blocked (auth, bot wall).
5. Write outputs; narrative language per target `review_codebase.md` (e.g. Czech for webamcr/digiarchiv when applicable).

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

## Plan and workflow

`.agents/plans/prod-ui-crawl-review.plan.md`

**Registry fallback:** Load openspec/specs/production-ui-verification/spec.md first for the durable behavioral contract; in target repo load `AGENTS.md`, `review_codebase.md`, `review_config.yaml`; read `deployed_verify` allowlisted URLs; confirm staging-first and explicit approval for production; run Tier 1 checks (optionally Tier 2 per policy); write `deployed_ui_analysis.json` and `T12.md`; update `review_cache.json`; map findings to source assets per stack; follow prod-ui-crawl-review.plan.md for execution workflow.

## Governance

- Do not confuse with **PR review** (`aiscr-review-pr`).
- No crawl without allowlist/caps; redact sensitive URLs and tokens.

Full workflow: `.agents/plans/prod-ui-crawl-review.plan.md`

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow