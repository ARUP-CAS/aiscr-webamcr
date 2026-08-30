---
name: aiscr-release-notes
description: Generate semantic, issue/PR-aligned release notes for a target AIS CR
  repository. Stores output in .agents/reports/release-notes/. Optionally updates
  the GitHub release body (opt-in, requires user approval).
disable-model-invocation: true
user-invocable: true
argument-hint: <repo>
---

<!-- aiscr:compiled=aiscr-release-notes -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.claude/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
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

## Embedded execution plan

### Plan: Release Notes Generation (Wiki format, reports-only)

> **OpenSpec migration:** Persistent behavioral requirements for this workflow now live in the workflow contract summarized in this compiled skill. This `.plan.md` file remains the reusable execution and governance layer for aiscr-management. See the identifiers and references stated in this workflow.

#### Context

AIS CR repositories under ARUP-CAS need consistent, user-friendly release notes for GitHub releases. In the **AIS CR ecosystem, issues are the main tracking tool**; release notes should be built **primarily from information gathered in the issues** (full description and discussion until closed), not only from issue titles or first comments. Manually maintained changelogs are often just commit lists; best practice is **semantic grouping** (Features, Bug fixes, Breaking changes, etc.) aligned with **issues and PRs**, not raw commits. This plan lives in `aiscr-management` and targets any AIS CR repo (webapp, api, data-app) that uses GitHub releases. Output must be **GitHub Wiki–compatible Markdown** but **stored only in reports** (e.g. `.agents/reports/release-notes/`); no direct push to the wiki—humans can copy to wiki or release body later.

#### Execution approach

- Discover releases/tags, existing release notes or wiki, `.github/release.yml` if present; **discover repo conventions** (CONTRIBUTING.md or similar) for commit format and issue-reference patterns (e.g. `Closes #N`, `(#N)`); identify default branch and tag range logic.
- Call GitHub API or `gh` to list releases (with pre-release flag), PRs merged in range, **commits in range**; for each PR fetch **body, labels, and comments**; fetch commit messages for the range; optional fetch of `.github/release.yml` and CONTRIBUTING (or linked docs) from target repo.
- **Parse** PR bodies, PR comments, and commit messages for issue references; resolve issue numbers via API; build enriched list (PR, commits, issues[], labels, inferred_commit_types[]); deduplicate. **Summarise each issue**: for each unique issue, fetch full issue body and **all comments** (GitHub API); produce a **concise summary of the whole issue until closed** (what was requested, decided, and done) for use as the release-note bullet text; do not use only the title or first comment.
- Review generated Markdown for clarity, correct grouping, deduplication, and wiki compatibility before saving to reports; flag ambiguous or uncategorised items.
- **Release body update (Step 5b, when user opted in):** Prefer `gh release edit <tag> --notes-file <path>` with `-R owner/repo` when running from a different repo. If the workstation has an optional GitHub-capable MCP or plugin (for example plugin-github) with an update-release tool, use it; otherwise rely on `gh` CLI. Ensure `gh auth status` succeeds for the target repo before attempting updates.

#### Steps

##### Step 1 — Gather input and choose scope

- **Target repo**: e.g. `ARUP-CAS/aiscr-webamcr` (or path/URL).
- **Mode**: (a) **Single release** (e.g. latest or a specific tag), (b) **Supplement missing** (generate notes for all past releases that have no notes, skipping pre-releases), or (c) **Date-range (repos without releases)**: when the target repo does not use GitHub Releases (e.g. aiscr-management), require a **start and end date** instead of tag/release; generation is on demand only. For date-range, if the user chooses **"from repository creation"** (or equivalent), **start date = date of the repository's first commit** (discovered at execution: use chronological order, e.g. `git log --reverse -1 --format=%ad --date=short` so the oldest commit by date is used, not the first by topological order), **end date = today** (inclusive). The range must include **all commits** from that start through end of end date; do not restrict to a single calendar day unless both dates coincide.
- **Output location**: `.agents/reports/release-notes/` in the repo where the plan is run (typically aiscr-management); file naming e.g. `<repo-short-name>_<tag>.md` or `release_notes_<repo>_<tag>_<date>.md`.
- **Push generated notes to GitHub release body?** (Only in **tag-based mode**; in date-range mode there are no GitHub releases to update, so this choice is skipped.)
  - **(A) No (default):** Report-only; do not call GitHub to update release body.
  - **(B) Yes:** After writing each report to `.agents/reports/release-notes/`, update the corresponding GitHub release body with that content (see Step 5b). Requires confirmation before the first update.
  - **Propagation scope** (when (B) is chosen): **(1) Single** — one tag only (user specifies, or the one release in single-release mode); **(2) Range** — only tags in [start_tag, end_tag] (user specifies start and end tag; only update releases that have a matching report file from this run); **(3) All** — every report file generated in this run (default when multiple).
- Confirm with the user: no push to wiki; output is report-only unless (B) was chosen.

##### Step 2 — Discover releases and config

- **`.github/release.yml` (GitHub Docs):** File location `.github/release.yml`. Required: `changelog.categories` (each entry: `title`, `labels`). Optional: `changelog.exclude.labels`, `changelog.exclude.authors` to filter bots/noise (e.g. dependabot). See [Automatically generated release notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes).
- **If target uses GitHub Releases:** List releases for the target repo (`gh release list` or GitHub API); if mode is "supplement missing", filter to releases that have no release body (or no wiki page) and **exclude pre-releases**. If present, fetch `.github/release.yml` from the target repo and derive label→category mapping (`changelog.categories`). If absent, use a default set (e.g. Breaking changes, Features, Bug fixes, Other / maintenance).
- **If target does not use releases (date-range mode, e.g. aiscr-management):** Skip listing releases/tags; skip fetching `.github/release.yml` from the target (use default categories only). The range is defined by the start and end date gathered in Step 1.

##### Step 3 — For each release, collect PRs, commits, and issues

- **3a. Define range and fetch PRs and commits**
  - **Tag-based mode:** For the release tag, determine the previous tag (or base branch) to define the range. List **PRs merged** in that range and **commits** in that range (e.g. `gh pr list --state merged --base …` and `gh api` or `git log` for commit list). If the repo is available locally (e.g. sibling path), `git log prev_tag..tag --oneline` can supplement.
  - **Date-range mode (repos without releases, "mimic mode"):** Use the start and end date from Step 1. The range is inclusive: all commits with commit date (or author date) on or after start and on or before end must be included. Use e.g. `git log --since="<start_date>" --until="<end_date + 1 day>"` so that the entire span is covered. List **merged PRs** whose merge date falls in the range. **Treat each calendar day in the range as a separate release:** group commits by commit date (or author date) and PRs by merge date into per-day buckets; only days with at least one commit or one merged PR get an output file. For each such day, run the rest of Step 3 (enrich, parse issue refs, summarise issues, build grouping input) for that day's entries only.

- **3b. Enrich each PR and the commit set**
  - For each merged PR: get **body**, **labels**, and **comments** (GitHub API or `gh pr view` / `gh api repos/…/issues/…/comments`).
  - For commits in range (optionally per-PR or whole range): get **commit message** (subject + body). Prefer API so issue refs in commit body are not missed.

- **3c. Discover repo convention for issue refs**
  - If the target repo is accessible (clone or API), fetch **CONTRIBUTING.md** (or linked docs) and detect documented patterns (e.g. "Closes #N", "Refs #N", "(#N) in commit message"). Use this to prioritise regex patterns and to interpret commit prefix for Step 4.

- **3d. Parse issue references**
  - From PR bodies, PR comments, and commit messages, extract **issue numbers** using a set of patterns: `#(\d+)`, `Closes\s*#(\d+)`, `Refs\s*#(\d+)`, `\(#(\d+)\)`, `[Ff]ixes?\s*#(\d+)`, `[Ii]ssue\s*(\d+)`, and similar. Normalise to a list of unique issue numbers per PR and per commit.
  - For each unique issue number, **resolve to issue metadata** (GitHub API: title, state). Build a list: `(PR?, commit?, issues[], labels, commit_prefix?)` for grouping. If a commit has no PR, treat it as a standalone entry with commit message and any parsed issue refs.

- **3e. Summarise each issue**
  - For each **unique issue** in scope: fetch the **full issue** (description + **all comments**, timeline until closed) via GitHub API or `gh issue view`.
  - From the full thread, produce a **concise summary of the whole issue until closed** (what was requested, decided, and done), suitable for a single release-note bullet (one or two sentences). Do not use only the issue title or first comment.
  - Attach this **issue summary** to each entry that references that issue, for use in Step 4c.

- **3f. Build grouping input**
  - Produce a unified list of **entries**: each entry is either (PR + issues + labels + issue_summaries) or (commit + issues + commit_prefix when present + issue_summaries when available). Attach inferred commit type (e.g. `feat`, `fix`, `docs`) when the repo convention uses a prefix like `[feat]` and it was discovered in 3c.

##### Step 4 — Group by semantics and draft notes

- **Date-range (mimic) mode:** Repeat steps 4a–4d **for each day** that has activity (commits or merged PRs); produce one draft per day.
- **4a. Define category mapping**
  - **First:** Use label→category from `.github/release.yml` if present.
  - **Else:** Use default mapping (Breaking changes, Features, Bug fixes, Other).
  - **Fallback for entries without labels:** If repo convention was discovered (e.g. commit prefix `[feat]`, `[fix]`, `[docs]`), map: `feat` → Features, `fix` → Bug fixes, `docs`/`chore`/`style`/`refactor`/`perf`/`test` → Other (or a "Maintenance" category if desired). If no prefix, put in Other.

- **4b. Group entries**
  - Group all entries (PR-based and commit-only) by the chosen category. **Deduplicate**: if the same issue appears in multiple PRs/commits, list it once under the most appropriate category (e.g. prefer the PR that "Closes" it; or the first occurrence).

- **4c. Draft bullet text**
  - For each entry: prefer **issue summary** (from Step 3e, summary of the whole issue until closed) when available; otherwise **issue title**. Always link to the issue (and to PR if useful). If no issue, use **PR title** and link to PR. If commit-only (no PR, no issue), use **first line of commit message** and link to commit (or omit if too noisy; document in Notes that "commit-only" entries can be included or filtered by user preference). Do not use only the issue title or first comment when a full-issue summary was produced.
  - Produce one Markdown section per category (e.g. "## Breaking changes", "## Features", "## Bug fixes", "## Other"). Ensure GFM and wiki-compatible syntax. **For date-range (mimic) mode:** use **Czech** for section headings, boilerplate, **and individual bullet/note text** in the generated report: section headings "## Změny breaking", "## Nové funkce", "## Opravy chyb", "## Ostatní"; "(žádné)" when empty; footer e.g. "Vygenerováno plánem release-notes. Výstup pouze do reportů; kopírování na wiki nebo do release je ruční." For each bullet, write the descriptive title/summary in **Czech** (translate or briefly summarize the commit/PR in Czech); keep the link to commit/PR unchanged.

- **4d. Review**
  - Review the draft: check for duplicate bullets, wrong category, broken links, and clarity; suggest moving items between categories or merging duplicates.

##### Step 5 — Write to reports only

- **Tag-based mode:** Save the generated content to `.agents/reports/release-notes/<repo>_<tag>.md` (or agreed naming).
- **Date-range mode (mimic mode):** Save **one file per day** that has activity: `.agents/reports/release-notes/<repo>_YYYY-MM-DD.md` (e.g. `aiscr-management_2025-05-13.md`, `aiscr-management_2026-03-14.md`). Only days with at least one commit or one merged PR in the range get a file; skip days with no activity. When generating date-based filenames or the "today" / end date, use the output of a deterministic command (e.g. `python -c "import datetime; print(datetime.date.today().isoformat())"`), not an inferred date. Use **Czech** for section headings, boilerplate, **and individual bullet/note text** in these report files (Změny breaking, Nové funkce, Opravy chyb, Ostatní; žádné; footer; each bullet description in Czech).
- Create the directory if missing. Do **not** call GitHub API to update release body or wiki unless the user opted in (Step 5b).

##### Step 5b — Optionally update GitHub release body (tag-based, user opt-in)

