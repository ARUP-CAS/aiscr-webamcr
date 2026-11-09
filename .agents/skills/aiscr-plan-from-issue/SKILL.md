---
name: aiscr-plan-from-issue
description: Use when the user asks to turn a fully shaped GitHub issue into an OpenSpec
  implementation plan. Validate issue readiness, create the change in its owning repository,
  open a draft PR, and stop before implementation.
argument-hint: <issue-number>
license: CC-BY-4.0
author: AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
---

<!-- SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- aiscr:compiled=aiscr-plan-from-issue -->
<!-- delivery-version: c35418343fe8896348732bd54f8256de17338f8d 2026-11-07T14:33:16+01:00 -->

<!-- aiscr:entry-scope -->

**Entry scope (compiled)**

- This `.agents/skills/` skill is self-contained; use the workflow body below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-plan-from-issue — promote an issue into an OpenSpec change

Turn a fully described GitHub issue into an OpenSpec change **in the repository that owns the issue**, on the branch its implementation will use, ending in a draft pull request — then stop.
Issues are the ideation layer; OpenSpec is entered here, at the implementation boundary.

**Run this in a checkout of the repository the issue belongs to.**
The change, branch, and pull request live where the implementation will happen; promoting elsewhere files the plan in a repository the work never reaches, and the engine refuses a target that is not this checkout.

**When to use this versus the adjacent workflow:** this skill promotes an issue whose description is already complete; developing that description is `aiscr-plan-issue`.
If the issue is thin, you want that one first — this skill will say so and stop.

## Phase awareness

This skill operates at the **plan → implement boundary** of the OpenSpec lifecycle.
It creates OpenSpec change artifacts from an already-described issue and then hands off to the OpenSpec execution seeds; it must not initiate implementation or cross into the apply phase itself.
Crossing that boundary requires fresh post-promotion approval naming the specific change; approval for shaping, for readiness assessment, or for promotion does not carry forward to it.

Check for an existing OpenSpec change for this issue before creating a second one.

## Context to load first

1. The issue itself, gathered whole — see step 1. *(non-file)*
2. This repository's `openspec/config.yaml`: the declared schema decides the artifact set, not this workflow.
3. This repository's `CONTRIBUTING.md`: it owns the branch naming convention and base branch, which differ per repository — do not carry one in from elsewhere.
4. This repository's `AGENTS.md`.

## Steps

> **Authority:** Persistent behavior lives in the `github-issue-lifecycle` capability contract.
> This file owns the execution procedure and volatile runtime choices.

### Arguments

Argument: `<ISSUE_NUMBER>` — the issue to promote.

### 1. Gather, then assess readiness

```bash
python .agents/scripts/github/github_issues.py assess-readiness <ISSUE_NUMBER>
```

**Only the invoking checkout applies.**
The target is this checkout; a `--repo` naming a different repository is refused, because promotion writes files, a branch, and a pull request that belong where the issue lives, so a run from another checkout would put the change in the wrong repository.

<!-- aiscr:ecosystem-only -->
Tier semantics are defined under *Workflow execution tiers* in the `aiscr-ecosystem-governance` governance rule.
<!-- aiscr:ecosystem-end -->

This gathers the whole conversation — every comment including hidden ones, plus one hop of references and every hierarchy edge — and reports the description against the **declared issue shape**: which sections are present, missing, present but empty, which metadata rows are absent, and how much content the thread carries.
It exits non-zero when the issue is not ready.

**Do not restate readiness criteria here or in conversation.**
The shape is declared in `.agents/scripts/github/github_issues.py` and the report is its output; a second description of what "ready" means would drift from the first one.

### 2. When it is not ready, route back — do not fill the gap yourself

An unready issue is **not** promoted and **not** developed here.
Name the missing and empty sections, then hand the user to issue shaping:

> `Scope` and `Acceptance criteria` are missing.
> Run `/aiscr-plan-issue <ISSUE_NUMBER>` to develop them, then come back.

When `thread_has_content` is true, say so in the same breath — the gap is one shaping run away, not new thinking:

> The thread carries 12 comments; shaping absorbs them, so this is likely one run rather than new work.

Developing the description is `aiscr-plan-issue`, which already owns the explore stance that closes the gap; a second copy here would give one obligation two homes and blur elaborating an issue from planning it.
**Stop and let the user decide.**

### 3. Prepare the implementation branch — before any artifact is written

The change and the work implementing it share one branch and one review surface, so the branch comes **first**: artifacts written on the wrong branch must be moved by hand, and the final draft pull request would have nothing to open from.

Read this repository's `CONTRIBUTING.md` for the naming convention and base branch — both differ per repository, and the base is not always the default branch.
Propose the concrete name and base, and **wait for approval of that specific name** before creating or switching anything: a branch action is a git action and does not happen on your own initiative.

If the current branch is already right for this change, say so and stay on it.

### 4. Read what this repository's schema requires

The artifact set is the **repository's** decision, not this workflow's:

```bash
cat openspec/config.yaml
```

Take the declared schema and produce the artifact set that schema defines, following its own artifact instructions and any per-artifact `rules` the config declares.
Do not assume a schema, and do not import one from another repository.
Where this repository provides OpenSpec tooling, drive the artifacts through it; where it does not, write them directly under `openspec/changes/<slug>/` in the shape the schema prescribes.

**Check the posture before writing anything.**
Read this repository's declared OpenSpec posture from the `context:` content of its `openspec/config.yaml`.
If the posture is `none`, stop before writing any artifact and say which posture stopped the run: promotion writes an OpenSpec change here, and whether this repository keeps OpenSpec changes is an adoption decision taken deliberately, not settled on a promotion run's way past.

Do **not** edit the declared posture to unblock the run — re-declaring it bypasses the decision rather than making it; route the adoption question to the governance-bootstrap path that owns it and stop.
Creating an `openspec/` root by hand for the same purpose is the same bypass.

If this repository has no `openspec/` root at all, stop and say so: promotion has nowhere to land, and creating one is a repository decision outside this workflow.
The posture check catches a repository that has not adopted; this catches one whose declaration and tree disagree.

Shaping an issue carries no such precondition: it produces no OpenSpec artifact and is useful at any posture.
Only promotion is gated.

### 5. Seed the artifacts from the issue, not from scratch

The shape exists because promotion consumes it — map it rather than rewriting it:

| Issue section | Seeds |
| --- | --- |
| `Problem` | the change's rationale — why this is worth doing |
| `Scope` | scope, non-goals, and impact |
| `Acceptance criteria` | the spec scenarios |
| `Open questions` | the design record's open questions and decisions |
| the type block | the evidence design and tasks reason from |

Carry the evidence tiers across: a claim recorded as `inferred` or `reported` does not become a fact by being restated in a proposal, and a reporter hypothesis stays a hypothesis.

Cross-reference both ways — the change names the issue, and tell the user so the issue can be updated with the change slug.

### 6. Validate

Validate the artifacts with this repository's OpenSpec tooling first: a draft pull request over invalid artifacts advertises work that is not ready.

### 7. Commit on the branch, then open the draft pull request

Present the commit and the exact pull-request body, and get approval for **that content** before the remote write: pushing a branch and opening a pull request are outward-facing, and neither is quietly undone.
Before authoring the body, run `python .agents/scripts/github/github_issues.py prepare-handoff --workflow aiscr-plan-from-issue --run <run>`.
It creates `<HANDOFF_DIR>` (`.agents/local_scratch/aiscr-plan-from-issue/<run>/`) and its `POINTER.md` naming `.venv/.cache/aiscr-plan-from-issue/<run>/`.
Write the exact body to `<HANDOFF_DIR>/pr-body.md` and the approval view alongside it; keep the local bulk pointer outside posted bytes.
Placement classification is owned by `workflow/artefact-placement`.

```bash
python .agents/scripts/github/github_issues.py approval-view open-draft-pr <ISSUE_NUMBER> \
  --head <BRANCH> --base <BASE> --title "<TITLE>" \
  --body <HANDOFF_DIR>/pr-body.md --approval-view <HANDOFF_DIR>/draft-pr-approval.json

python .agents/scripts/github/github_issues.py open-draft-pr <ISSUE_NUMBER> \
  --head <BRANCH> --base <BASE> --title "<TITLE>" \
  --body <HANDOFF_DIR>/pr-body.md --mode interactive \
  --approved-digest <APPROVED_DIGEST> --approval-view <HANDOFF_DIR>/draft-pr-approval.json
```

The read-only `approval-view` writes the exact target and pull-request payload plus its canonical digest to the hand-off file.
Present that view, obtain approval of the digest, then pass the same value to `open-draft-pr`; any change to repository, branches, title, body, or draft flag causes the write to refuse.

The pull request is a **draft** because the work is planned, not done — a ready pull request invites review of an implementation that has not happened.
The body must reference the issue and must **not** carry an issue-closing keyword: promotion plans the work rather than resolving the issue, and a keyword would close it on merge.
The command refuses both mistakes, and a re-run cites the existing pull request for the branch rather than opening a second one.

### 8. Stop

Once all posting decisions are final and approved writes succeeded (or posting was declined), run `python .agents/scripts/github/github_issues.py cleanup-handoff --workflow aiscr-plan-from-issue --run <run> --kind draft-pr --approve`.
Retain the hand-off on validation, posting, or retry failure.
The write validates the exact approval file; editing it requires re-rendering and fresh approval.

State that the change is ready, name the next step, and **do not begin it.**
The draft pull request is where implementation will land, not a sign that it started.

### Execution using subagents

**Posture: declines.**
This workflow delegates nothing. `github_issues.py assess-readiness` gathers the thread and reports it against the declared shape.
What follows is authoring, branching, committing and opening a pull request, none of which is delegated.

The posture vocabulary, the default that governs a workflow declaring none, the declared return contracts, and the admission test are owned by `aiscr-quality-first-execution`.

<!-- aiscr:gen:id=guardrails -->

## Iron Law

**IRON LAW:** `NEVER TREAT ARTIFACT COMPLETION AS IMPLICIT APPROVAL TO IMPLEMENT.`

**IRON LAW:** `NEVER PROMOTE AN ISSUE THAT DOES NOT SATISFY THE DECLARED SHAPE.`

**IRON LAW:** `NEVER PROMOTE INTO A REPOSITORY THAT DOES NOT OWN THE ISSUE.`

No exceptions.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The issue is thin, but I can fill the gaps while writing the proposal." | Stop. Name the missing sections and route to `/aiscr-plan-issue`. |
| "I'll open a short explore stance to close the gap before promoting." | That stance belongs to `/aiscr-plan-issue` — one obligation, one home. |
| "The artifacts are complete, so I'll start on the tasks." | Stop. Completion is not approval; it needs a fresh instruction. |
| "The user approved promotion, so implementation is covered." | It is not — that approval is phase-local and ends at promotion. |
| "Another repository uses the governance-driven schema, so I'll use it whenever." | Read this repository's `openspec/config.yaml`. The schema is its decision. |
| "The issue body is thin but the thread is rich, so it is effectively ready." | Readiness is the body. Route to shaping, and say the thread will close it. |
| "The reporter's theory explains it, so I'll write it as the cause." | Carry the tier across. A hypothesis stays a hypothesis in the proposal. |
| "I'm in another repository, so I'll pass `--repo` to promote this issue from here." | Stop. The change belongs where the implementation happens. Open that checkout. |
| "I'll write the artifacts first, then sort out the branch." | Branch first. Artifacts on the wrong branch have to be moved by hand. |
| "`CONTRIBUTING.md` elsewhere says branch from `main`, so I'll do that." | Read *this* repository's. Base branches differ; some repos target `dev`. |
| "The change is complete, so I'll open a normal pull request." | Draft — the work is planned, not done. |
| "I'll add `Fixes #N` so the issue closes on merge." | No. Promotion plans the work; it does not resolve the issue. |
| "The draft PR is open, so I can start filling it in." | Stop. The draft is where implementation *will* land, not a start signal. |
| "The artifacts are complete, so I'll start on the tasks." | Stop. Completion is not approval; implementation needs a fresh instruction. |

## Verification before completion

Before claiming this workflow complete:

- [ ] The checkout is the repository that owns the issue; no foreign target promoted.
- [ ] Readiness assessed from the gathered conversation, not the body alone.
- [ ] An unready issue was routed to shaping with its missing sections named, not promoted.
- [ ] The branch name and base came from this repository's `CONTRIBUTING.md`, and the specific name was approved before creation.
- [ ] The branch existed before the first artifact.
- [ ] The artifact set came from this repository's declared schema in its own config.
- [ ] Every artifact was created under this repository's own OpenSpec root; no other repository written.
- [ ] Evidence tiers survived the mapping; no hypothesis became a fact.
- [ ] The change and issue reference each other.
- [ ] Validation ran and passed this session.
- [ ] The pull-request approval view was approved and its matching digest supplied; the pull request is a draft carrying no issue-closing keyword.
- [ ] The workflow stopped at the implementation boundary, naming the next step without starting it.

<!-- aiscr:endgen -->

## Governance

- GitHub references follow the delivered `aiscr-quality-first-execution` rule (*GitHub references*).
- Issues are the ideation layer where this workflow is enrolled; promotion enters OpenSpec, a phase boundary with its own approval.
- The change belongs to the repository that owns the issue, where the implementation happens.
  A run writes only that repository's OpenSpec root and nothing outside it.

<!-- aiscr:ecosystem-only -->

- A hub-cockpit run never writes management-hub paths or invokes hub-only commands; anything warranting hub adoption is prepared and stopped for a separate action.

<!-- aiscr:ecosystem-end -->

- Branch creation, commits, and the pull request are git and remote actions: each needs your direct instruction, and the branch convention belongs to the target repository's `CONTRIBUTING.md`, not this workflow.
- Readiness is mechanical, owned by `.agents/scripts/github/github_issues.py`; this body routes on its result rather than re-deciding.
- Deterministic engine: `.agents/scripts/github/github_issues.py`.

## Valid next steps

- `/openspec-apply-change <slug>` -- implement the promoted change, on your separate instruction
- `/aiscr-plan-issue <ISSUE_NUMBER>` -- develop the issue when readiness reported gaps
- End the session; the promoted change is the output

## Bundled scripts

The enrollment bundle installs these repository-local runtime scripts:

- `.agents/scripts/github/github_issues.py`
- `.agents/scripts/github/github_utils.py`
- `.agents/scripts/github/github_references.py`
- `.agents/scripts/lib/__init__.py`
- `.agents/scripts/lib/local_scratch_paths.py`
- `.agents/scripts/lib/log_utils.py`
- `.agents/scripts/lib/proc_utils.py`
- `.agents/scripts/lib/runtime_env.py`
