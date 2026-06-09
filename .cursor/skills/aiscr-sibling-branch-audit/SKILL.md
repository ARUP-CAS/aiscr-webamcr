---
name: aiscr-sibling-branch-audit
description: Audit local branches across sibling AIS CR repositories; fetch and prune
  remote-tracking refs locally, list detached or unpublished branches, produce a per-repo
  report. Never changes the remote.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-sibling-branch-audit.md -->

# aiscr-sibling-branch-audit

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Run a safe, read-only audit of local branches in sibling AIS CR repositories: fetch and prune remote-tracking refs (local only), list unpublished or upstream-gone branches, and produce a report.

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

1. `openspec/specs/sibling-branch-inventory/spec.md` — behavioral requirements and architecture
2. `AGENTS.md` — governance and scope
3. `.agents/canonical_configs/references/ecosystem_map.md` — list of sibling repos
4. `.agents/scripts/README.md` — script documentation and CLI reference

## Steps

1. Ask the user: repos-root path (default: `..`); optional `--stdout` or `--output` if they do not want the default scratch file.
2. Resolve repo list from `ecosystem_map.md`.
3. Run the audit script (default writes under `.agents/reports/local_sync_scratch/`):

   ```bash
   python .agents/scripts/sibling_repos_branch_audit.py --repos-root ..
   ```

   Or run manually per repo: `git fetch --prune` then `git branch -vv`.
4. List branches that are:
   - **Unpublished**: no upstream or not pushed to remote
   - **Upstream-gone**: remote branch was deleted
5. Present the per-repo report with branch name, reason, and last commit summary.
6. Ask user for follow-up decisions per branch: delete local, push to create remote, or keep.

## Iron Law

**IRON LAW:** `NEVER SWITCH, RESET, MERGE, OR MODIFY ANY BRANCH. THIS IS A READ-ONLY WORKFLOW. ALL FOLLOW-UP ACTIONS REQUIRE EXPLICIT PER-BRANCH USER CONFIRMATION.`

No exceptions. `git fetch --prune` updates local remote-tracking refs only; no branch state is changed.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The branch is clearly stale — I'll delete it while I'm here" | List only; every delete requires explicit per-branch confirmation from the user. |
| "The user said 'clean up' — I'll assume all gone branches should be deleted" | Present the list first; deletion requires confirmation per branch or per repo, even with a general cleanup request. |
| "git fetch --prune already ran — I can skip presenting the report" | Always present the full per-repo report before acting on any branch. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Audit run without modifying any branch or remote ref.
- [ ] Per-repo report presented to user before any follow-up actions.
- [ ] All branch deletions or pushes confirmed explicitly per branch; no batch destructive actions.
- [ ] No `git push` or `git push --delete` executed.

## Plan and workflow

_No backing plan file;_ follow fallback and governance.

**Registry fallback:** Load openspec/specs/sibling-branch-inventory/spec.md first for the durable behavioral contract; then run `python .agents/scripts/sibling_repos_branch_audit.py`; default report under `.agents/reports/local_sync_scratch/`; use `--stdout` or `--output` for custom location; never modifies remote.

## Governance

- **Never change the remote.** Only `git fetch` and local remote-tracking prune are allowed — no `git push`, no `git push --delete`.
- Any follow-up (delete local branch, push to create remote branch) requires **explicit user confirmation per branch or per repo**; never batch destructive or push actions automatically.
- Full workflow: See spec for requirements; use script directly for execution.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow