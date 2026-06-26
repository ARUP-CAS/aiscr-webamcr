---
name: aiscr-release-notes
description: Generate semantic, issue/PR-aligned release notes for a target AIS CR
  repository. Stores output in .agents/reports/release-notes/. Optionally updates
  the GitHub release body (opt-in, requires user approval).
---

<!-- aiscr:compiled=aiscr-release-notes -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.github/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-release-notes — generate release notes

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

1. the workflow contract summarized in this compiled skill — behavioral requirements for release documentation
2. `AGENTS.md` — governance and scope
3. `.agents/README.md` — structure of `.agents/`
4. the embedded execution plan below — execution procedures and operator runbook

## Steps

1. Ask the user:
   - **Target repo** (e.g. `aiscr-webamcr`, `aiscr-digiarchiv-2`)
   - **Mode**: single release (tag), date-range, or backfill missing past releases (skip pre-releases)
   - **Optional**: update GitHub release body after generating? (opt-in; requires `gh` CLI by default; optional GitHub-capable MCP/plugin only when the operator added one)

2. Establish ecosystem context: the target repo's path and tech stack (the repository this workflow runs in).

3. Collect sources using `gh` CLI by default; if an optional GitHub-capable MCP or plugin is available on the workstation, it may be used instead for the same GitHub API operations:
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

<!-- aiscr:gen:id=guardrails -->
## Iron Law

**IRON LAW:** `NEVER PUSH RELEASE NOTES TO GITHUB (gh release edit) WITHOUT FIRST PRESENTING THE GENERATED CONTENT TO THE USER AND RECEIVING EXPLICIT PER-RELEASE APPROVAL.`

No exceptions. Publishing release notes is a public-facing action that cannot be undone silently.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The notes look good — I'll just push them" | Present the generated Markdown to the user first; wait for explicit approval. |
| "The user asked for backfill — I'll push all at once" | Get per-release approval; never batch-push without explicit confirmation. |
| "gh release edit is reversible" | Still requires user preview and approval before running. |
<!-- aiscr:endgen -->

## Verification before completion

Before claiming this workflow complete, confirm:

- [ ] Generated release notes were presented to user before any `gh release edit` call.
- [ ] Per-release explicit approval obtained for each updated GitHub release body.
- [ ] Output files exist under `.agents/reports/release-notes/` with correct naming.
- [ ] `.github/release.yml` conventions followed (label grouping, bot exclusion).

## Governance

- Output is stored in `.agents/reports/release-notes/` only by default; no wiki push is automatic.
- Updating GitHub release body requires explicit user approval per release.
- Follow `.github/release.yml` conventions (exclude bots, assign labels).
- Requirement authority: the workflow contract summarized in this compiled skill
- Execution runbook: the embedded execution plan below

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- Read the identifiers and references stated in this workflow and follow the **Usage** section before loading a different workflow's context.
