---
name: aiscr-review-pr
description: Review a GitHub PR — durable behavioral contract in OpenSpec spec; execution
  runbook in plan. Ingest prior review context, structure findings into buckets (resolved
  / disputed / not addressed / new), post body and inline comments as a single grouped
  review via GH API.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-review-pr.md -->

# aiscr-review-pr

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Review a PR end-to-end: gather prior context, structure findings, and post as a formal
GH review with inline comments where possible.

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

1. `openspec/specs/pr-review-workflow/spec.md` — durable behavioral requirements and review architecture
2. `AGENTS.md` — governance and scope
3. `.agents/README.md` — hub structure
4. `.agents/plans/review-pr.plan.md` — execution procedures and operator runbook

## Arguments

`<PR_NUMBER>`

Prior review context and author responses are discovered automatically from the PR's
review and comment history — no manual IDs needed.

## Bot identity requirement

Always post reviews as the **GitHub Actions bot identity**. Export `GH_TOKEN` to a
GitHub Actions installation token or GitHub App installation token before running
the post step. `review_pr.py post` will exit with an error if `GH_TOKEN` is not set.

## Steps

1. **Gather context** — fetch all PR state in one call:

   ```bash
   python .agents/scripts/review_pr.py gather $PR_NUMBER
   ```

   Returns JSON with `owner_repo`, `head_sha`, `pr_author`, `last_review_body`,
   `last_review_comments`, `author_response`, and `existing_threads`.
   Also run `gh pr diff $PR_NUMBER` to read the diff for analysis.

   If `last_review_id` is null: fresh review — omit "Resolved", "Disputed",
   "Not addressed"; only "New findings" applies.

> **Optional — Qodo augmentation:** before step 2, check Qodo availability:
> (a) MCP available + active subscription → pull repo-specific review rules via MCP;
> (b) IDE extension only → use extension if installed;
> (c) neither, or **no active Qodo subscription** → skip silently; proceed to step 2.
> Subscription limit is a primary fallback trigger — treat it the same as MCP unavailability.
> Note in the review body when relevant: `Review performed without Qodo rules (no active subscription).`

1. **Structure findings** into the bucket taxonomy with severity labels:
   - **Resolved** — confirmed fixed in the diff; acknowledge briefly.
   - **Disputed** — author responded; evaluate technical validity; flag if insufficient.
   - **Not addressed** — missing from author response; call out explicitly.
   - **New findings** — issues found by independent review of new or changed code.

   Severity: 🔴 Critical, 🟠 Serious, 🟡 Medium, 🟢 Minor/informational.

2. **Classify inline findings** — for each finding decide: reply to an existing thread
   (same `path` + `line` in `existing_threads`) or new inline comment (verified in the
   diff). Lines not in the diff → move to the review body (API returns 422 otherwise).

3. **Generate payload and post** — write `review_payload.json` (body, event, commit_id,
   comments array for new threads) and `review_replies.json` (list of
   `{comment_id, body}` for existing threads). Use Python `json.dump` for non-ASCII
   safety. Then post:

   ```bash
   python .agents/scripts/review_pr.py post $PR_NUMBER \
       --review-payload /tmp/review_payload.json \
       --replies /tmp/review_replies.json
   ```

   If a comment returns 422, remove it from `comments`, add its content to `body`,
   and repost.

## Iron Law

**IRON LAW:** `NEVER POST REVIEW COMMENTS TO GITHUB WITHOUT PRESENTING FULL GROUPED FINDINGS AND RECEIVING EXPLICIT APPROVAL.`

No exceptions. Presenting findings is always Step N; posting is always the next step and only after approval.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The findings are clear — I'll post them immediately to save a round-trip" | Present the full grouped findings first; post only after explicit approval. |
| "Inline comment failed with 422 — I'll retry on the same line" | Move the comment to the review body; do not retry against the same diff line. |
| "GH_TOKEN is not set — I'll post with my default credentials" | Export a GitHub Actions installation token before running the post step; never post with personal credentials. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Findings structured into buckets (Resolved / Disputed / Not addressed / New findings) before posting.
- [ ] Full review presented to user and explicit approval received before `review_pr.py post`.
- [ ] `GH_TOKEN` set to GitHub Actions bot identity before post step.
- [ ] No findings copied to codebase audit files (`bugs.md`, `refactoring_backlog.md`, etc.).

## Plan and workflow

`.agents/plans/review-pr.plan.md`

**Registry fallback:** Load openspec/specs/pr-review-workflow/spec.md first for the durable behavioral contract. PR number + optional GH_TOKEN; run review_pr.py gather for prior context; structure findings into buckets (resolved, disputed, not addressed, new) with severity labels; post grouped review per review-pr.plan.md (review_pr.py post).

## Governance

- Keep PR review findings in the PR. Do **not** copy them into `bugs.md`,
  `refactoring_backlog.md`, or any codebase audit file.
- Exception: a pre-existing defect found incidentally may be logged to the repo's
  technical debt backlog with the PR as discovery context.
- Full workflow: `.agents/plans/review-pr.plan.md`.
- Script reference: `.agents/scripts/review_pr.py`.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow