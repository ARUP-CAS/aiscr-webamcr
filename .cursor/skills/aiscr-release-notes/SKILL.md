---
name: aiscr-release-notes
description: Generate semantic, issue/PR-aligned release notes for a target AIS CR
  repository. Stores output in .agents/reports/release-notes/. Optionally updates
  the GitHub release body (opt-in, requires user approval).
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-release-notes.md -->

# aiscr-release-notes

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Generate semantic, issue/PR-aligned release notes for a target AIS CR repository in GitHub Wiki-compatible Markdown.

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

1. `openspec/specs/release-documentation/spec.md` — behavioral requirements for release documentation
2. `AGENTS.md` — governance and scope
3. `.agents/README.md` — structure of `.agents/`
4. `.agents/plans/release-notes.plan.md` — execution procedures and operator runbook

## Steps

1. Ask the user:
   - **Target repo** (e.g. `aiscr-webamcr`, `aiscr-digiarchiv-2`)
   - **Mode**: single release (tag), date-range, or backfill missing past releases (skip pre-releases)
   - **Optional**: update GitHub release body after generating? (opt-in; requires `gh` CLI or GitHub MCP)

2. Load ecosystem context: read `.agents/canonical_configs/references/ecosystem_map.md` for the target repo's path and tech stack.

3. Collect sources using `gh` CLI or GitHub MCP:
   - Issues (full thread for context)
   - Pull requests merged in scope
   - Commits in scope

4. Generate release notes following the plan:
   - Group by feature / fix / chore
   - Reference issue/PR numbers
   - Use GitHub Wiki-compatible Markdown

5. Write output to:

   ```text
   .agents/reports/release-notes/<repo>-<tag-or-date>.md
   ```

   Use today's date for the filename if date-range mode:

   ```bash
   python -c "import datetime; print(datetime.date.today().isoformat())"
   ```

6. Present to user. If they approved updating the GitHub release body, run:

   ```bash
   gh release edit <tag> --repo <owner>/<repo> --notes-file <output-file>
   ```

   Only with explicit user approval.

## Iron Law

**IRON LAW:** `NEVER PUSH RELEASE NOTES TO GITHUB (gh release edit) WITHOUT FIRST PRESENTING THE GENERATED CONTENT TO THE USER AND RECEIVING EXPLICIT PER-RELEASE APPROVAL.`

No exceptions. Publishing release notes is a public-facing action that cannot be undone silently.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The notes look good — I'll just push them" | Present the generated Markdown to the user first; wait for explicit approval. |
| "The user asked for backfill — I'll push all at once" | Get per-release approval; never batch-push without explicit confirmation. |
| "gh release edit is reversible" | Still requires user preview and approval before running. |

## Verification before completion

Before claiming this workflow complete, confirm:

- [ ] Generated release notes were presented to user before any `gh release edit` call.
- [ ] Per-release explicit approval obtained for each updated GitHub release body.
- [ ] Output files exist under `.agents/reports/release-notes/` with correct naming.
- [ ] `.github/release.yml` conventions followed (label grouping, bot exclusion).

## Plan and workflow

`.agents/plans/release-notes.plan.md`

**Registry fallback:** Load openspec/specs/release-documentation/spec.md first for the durable behavioral contract; gather target repo, mode (single release vs supplement missing vs date-range), and output scope; discover releases and `.github/release.yml` config; collect PRs, commits, and linked issues per release; group by semantic categories; write to `.agents/reports/release-notes/`; optionally push to GitHub release body with user approval and propagation scope (single/range/all).

## Governance

- Output is stored in `.agents/reports/release-notes/` only by default; no wiki push is automatic.
- Updating GitHub release body requires explicit user approval per release.
- Follow `.github/release.yml` conventions (exclude bots, assign labels).
- Requirement authority: `openspec/specs/release-documentation/spec.md`
- Execution runbook: `.agents/plans/release-notes.plan.md`

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow