---
name: aiscr-review-pr
description: Review a GitHub PR — durable behavioral contract in OpenSpec spec; execution
  runbook in plan. Ingest prior review context, structure findings into buckets (resolved
  / disputed / not addressed / new), post body and inline comments as a single grouped
  review via GH API.
disable-model-invocation: true
---

<!-- aiscr:compiled=aiscr-review-pr -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.gemini/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-review-pr — GitHub PR review

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

1. the workflow contract summarized in this compiled skill — durable behavioral requirements and review architecture
2. `AGENTS.md` — governance and scope
3. `.agents/README.md` — hub structure
4. the embedded execution plan below — execution procedures and operator runbook

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

2. **Structure findings** into the bucket taxonomy with severity labels:
   - **Resolved** — confirmed fixed in the diff; acknowledge briefly.
   - **Disputed** — author responded; evaluate technical validity; flag if insufficient.
   - **Not addressed** — missing from author response; call out explicitly.
   - **New findings** — issues found by independent review of new or changed code.

   Severity: 🔴 Critical, 🟠 Serious, 🟡 Medium, 🟢 Minor/informational.

3. **Classify inline findings** — for each finding decide: reply to an existing thread
   (same `path` + `line` in `existing_threads`) or new inline comment (verified in the
   diff). Lines not in the diff → move to the review body (API returns 422 otherwise).

