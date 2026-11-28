---
name: aiscr-review-live
description: Use when the user asks to verify a deployed AIS CR service against a
  driving issue and its implementation. Discover and probe the live surface, verify
  findings in-session, and prepare the corpus report and issue comment.
argument-hint: <issue-number>
license: CC-BY-4.0
author: AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
---

<!-- SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- aiscr:compiled=aiscr-review-live -->
<!-- delivery-version: a9e7178f2056994b3ac481702b0ec38cdb13c576 2026-11-28T16:49:05+01:00 -->

<!-- aiscr:entry-scope -->

**Entry scope (compiled)**

- This `.agents/skills/` skill is self-contained; use the workflow body below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-review-live — live acceptance verification

Acceptance-verify a deployed AIS CR service against one driving issue: establish the expected behaviour from the issue together with its implementation, find test candidates by discovery recipe, probe the deployed test instance (comparing with production where meaningful), verify every finding in the session that reports it, and emit a testing-scenario report in the subject's corpus plus a comment on the issue.

Consume `aiscr-review-conduct` through the invoking repository's delivered rule reader for severity, admission, exclusions, security exceptions, observations, empty results, and untrusted input; own the procedure and output destination.

## Phase awareness

This is an **operational execution skill** for a deployed service's behaviour against one driving issue, not spec-governed repository state; it never gates on OpenSpec context and never invokes `/openspec-propose`.
Execution boundaries: verify and report only — do not modify the deployed service or its product code, do not fix what you find, or escalate beyond the driving issue's acceptance.

## Context to load first

1. The subject repository's `AGENTS.md` and, where one exists, its testing-scenario corpus index.

## Steps

### Capability contract (inline summary)

- Expected behaviour is established from the driving issue together with the implementation **before** the deployed surface is probed; a probe result is compared against that expectation, never interpreted on its own, and a finding reported without it is unverified.
- Test candidates are found by **discovery recipes** — durable procedures yielding fresh candidates — never by embedded record identifiers, which drift while a recipe survives; a verification command may carry an identifier placeholder the recipe fills.
  The prohibition binds the report, not the comment: the comment may cite examined example records as active links into the deployed instance where examined, each paired with its recipe.
  Identifier-free links — endpoints, search and query URLs, links illustrating the live endpoint and its result — are as durable as recipes and welcome in both artefacts.
- Finding admission follows the shared conduct; deployed evidence is this session's, and a correction is preserved when later evidence changes an earlier conclusion.
- A run emits **two artefacts**: a testing-scenario report in the subject's corpus and a comment on the driving issue.
- **Language split:** the comment follows the issue's language and that surface's declared heading forms; the report is written in English under the subject's English operational authority for durable agent-facing surfaces.
  Domain entity names appear verbatim in their native form in both.
- Checks requiring a role, credentials, or a browser the run lacks are marked **maintainer-assisted** with what they require; their outcome is never inferred from an anonymous result, and credentialed probing happens only at the maintainer's direction.
- Before such a check is marked, the run **offers the operator a short dialog** with what is needed, what it would unblock, and how to supply it.
  A gap whose answer unblocks the session's probing is raised and applied when found; a gap only the operator can perform is queued and raised once, in one consolidated dialog, before any artefact is written.
  The option to decline for the rest of the run rides on the first prompt actually raised, so a run that never needs help never asks.
  A declined, deferred, or unanswered prompt leaves no trace: the check appears exactly as it would had the dialog never fired.
- The issue comment renders everything a maintainer must still act on as **GitHub task-list entries** and settled items as plain list items.
  `Findings` carries only open findings, `Maintainer-assisted checks` is all task entries, and `Verified behaviour` and `Unverified` carry none.
  A defect walked to fixed or changed appears under `Verified behaviour`; a defect not examined appears under `Unverified`, never under `Verified behaviour`.
  The comment shape validation enforces both directions.
- A **run merges** its scenario row into the repository's existing corpus index and regenerates the view before writing either; a run-local index would destroy every other scenario's entry under whole-file delivery.
  Where the current index cannot be read, the run stops and writes nothing — a failed read is not an absent corpus.
  Where the repository carries no corpus, the base is legitimately empty and the index carries the one scenario.

<!-- aiscr:ecosystem-only -->

- In the **hub-cockpit tier**, that merge is performed hub-side against the subject's index, and the result is delivered through the approval-gated artefact delivery engine.

<!-- aiscr:ecosystem-end -->

- A scenario report separates **durable knowledge** (environments, architecture and endpoint facts, the feature or entity model, discovery recipes, verification commands) from **point-in-time verification** (the behaviour matrix, known defects, corrections made in the run).
  A newer verification supersedes the older, while durable knowledge is amended and accumulates.
- A repeat run on a known scenario is a **regression pass**: it reuses the prior report's recipes and endpoint knowledge, compares the new behaviour matrix against the prior verification, and resolves every earlier recorded defect to a stated outcome — still present, fixed, changed, or not examined.
  A defect not examined is stated as not examined, never left to read as fixed.
- Each recorded defect carries an **identifier stable across runs** — never derived from list position, a date, or anything else that changes when the report is rewritten.
- The corpus carries a **structured index** declaring per scenario its key, covered features and entities, exercised surfaces, driving issues, and last verification date.
  Its human-readable view is generated and never hand-edited; a view that does not match generation is an error, and a scenario file with no index entry is reported, not left undiscoverable.
- Scenarios are keyed on a **feature** by default, on an **entity** only where that entity's own introduction or rework is the subject; a surface is never a key — surfaces are dimensions exercised within a scenario.
  A fact true across entities belongs to the feature scenario with its per-entity deviation table; a fact true for one entity across features belongs to that entity's scenario, which cites the feature scenario for the mechanism and records only its deviations.
- A scenario is **one living file** at a path that does not change between verifications, carrying its durable body, the current verification, and a bounded verification log with one entry per past run (date, instance or build verified, what changed).
  Superseded verification detail does not accumulate; it stays recoverable from the repository's history at that stable path.
- A missing corpus is **created from the bundled starter** on first run, so the corpus exists with its explanatory content; no empty placeholder file is ever created to hold the directory open.

### Where the run executes

This workflow runs in the repository whose deployed service it tests.
The operator states the target; the acceptance loop is identical, and only how outputs reach the subject and the comment is posted differs:

- **In-repo tier.**
  The report, the corpus index, and the generated view are written into the working tree of the repository the workflow runs in, on its current branch.
  With the deterministic GitHub write engine, the comment is posted through it under exact-content approval; without it, the run renders the exact comment and hands it to the maintainer to post — performing no GitHub mutation outside the engine.

<!-- aiscr:ecosystem-only -->

- **Hub-cockpit tier.**
  A maintainer runs it from the management hub against a registered sibling, with semantics defined under *Workflow execution tiers* in the ecosystem governance rules.
  The report, the merged index, and the regenerated view are delivered into the subject repository through **artefact delivery** on the sibling delivery engine — `inspect` → `plan` → approval-gated `apply` — never through a session-side file write into the subject, because this delivery is a governed bundle apply carrying its own provenance and overwrite review rather than an ordinary file write.
  The subject's index is read by a sanctioned sibling read route and merged hub-side (Step 8); state and confirm the target repository's branch before the apply.
  The comment is posted through the deterministic write engine from the hub.

<!-- aiscr:ecosystem-end -->

### Step 1 — Establish expected behaviour

- Read the driving issue in full: description, comments, and linked work.
- Read the subject repository's implementation that claims to satisfy it — the change, its tests, and its documentation.
- Write down, per behaviour under test, what the issue asked for and what the implementation claims.
  Every later probe is compared against this statement; a divergence is reported as a finding, not absorbed as the expected result, and a finding prepared without this expectation is marked unverified until established.