- **When:** User chose "Yes" to push to release body in Step 1 **and** mode is tag-based (single release or supplement missing). Skip in date-range (mimic) mode.
- **Scope:** The propagation scope (single / range / all) gathered in Step 1 determines which generated reports are used to update release bodies. For **single**: only the one tag (user-specified or the single release). For **range**: filter report files by tag so that only releases with tag in [start_tag, end_tag] are updated (only reports from this run). For **all**: every report file generated in this run. List which tags will be updated and confirm once before the first update.
- **How:** For each report file in scope that corresponds to a release tag (e.g. `<repo>_<tag>.md`), set the GitHub release body to the report content.
  - **Preferred:** `gh release edit <tag> --notes-file <path>` with `-R owner/repo` when running from another repo (e.g. aiscr-management). Ensure `gh auth status` succeeds for the target repo; if not authenticated, warn and skip (or list the releases that would have been updated).
  - **Alternative:** If an optional GitHub-capable MCP or plugin exposes an "update release" / "edit release" tool, use it when available; either `gh` or that tool is acceptable.
- **Safety:** Do not overwrite release body without the user having chosen (B) in Step 1. Confirm once before the first update (e.g. "Update N release(s) in repo X? (y/N)").

##### Step 6 — Propagate `.github/release.yml`

- **Tag-based mode:** **Always** produce a recommended `.github/release.yml` that reflects the categories and label mapping used for this run (from the target repo's existing file, or the default set). Save it to `.agents/reports/release-notes/<repo>_release.yml` (or `<repo>_release_yml_recommended.yml`) so the user can copy it into the target repo's `.github/` if desired. **Optionally (with explicit user approval):** If the user requests propagation to the target repo and the plan is run with write access to that repo, create or update `.github/release.yml` in the target repo so that GitHub's automatically generated release notes and future runs of this plan use the same categories. Do not overwrite the target file without confirmation if it already exists and has customisations.
- **Date-range mode (repos without releases):** **Always** produce the recommended `.github/release.yml` and save it to `.agents/reports/release-notes/<repo>_release.yml`. **Also populate the target repo:** create or update `.github/release.yml` in the target repo (create `.github/` if missing) so the repo has a canonical categories file for consistency and future runs. If `.github/release.yml` already exists and contains customisations, do not overwrite without user approval; otherwise write the recommended file. **Language:** Keep `.github/release.yml` in **English** (category titles and comments) for GitHub and tooling. The report copy in `.agents/reports/release-notes/` may use **Czech** comments; keep `title` values in English to match the repo file.

##### Step 7 — Validate and hand off

- Validate: file exists under `.agents/reports/release-notes/`, Markdown is valid, links point to the target repo's issues/PRs. Run `validate_release_yml.py` (structure and populated content); optionally `--check-git-count` for date-based reports (sanity check: activity that day ⇒ at least one note).
- Confirm recommended `.github/release.yml` is present in reports (e.g. `<repo>_release.yml`); for tag-based mode if propagation was approved, or for date-range mode by default, confirm `.github/release.yml` in the target repo exists or was updated.
- Document in the plan or in a short report note that copying to wiki is **manual** if the user wants it; release body was updated only when the user opted in (Step 5b).

#### Validation

- Generated file(s) exist under `.agents/reports/release-notes/` with the agreed naming. For date-range (mimic) mode: one file per day with activity, `<repo>_YYYY-MM-DD.md`.
- Recommended `.github/release.yml` exists under `.agents/reports/release-notes/` (e.g. `<repo>_release.yml`); for tag-based mode if propagation was approved, or for date-range mode by default, the target repo's `.github/release.yml` is present and consistent with the categories used.
- Content is semantic (grouped by type); bullets are based primarily on **issue summaries** (full issue until closed) when available, with links to issues and PRs; does not rely on raw commit lists or only issue titles for user-facing bullets.
- When "supplement missing" was used: only non–pre-releases were processed.
- If user opted in to push to release body, only the releases in the chosen propagation scope (single / range / all) were updated via `gh release edit` or an optional GitHub-capable MCP/plugin; otherwise no release body was modified.
- No automation in this plan pushes to GitHub Wiki or updates release body **unless the user explicitly opted in** (Step 5b). For tag-based mode, writing `.github/release.yml` to the target repo is with explicit user approval; for date-range mode, the plan populates `.github/release.yml` in the target repo by default (do not overwrite existing customisations without approval).
- Optional: run a quick link check or a review pass on the generated Markdown.
- Optional: run `validate_release_yml.py --check-git-count` for a sanity check (if there were commits that day, the report should have at least one note; no tight commit-to-note count alignment).

#### Notes / Adaptation per repo

- **Repos without GitHub Releases (e.g. aiscr-management, "mimic mode"):** This repo does not use GitHub Releases. Use **date-range mode** with **individual days as releases**: scope by start and end date (when the user chooses "from repository creation", use first-commit date as start and today as end); collect all commits and merged PRs in that range, then **group by calendar day**; produce **one release notes file per day** that has activity, naming `<repo>_YYYY-MM-DD.md` (e.g. `aiscr-management_2026-03-14.md`). Same semantic grouping and output path; on demand only. Skip release/tag discovery. **Language:** `.github/release.yml` in the repo stays in **English**; generated report files under `.agents/reports/release-notes/` (markdown and README) use **Czech** for section headers and explanatory text. **Populate `.github/release.yml`** in the target repo (create `.github/` if missing); also save the recommended file to reports (Czech comments allowed there). See `AGENTS.md` and `mgmt-repo-operating-basics.md` when running in aiscr-management.
- **Webapps** (e.g. `aiscr-webamcr`, `aiscr-digiarchiv-2`): often have more PRs per release; ensure categories stay readable (collapse "Other" if large).
- **API/docs** (e.g. `aiscr-api-home`): may have fewer releases; "supplement missing" can fill historical gaps.
- **Label convention**: If a repo does not use `.github/release.yml`, document the default category mapping in the plan or in a small table in `.agents/reports/` so maintainers can add labels later for better grouping. The propagation step (Step 6) always writes a recommended `.github/release.yml` to reports so the user can copy it into the target repo; optionally propagate directly to the target repo with user approval.
- **Commit and issue-ref conventions:** For repos like aiscr-webamcr with CONTRIBUTING that define commit format (`[typ] desc (#N)`) and PR issue links (`Closes #N`, `Refs #N`), Step 3 should fetch CONTRIBUTING (or linked docs) and use it to drive parsing and Step 4 fallback mapping. When conventions are missing or inconsistent, rely on generic patterns and default categories.
- **Issues as primary source:** In AIS CR, issues are the main tracking tool; Step 3e (summarise each issue) must fetch the full issue thread and produce a summary of the whole issue until closed. Do not fall back to title-only or first-comment-only when the full thread is available.

#### Options (planning phase)

**Delivery (choose before any commit or push):**

- **(A)** Create a branch and open a **draft** PR for the new plan file and any prompt/script additions (recommended).
- **(B)** Create a branch only (no PR).
- **(C)** Local changes only (no branch, no push).

**Scope / target:** Confirm with the user which repo and which mode (single release, supplement missing, or date-range for repos without releases) before running. Do not assume from context.

**Partial execution:** User may restrict to a single release or a subset of tags when supplementing; document the choice before generating.

**Propagation to target repo:** Writing `.github/release.yml` into the target repo's `.github/` is optional. Obtain explicit user approval before creating or updating that file in the target repo. If the user also explicitly requests git delivery, state which branch will be used in the target repo and obtain user confirmation before any branch creation, staging, commit, push, or PR step.

**Push to release body:** Ask the user whether to update the GitHub release body (tag-based mode only). Default: no. When yes, also ask propagation scope (single / range / all) and for range the start and end tag. Use `gh release edit <tag> --notes-file <file>` with `-R owner/repo` (or an optional GitHub update-release MCP/plugin if the operator configured one); require authentication and one-time confirmation before running updates.

Do not commit or push until the user has chosen.

#### Plan refinement / Autoupdate

- After use: refine category defaults or label mappings if repos consistently use different labels; add a short "Release notes conventions" subsection to `.agents/reports/` or to this plan if useful.
- Keep the plan repo-agnostic; put repo-specific examples (e.g. "for aiscr-webamcr") in Notes / Adaptation per repo or in reports.
- If a dedicated prompt (e.g. `.agents/prompts/release_notes_generation.md`) is added later, link it here and in the skillset mapping.