4. **Generate payload and post** — write `review_payload.json` (body, event, commit_id,
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

<!-- aiscr:gen:id=guardrails -->
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
<!-- aiscr:endgen -->

## Governance

- Keep PR review findings in the PR. Do **not** copy them into `bugs.md`,
  `refactoring_backlog.md`, or any codebase audit file.
- Exception: a pre-existing defect found incidentally may be logged to the repo's
  technical debt backlog with the PR as discovery context.
- Full workflow: the embedded execution plan below.
- Script reference: `.agents/scripts/review_pr.py`.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- Read the identifiers and references stated in this workflow and follow the **Usage** section before loading a different workflow's context.

## Embedded execution plan

### Plan: GitHub PR Review Workflow

> **OpenSpec migration:** Persistent behavioral requirements for this workflow now live in the workflow contract summarized in this compiled skill. This `.plan.md` file remains the execution-layer runbook for operators. See the identifiers and references stated in this workflow.

#### Context

This plan is the execution-layer runbook for the PR review workflow. The durable behavioral contract lives in the workflow contract summarized in this compiled skill.

This plan defines a reusable end-to-end workflow for reviewing a GitHub pull request in any
AIS CR repository. It is the backing plan for the **aiscr-review-pr** skill (Claude command,
Cursor skill, Codex skill).

The workflow handles multi-round review cycles where a prior review and author response already
exist, but is equally applicable to fresh reviews. It produces a formal GitHub PR review
(body + inline comments) posted in a single API call so all findings appear grouped as one
review unit in the GitHub UI.

The plan lives in `aiscr-management` and is orchestrated by the `aiscr-review-pr` skill;
see the identifiers and references stated in this workflow for full skill interfaces. Mechanical steps
(fetching PR state, posting the review) are handled by `.agents/scripts/review_pr.py`;
no separate execution prompt is needed — the workflow is self-contained in this plan and
the skill files.

**Qodo augmentation (optional):** Qodo can be used as an optional pre-step to pull
repository-specific review rules before structuring findings. Prefer the MCP path when
available; it avoids requiring an IDE extension to be installed by the reviewer. The core
`gather → structure → post` flow is identical with or without Qodo — see
the **Qodo augmentation** section below for integration details and the full fallback chain.

#### Goals

- Provide a repeatable structure for PR reviews that includes prior-context ingestion and
  bucketed analysis (resolved / disputed / not addressed / new) without requiring manual review or comment IDs.
- Post review body and inline comments as a single grouped review (not standalone diff
  comments) via the GH API; reply to existing threads for findings that map to prior
  inline comments, leaving threads open.
- Always post as the **GitHub Actions bot identity**: `GH_TOKEN` must be set to a
  GitHub Actions installation token or GitHub App installation token. Reviews must not
  appear under a personal account.
- Enforce scope discipline: PR findings stay in the PR and are not propagated to codebase
  backlog files (`bugs.md`, `refactoring_backlog.md`).

#### Scope and assumptions

- **In scope**
  - Fetching PR state, diff, prior review body, author response comment, and existing inline
    threads via `review_pr.py gather` — all discovered automatically from the PR number alone.
  - Structuring findings into the bucket taxonomy with severity labels.
  - Generating JSON payloads (review body + comments array; replies list) as files on disk.
  - Posting a single grouped review via `review_pr.py post --review-payload <file>` with a
    `comments` array for new inline threads, and replies via `--replies <file>` for
    findings matching existing threads.
  - Bot identity enforced by `review_pr.py post`: the script exits with an error if
    `GH_TOKEN` is not set.
- **Out of scope**
  - Modifying source code in response to review findings (that is the author's task).
  - Closing or resolving existing comment threads.
  - Propagating PR review findings to `bugs.md`, `refactoring_backlog.md`, or any codebase
    audit file.
- **Assumptions**
  - `gh` CLI is installed and authenticated (`gh auth status`).
  - The caller provides only the PR number; prior review and author response are discovered
    automatically from the PR's review history and comment thread.
  - If no prior review exists, the prior-review buckets collapse: "Resolved", "Disputed",
    and "Not addressed" are omitted; only "New findings" applies.
  - Inline comments only attach to lines present in the PR diff. Lines in unmodified files
    return HTTP 422 from the GH API.
  - `GH_TOKEN` is pre-set to a GitHub Actions or GitHub App installation token before
    running `review_pr.py post`. The script refuses to post if `GH_TOKEN` is absent.

#### Focused review roles

- Read the diff and structure findings across the required buckets.
- Add focused security analysis for auth, input validation, secrets handling, or other sensitive changes.
- The GH API posting remains handled by `review_pr.py`.

Subagents do **not** replace reading the repo's governance docs (`AGENTS.md`,
`CONTRIBUTING.md`) before reviewing.

#### Steps

##### Step 1 — Gather context

Run the gather script to fetch all PR context in one call:

```bash
python .agents/scripts/review_pr.py gather $PR_NUMBER
```

The script prints a JSON object with:

- `owner_repo`, `head_sha`, `pr_author`
- `last_review_id`, `last_review_body`, `last_review_comments` (null when no prior review)
- `author_response` (null when the author has not responded)
- `existing_threads` — array of `{id, path, line, body}` for root-level inline comments

If `last_review_id` is null, run as a fresh review: the "Resolved", "Disputed", and
"Not addressed" buckets are omitted and only "New findings" applies.

Also fetch the diff for analysis:

```bash
gh pr view $PR_NUMBER
gh pr diff $PR_NUMBER
```

##### Step 2 — Structure findings

Classify all findings into the four buckets defined in the spec (Resolved, Disputed, Not addressed, New).
Apply severity labels (Critical, Serious, Medium, Minor) to unresolved items and new findings.

##### Step 3 — Classify inline findings: new thread vs reply

For each candidate inline comment, decide how to post it:

- **Reply to existing thread** — if an existing root comment matches the same `path` + `line`
  as the finding (compare against `existing_threads` from Step 1), add it to the replies list.
  Do **not** close or resolve the thread.
- **New inline comment** — if no existing thread matches, include the comment in the main
  review payload's `comments` array. The diff line must be verified first (see below).
- **Move to review body** — if the line is not in the PR diff (`+` or space prefix), include
  the finding in the main review body instead (API returns 422 otherwise).

To verify a new inline comment target is in the diff, search the diff output from Step 1
for the exact target line. Lines not found → move to review body.

##### Step 4 — Generate review payload and reply list

Write two JSON files to disk (e.g. `/tmp/review_payload.json` and `/tmp/review_replies.json`):

**review_payload.json** — the main review object:

```json
{
  "body": "<Markdown review body with all bucket sections>",
  "event": "COMMENT",
  "commit_id": "<head_sha from Step 1>",
  "comments": [
    {
      "path": "relative/path/to/file.ext",
      "line": 123,
      "side": "RIGHT",
      "body": "**Finding**\n\nSuggestion..."
    }
  ]
}
```

- `event`: `COMMENT` = non-blocking; `REQUEST_CHANGES` blocks merge; `APPROVE` approves.
- `comments`: new inline threads only — do not include findings that map to existing threads.
- `side`: `RIGHT` for added lines, `LEFT` for removed lines.

**review_replies.json** — replies to existing threads:

```json
[
  {"comment_id": 123456789, "body": "Suggestion: ..."}
]
```

- `comment_id`: root comment ID from `existing_threads` in Step 1.
- Keep the reply as a hint only — do not close or resolve the thread.

Generate the JSON using Python (`json.dump`) or any method that correctly handles
non-ASCII characters and nested quotes. Do not use shell heredocs for the payload body.

##### Step 5 — Post review and thread replies

Export `GH_TOKEN` to a GitHub Actions or GitHub App installation token so the review
appears from the bot identity. Then run:

```bash
python .agents/scripts/review_pr.py post $PR_NUMBER \
    --review-payload /tmp/review_payload.json \
    --replies /tmp/review_replies.json
```

The script:

1. Validates `GH_TOKEN` is set (exits with an error if missing).
2. Posts the main review (body + new inline comments) in one API call.
3. Posts each reply to its existing thread individually (threads remain open).
4. Prints the review URL and reply URLs.

If the main review returns 422 for a comment object, remove it from the `comments` array,
add its content to the `body`, regenerate `review_payload.json`, and repost.

#### Qodo augmentation (optional)

Qodo can provide repository-specific review rules via its MCP server before Step 2
(structure findings). This is an optional pre-step — the core `gather → structure → post`
flow is unchanged whether or not Qodo is available.

See the spec Architecture section for the Qodo fallback chain (MCP → IDE → degraded).

##### Hub baseline: `.pr_agent.toml` and local `.qodo/`

The hub commits **`.pr_agent.toml`** at the repository root with `automatic_review = false`, propagated via `REPO_ROOT_SYNC_IDS` and `repos.toml` (see `config-sync.plan.md`, `mandatory_vendor_doc_urls.toml`). That keeps the Qodo PR bot aligned with the **manual** `aiscr-review-pr` workflow rather than unsolicited automated reviews.

**`.qodo/`** at the repo root is **gitignored** (IDE/plugin local state). It is **not** part of `local_configs` sync — do not treat `.qodo/` as a committed hub baseline.

##### Degraded path

Proceed with `review_pr.py gather` → structure findings using the AI reviewer's own analysis
→ post via `review_pr.py post`. No Qodo rules are pulled. Review quality is not blocked —
it relies entirely on the AI reviewer and the repo's own governance docs.

Document the path used in the review body header when relevant (e.g. `_Review performed
without Qodo rules (no active subscription)._`).

#### Validation

1. Main review URL printed by the script; review appears as a single unit with body and
   inline comments in the GitHub UI.
2. Reply URLs printed for each thread reply; replies appear under the existing thread,
   which remains open (not resolved).
3. All bucket sections are represented in the review body (or noted as empty if not applicable).
4. No findings have been written to `bugs.md`, `refactoring_backlog.md`, or any codebase
   audit file.
5. Review shows the GitHub Actions bot identity, not the reviewer's personal account.
6. `python .agents/scripts/review_pr.py --help` prints both subcommands.

#### Notes / Adaptation per repo

- **Repos with Czech docstrings** (e.g. `aiscr-webamcr`): review comments may be written in
  Czech or English per project convention; check `CONTRIBUTING.md` of the target repo.
- **Security-sensitive PRs**: add a focused security pass in addition to the standard review.
- **Large diffs**: split the review into functional areas (e.g. backend / frontend / CI);
  consider posting per-area review comments rather than one monolithic body.

#### Options (planning phase)

This plan posts a review to a remote GitHub PR — it does not change local files. No branch
or PR is needed for the plan execution itself.

**Scope / target:** Confirm the PR number with the user before starting. Prior review and
author response are auto-discovered — no manual IDs needed.

#### Plan refinement / Autoupdate

After using this workflow:

- If certain bucket categories are consistently empty (e.g. "Disputed" on first-round
  reviews), simplify the template for fresh reviews.
- If 422 errors recur for specific file types or line ranges, add pre-flight diff
  verification patterns to Step 3.
- Keep this plan repo-agnostic; capture target-repo-specific conventions in that repo's
  `CONTRIBUTING.md` or governance docs.

## Bundled scripts

The enrollment bundle installs these repository-local runtime scripts:

- `.agents/scripts/review_pr.py`
- `.agents/scripts/log_utils.py`