### Step 2 — Resolve prior knowledge from the corpus

- Where the subject carries a testing-scenario corpus, resolve relevant scenarios from the index's declared coverage — features, entities, surfaces, driving issues — never from filenames.
- A known scenario makes the run a regression pass: reuse its recipes and endpoint knowledge, compare the new behaviour matrix against the prior verification, and walk every earlier defect to a stated outcome (still present, fixed, changed, or not examined).
- Where the subject has no corpus, create it from the bundled starter — the corpus README, the scenario file template, and the index engine — together with the first report, so the corpus exists with its explanatory content on first use.
  Never create a placeholder file to hold the directory open.

### Step 3 — Find candidates by discovery recipe

- Record the durable procedure by which a reader finds fresh candidates: the search, the filter, the listing endpoint, the navigation path.
  Never embed a concrete record identifier as the means of reproducing a check in the report.
- A link that embeds no record identifier — an endpoint, search, or query URL illustrating the live endpoint and its result — is durable like a recipe, because opening it re-executes against the current deployment; it is welcome in the report's durable half and in the comment.
  The test for any link is whether it carries a concrete record identifier.
- A verification command may carry an identifier placeholder the recipe fills at verification time.

### Step 4 — Probe the deployed surface

- Resolve the probing mechanics from the production-UI verification capability: allowlisted probe targets, staging-first execution, explicit production approval, rate limiting, and redaction of sensitive data.
  Where this workflow needs something stricter, it says so here: a probe result obtained without the Step 1 expectation is evidence of nothing and is not reported as verified.
- Probe the deployed **test** instance first.
  Compare against production only where that comparison is meaningful for the behaviour under test, and state what was compared.
- The curated probe command entries may not be live in every runtime.
  Where a probe shape is refused, degrade to prompt-gated execution of the same shape; do not fail the run or reach the probe by a route the control does not cover — report the gap to the operator.
- When a gap would prevent a check completing, offer the operator a short dialog before marking anything maintainer-assisted, carrying what is needed, what it would unblock, and how to supply it:
  - a gap whose answer lets the session continue probing — an ambiguity in what the issue asks for, or a selection among records — is raised **when it is found**; apply the answer and continue probing;
  - a gap only the operator can perform — a role-gated check, a credentialed flow, a browser action the runtime lacks — is **queued**, because no answer lets the session perform it; every queued gap is raised once, in one consolidated dialog, before Step 6 writes any artefact.
- The first prompt actually raised offers the option to **decline the dialog for the remainder of the run**.
  After a decline, ask nothing further; every remaining gap takes today's mark-and-report path.
  A declined, deferred, or unanswered prompt produces no sub-vocabulary in the artefacts: the check is marked maintainer-assisted with what it requires, indistinguishable from a run where the dialog never fired.
- Credentialed probing happens only at the maintainer's direction; the dialog gathers that direction, not replaces it.
  Never infer a credentialed result from an anonymous one.

### Step 5 — Verify before reporting

- Apply the shared conduct to candidates using this session's exact probes.
- Put incomplete checks in the unverified-checks output; route admitted security exceptions under the shared conduct.
  Record proven pre-existing observations only in the report's separated pre-existing-observations section.
- Where later evidence in this run corrects an earlier claim, record the correction with the original conclusion visible, showing which conclusions moved and why.
- An answer supplied through the Step 4 dialog is input to verification like any other probe result: if it moves an earlier conclusion, record the correction the same way.
  A check raised but unanswered at artefact time is maintainer-assisted, marked exactly as in a run where the dialog never fired.

### Step 6 — Emit the report (English)

- File the scenario as one living document at `.agents/reports/testing_scenarios/<scenario-key>.md`, per the bundled template's split: durable body, current verification, bounded verification log.
- Amend the durable half where the run found it incomplete or wrong; do not re-derive it from scratch.
  Supersede only the dated half, and add one log entry for the superseded run.
- Assign the scenario key per the ownership rule: feature by default, entity only where that entity's introduction or rework is the subject.
  An entity scenario cites the feature scenario for the mechanism it depends on and records only its deviations.
- Mint stable identifiers for newly recorded defects, reusing the existing identifiers for defects walked to still present, fixed, or changed.
- Merge this run's scenario row into the corpus index and regenerate its human-readable view with the bundled engine, upserting by scenario key so prior entries survive; a stale view is an error, and a scenario file with no index entry is reported.
- The report is English; domain entity names appear verbatim in their native form.

<!-- aiscr:ecosystem-only -->
The hub-cockpit tier merges hub-side onto the subject's current index, per Step 8.
<!-- aiscr:ecosystem-end -->

### Step 7 — Emit the issue comment (the issue's language)

- Before authoring the comment, run `python .agents/scripts/github/github_issues.py prepare-handoff --workflow aiscr-review-live --run <run>`.
  It creates `<HANDOFF_DIR>` (`.agents/local_scratch/aiscr-review-live/<run>/`) and `POINTER.md` naming `.venv/.cache/aiscr-review-live/<run>/`.
  Write the exact comment body to `<HANDOFF_DIR>/comment.md`; keep machine artefacts in the named bulk directory.
  The sidecar pointer stays outside posted bytes; placement classification is owned by `workflow/artefact-placement`.
- Render the approval view into the same directory rather than letting it print to stdout: `python .agents/scripts/github/github_issues.py approval-view post-comment <ISSUE_NUMBER> --body <HANDOFF_DIR>/comment.md --repo OWNER/REPO --approval-view <HANDOFF_DIR>/comment-approval.json`.
- Render the comment in the driving issue's language, using the comment surface's declared heading forms for that language, one language per comment; domain entity names appear verbatim in their native form.
- The comment carries the run's verification result: a summary and what was verified, plus findings and the maintainer-assisted checks with what they require; anything unverified is stated as unverified.
- Outstanding and settled items take different list forms; the write engine refuses a comment that mixes them:
  - `Findings` carries only findings **still open**, every top-level list item a GitHub task-list entry (`- [ ]`), tickable in the issue thread;
  - `Maintainer-assisted checks` likewise consists entirely of task-list entries, each stating what it requires;
  - `Verified behaviour` and `Unverified` are plain bullet lists with no task-list entries anywhere.
- Route each earlier recorded defect by its outcome: still open stays under `Findings` as a task-list entry; fixed or changed moves to `Verified behaviour` as a plain bullet recording its current state; not examined moves to `Unverified`, never to `Verified behaviour` — displaying an unexamined defect as verified presents silence as resolution.
- Cite the concrete example records examined as active links into the deployed instance where examined, so the maintainer opens and tracks them directly; pair each cited record with its discovery recipe, so an equivalent candidate stays findable when the record drifts.
  Identifier-free links — endpoints, query URLs, links illustrating a live result — are welcome here too.
- Where the run has the deterministic write engine, present the exact rendered body and its approval view, obtain approval of the digest, and post it through the engine's issue-comment command (`post-comment <ISSUE_NUMBER> --mode interactive --body <HANDOFF_DIR>/comment.md --approved-digest <sha> --approval-view <HANDOFF_DIR>/comment-approval.json --repo OWNER/REPO`).
  The write validates the exact approval file; editing it requires re-rendering and fresh approval.
- Where the run lacks the engine, hand the exact rendered comment to the maintainer to post; the run performs no GitHub mutation outside the engine.

### Step 8 — Deliver by tier

- **In-repo:** the corpus writes of Step 6 are already in the working tree; leave them unstaged for review.

<!-- aiscr:ecosystem-only -->

- **Hub-cockpit:** the index is merged hub-side before any delivery, so a run-local one-entry index never replaces the subject's:
  1. Read the subject's current corpus index by a sanctioned sibling read route — the native route where the product's control row records a grant, otherwise the sibling read surface — which resolves its target only from the sibling registry and reports found, absent, or failed distinctly.
  2. A **failed read stops the run**: deliver nothing.
     A failure presented as an absent corpus would rebuild the index from empty and destroy every prior scenario's entry; report the failure to the operator instead.
  3. Merge this run's scenario row into the base index with the bundled index engine's merge subcommand, which preserves every base entry it did not upsert and validates the merged index before writing.
     An absent index — no corpus yet — is the legitimate first-run base and yields a single-entry index.
  4. Regenerate the human-readable view from the merged index with the bundled engine.
  5. Deliver the report, the merged index, and the regenerated view through artefact delivery on the sibling delivery engine, on a branch stated and confirmed for the subject repository: `plan --artefact <path> --artefact-capability review/live-acceptance-verification --targets <repo>` reports the resolved destination and content digest, and the approval-gated `apply` with the same selection delivers it.

<!-- aiscr:ecosystem-end -->

When every posting and delivery decision is final and every approved write succeeded (or was declined), run `python .agents/scripts/github/github_issues.py cleanup-handoff --workflow aiscr-review-live --run <run> --kind comment --approve`.
Retain the run's hand-off when validation, posting, delivery, or retry failed.
Without the engine, create the same bounded directory and sidecar before authoring, and hand local cleanup to the maintainer after posting is confirmed.

### Execution using subagents

**Posture: registers `survey`.**
Step 1 is a survey: read the driving issue in full and the implementation that claims to satisfy it, and return per behaviour under test what was asked against what is claimed, as a per-item `summary` this assignment names.
Every later probe is compared against that statement.
Probing and verification stay in this session, because a delegate cannot re-probe a deployed surface and a probe result is session-local evidence.

The posture vocabulary, declared return contracts, and admission test are owned by `aiscr-quality-first-execution`.
Acquire one route per invocation: the delegate definition where it resolves, or the shared library ([common](../../../.agents/skills/_dispatch/common.md), the contract part, and the lens part) run as a pass in this session; reading both delivers the contract twice.

<!-- aiscr:gen:id=guardrails -->

## Iron Law

**IRON LAW:** `NEVER POST THE ISSUE COMMENT WITHOUT PRESENTING THE EXACT RENDERED BODY AND RECEIVING EXPLICIT APPROVAL BOUND TO ITS DIGEST.`

No exceptions.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The response looks right, so the behaviour works." | Compare against the expectation stated from the issue and the implementation; an observed response shows what the deployment does, not what the issue asked for. |
| "I'll record this record ID so the check is reproducible." | In the report, record the discovery recipe finding an equivalent candidate; in the comment, cite the example records examined as links, each paired with its recipe. |
| "The anonymous response is probably what a role would see." | Mark the check maintainer-assisted with the required role; never infer a credentialed outcome. |
| "The defect is gone from my matrix, so it's fixed." | Mark it not examined; silence is not resolution. |
| "I'll write the report straight into the subject checkout from outside it." | Deliver through the governed delivery route; a session-side write is a bypass finding, not a technique. |
| "The probe command was refused, so I'll reach it another way." | Degrade to prompt-gated execution and report the gap; a route around a control is evidence the control set is incomplete, not a technique. |
| "The newer verification replaces the whole report." | Amend the durable half; supersede only the dated half. Rewriting everything discards knowledge the report itself calls expensive to rediscover. |
| "The comment is long, so I'll post a shortened version." | The digest binds the exact body: render, present, approve, then post exactly what was approved. |
| "This check needs something I can't do anonymously, so I'll mark it maintainer-assisted and move on." | Offer the gap to the operator first: answerable gaps when found, operator-only gaps in one consolidated dialog before any artefact; a declined or unanswered prompt then takes mark-and-report, leaving no trace. |
| "The subject's index couldn't be read, so I'll deliver the index this run built." | Stop and deliver nothing. A failed read is not an absent corpus: a run-local one-entry index under whole-file delivery destroys every prior scenario's row while its file remains undiscoverable. |
| "The defect is fixed now, so it goes back in Findings as resolved." | Route it under Verified behaviour as a plain bullet; Findings carries only still-open items as task lists, and the write engine refuses the mixed shape. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Expected behaviour was stated from the driving issue and the implementation before the first probe.
- [ ] Finding admission and the report's observation route follow the shared conduct; deployed evidence and corrections are this session's.
- [ ] Every earlier recorded defect on a known scenario was resolved: still present, fixed, changed, or not examined.
- [ ] New defects carry stable identities; no positional, dated, or reorder-sensitive identifiers were minted.
- [ ] The report is in English at the scenario's stable path, with the durable/dated split respected and the log bounded to one entry per past run.
- [ ] The corpus index was updated and its view regenerated; the view is not stale and no scenario file is missing from it.
- [ ] Every gap the run met was offered to the operator before being marked maintainer-assisted — answerable gaps when found, operator-only gaps in one consolidated dialog — unless the operator declined on the first prompt raised.
- [ ] No declined, deferred, or unanswered prompt left a trace in the artefacts; each affected check reads as if the dialog never fired.
- [ ] The comment is in the driving issue's language with declared heading forms and domain entity names verbatim, and was posted through the deterministic engine under an approved digest — or handed to the maintainer where the run lacks one.
- [ ] `Findings` and `Maintainer-assisted checks` render task-list entries only; `Verified behaviour` and `Unverified` carry none; each earlier defect is routed by outcome — still open in Findings, fixed or changed in Verified behaviour, not examined in Unverified.
- [ ] Example records cited in the comment are linked to the instance examined and paired with their recipes; every link in either artefact embeds no record identifier unless it is such a citation.

<!-- aiscr:ecosystem-only -->

- [ ] Hub-cockpit outputs were delivered through artefact delivery on a branch stated and confirmed for the subject repository; the deliverable index was the subject's own merged with this run's row, and an unreadable index stopped the run with nothing delivered.

<!-- aiscr:ecosystem-end -->

- [ ] No probe reached production without the production-approval gate; no refused probe shape was routed around.

<!-- aiscr:endgen -->

## Governance

- GitHub references follow the delivered `aiscr-quality-first-execution` rule (*GitHub references*).
- The testing-scenario corpus is repository-owned output of the subject: never synced from elsewhere, never reconciled against a foreign copy, never reported as drift.
- Findings stay in the report and the comment; fixing them is work outside this skill, under the subject repository's own issue and backlog policy.
- This skill creates no OpenSpec changes and promotes no backlog items.

## Valid next steps

- `/aiscr-review-live <ISSUE_NUMBER>` — re-run on the same or another scenario; a repeat run on a known scenario is a regression pass.
- Hand unverified and maintainer-assisted checks to the maintainers; performing them is outside this skill.
- End the session; the filed report, the updated index, and the posted comment are the durable output.

## Bundled scripts

The enrollment bundle installs these repository-local runtime scripts:

- `.agents/scripts/testing_scenario_corpus.py`
- `.agents/scripts/github/github_issues.py`
- `.agents/scripts/github/github_utils.py`
- `.agents/scripts/github/github_references.py`
- `.agents/scripts/lib/__init__.py`
- `.agents/scripts/lib/local_scratch_paths.py`
- `.agents/scripts/lib/log_utils.py`
- `.agents/scripts/lib/proc_utils.py`
- `.agents/scripts/lib/runtime_env.py`
- `.agents/canonical_configs/templates/documents/testing_scenario.md`
- `.agents/canonical_configs/templates/documents/testing_scenario_corpus_readme.md`
