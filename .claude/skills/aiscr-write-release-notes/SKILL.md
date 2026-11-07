---
name: aiscr-write-release-notes
description: Use when the user asks to generate or revise semantic, issue/PR-aligned
  release notes for an AIS CR repository. Store them under .agents/reports/release-notes/;
  updating the GitHub release body requires explicit approval.
argument-hint: <repo>
license: CC-BY-4.0
author: AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
---

<!-- SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- aiscr:compiled=aiscr-write-release-notes -->
<!-- delivery-version: b257a1a89279be5e17cda3c133aa77b8c4d2706c 2026-11-07T11:18:12+01:00 -->

<!-- aiscr:entry-scope -->

**Entry scope (compiled)**

- This `.claude/skills/` skill is self-contained; use the workflow body below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-write-release-notes — generate release notes

Generate semantic, issue/PR-aligned release notes for a target AIS CR repository in GitHub Wiki-compatible Markdown.

## Phase awareness

This is an **operational execution skill**: its subject is release notes prepared from issue, PR, and release context, not spec-governed repository state.
It runs without gating on OpenSpec context and never invokes `/openspec-propose`.
Execution boundaries: prepare the release notes only; do not tag, publish, or
cut the release, and do not create new OpenSpec changes or promote backlog items.

## Context to load first

1. `AGENTS.md` — governance and scope

Use the repository's Python environment with PyYAML installed for the bundled `.agents/scripts/validate_release_yml.py` validator.
Its `lib/log_utils.py` and `lib/proc_utils.py` helpers are bundled with it.
Resolve report paths from the invoking checkout, separately from the target repository's release configuration.

## Steps

### Context

Repositories that publish GitHub releases need consistent, user-friendly release notes.
Issues are the main tracking tool; release notes should be built **primarily from information gathered in the issues** (full description and discussion until closed), not only from issue titles or first comments.
Best practice is **semantic grouping** (Features, Bug fixes, Breaking changes, etc.) aligned with **issues and PRs**, not raw commits.
This workflow targets any repository that uses GitHub releases (webapp, service, docs site, plugin).
The operator names the target repo without a new argument.
The generated notes are **reports in the invoking checkout** (see *Output location* below); the release body and `.github/release.yml` are writes into the target and need its branch stated and confirmed first.
Output must be **GitHub Wiki–compatible Markdown** but **stored only in reports** (e.g. `.agents/reports/release-notes/`); no direct push to the wiki.

<!-- aiscr:ecosystem-only -->
In the AIS CR ecosystem, repositories under ARUP-CAS — webapps, services, docs sites and plugins — need consistent, user-friendly release notes for GitHub releases.
<!-- aiscr:ecosystem-end -->

<!-- aiscr:ecosystem-only -->
Both execution tiers apply, with semantics defined under *Workflow execution tiers* in the `aiscr-ecosystem-governance` governance rule; the hub-cockpit tier is the common one here.
In the hub-cockpit tier, every read of the target repository's tree — tags, log ranges, `.github/release.yml`, conventions — is acquired through a sanctioned sibling read route (the native route where the product's control row records a grant, otherwise the sibling bridge) or the GitHub API, never by a route the product's control row does not record.
<!-- aiscr:ecosystem-end -->

Tag-based runs emit **two** report files: a **publishable** body (`<repo>_<tag>.md`) and a **working-notes** companion (`<repo>_<tag>.working.md`); only the publishable file may be published.

### Execution approach

- Discover releases/tags, existing notes/wiki, and `.github/release.yml`; **discover repo conventions** (CONTRIBUTING.md) for commit format and issue-reference patterns (e.g.
  `Closes #N`, `(#N)`); identify default branch and tag range logic.
  Distinguish **git tag** from **GitHub Release object**.
- Call GitHub API or `gh` to list releases (with pre-release flag), PRs merged in range, **commits in range**; for each PR fetch **body, labels, and comments**; fetch commit messages for the range; optional fetch of `.github/release.yml` and CONTRIBUTING (or linked docs) from target repo.
- **Parse** PR bodies, PR comments, and commit messages for `#N` references; **classify each number as issue vs pull request** via API before summarizing; build enriched list; deduplicate.
  **Summarise each issue**: fetch the full body and **all comments**; produce a **concise summary of the whole issue until closed**.
- Inventory **dependency / maintenance bumps** in the range and collapse to final versions by group; run a **gap check** against the git range.
- Draft **publishable** and **working** Markdown separately; review, flag ambiguous items before saving.
- **Release body update (Step 5b, when user opted in):** Prefer `gh release edit <tag> --notes-file <path>` with `-R owner/repo` from another repo.
  The notes file MUST be the **publishable** path only (never `*.working.md`).
  Require a GitHub Release object for the tag and `gh auth status` success before updating.

### Procedure

#### Step 1 — Gather input and choose scope

- **Target repo**: e.g. `owner/repo` (or path/URL).

<!-- aiscr:ecosystem-only -->
In the AIS CR ecosystem, for example `ARUP-CAS/aiscr-webamcr`.
<!-- aiscr:ecosystem-end -->

- **Mode**: (a) **Single release** (e.g. latest or a specific tag), (b) **Supplement missing** (generate notes for all past releases that have no notes, skipping pre-releases), or (c) **Date-range (repos without releases)**: when the target repo does not use GitHub Releases, require a **start and end date** instead of tag/release; generation is on demand only.
  For date-range, if the user chooses **"from repository creation"** (or equivalent), **start date = date of the repository's first commit** (discovered at execution: use chronological order, e.g. `git log --reverse -1 --format=%ad --date=short` so the oldest commit by date is used, not the first by topological order), **end date = today** (inclusive).
  The range must include **all commits** from that start through end of end date; do not restrict to a single calendar day unless both dates coincide.
- **Partial execution**: the user may restrict supplement mode to one release or an explicit subset of tags; record that boundary before collection.
- **Scope source** (tag-based): milestone / git-range / **both merge+dedupe**; default to both when a milestone **and** a tag are named, unless overridden.
- **Semver milestone signal:** If a scoped milestone **title** matches semver (`v1.4.0`, `1.4.0`, optional pre-release suffix such as `-rc2`), treat it as a **release-identity hint** and default to **previous published non-pre-release tag (or previous GitHub Release) → this tag/Release** (e.g. `v1.3.2..v1.4.0-rc2`), combined with milestone issues (merge+dedupe) unless overridden; confirm `prev..target` with the user.
- **Language** (tag-based and date-range): Czech vs English for section headings and bullet prose.
  Ask for tag-based runs too (date-range defaults to Czech).
- **Open milestone issues:** treat as shipped with prod follow-up in **working notes** / omit / main-body deferred — **ask** (default: ask).
- **RC vs production filename** when drafting ahead of the final tag (e.g. write as `…_v1.4.0.md` while the tip tag is still `v1.4.0-rc2`).
- **Dependency coverage:** include collapsed deps in the publishable file when bumps exist (**default: yes**).
- **Output location**: `.agents/reports/release-notes/` in the run repo.
  Tag-based: publishable `<repo-short-name>_<tag>.md` plus companion `<repo-short-name>_<tag>.working.md`.
  Date-range: `<repo>_YYYY-MM-DD.md` (publishable only; no working companion).
- **Push generated notes to GitHub release body?**
  (Only in **tag-based mode**; skipped in date-range mode, which has no releases to update.)
  - **(A) No (default):** report-only; do not update the release body.
  - **(B) Yes:** after writing reports, update the corresponding GitHub release body from the **publishable** file only (see Step 5b); confirmation required before the first update.
  - **Propagation scope** (when (B) is chosen): **(1) Single** (one tag), **(2) Range** ([start_tag, end_tag]), **(3) All** (every publishable report this run).
- Confirm with the user: no wiki push; report-only unless (B); working companion not published.

#### Step 2 — Discover releases and config

- **`.github/release.yml` (GitHub Docs):** File location `.github/release.yml`.
  Required: `changelog.categories` (each entry: `title`, `labels`); optional: `changelog.exclude.labels`, `changelog.exclude.authors` for bots/noise.
  See [Automatically generated release notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes).
  Excluding `dependencies` from GitHub **auto**-notes does **not** mean curated publishable notes omit dependency coverage — they still get a collapsed deps subsection when bumps exist.
- **If target uses GitHub Releases / tags:** List releases (`gh release list` or API).
  Distinguish **git tag** vs **Release object** with `gh api repos/…/releases/tags/<tag>` (404 ⇒ tag may exist without a Release; report generation proceeds; Step 5b blocked until a Release exists).
  For "supplement missing", filter to releases with no body and **exclude pre-releases**.
  Fetch `.github/release.yml` for the label→category mapping, else use a default set (Breaking changes, Features, Bug fixes, Other / maintenance).
- **Previous baseline:** prefer the last **published non-pre-release** Release/tag before the target; state `prev..target` when confirming Step 1.
- **Local clone (in-repo tier):** `git fetch --tags` (or the specific tags) before `git log prev..tag`; peel annotated tags to the commit.
  Where no local clone is available for an operation this step names (fetching tags, full log ranges), the operation is reported as a route gap and the GitHub API path above remains the source.

<!-- aiscr:ecosystem-only -->

- **Hub-cockpit tier:** the sibling's clone is reached through a sanctioned sibling read route — the native route where the product's control row records a grant (for Kilo, the shell's working directory set to the sibling), otherwise the bridge, for example `python .agents/scripts/sibling/sibling_git_read.py --repo <REPO_NAME> -- rev-list --count <prev>..<tag>` for a range count.
  Where no route exposes an entry point for an operation this step names, the operation is reported as a route gap and the GitHub API path above remains the source; a `git` invocation is composed only inside a granted root or through the bridge.

<!-- aiscr:ecosystem-end -->

- **If target does not use releases (date-range mode):** Skip listing releases/tags; skip fetching `.github/release.yml` from the target (use default categories only).
  The range is defined by the start and end date gathered in Step 1.

#### Step 3 — For each release, collect PRs, commits, and issues

- **3a.
  Define range and fetch PRs and commits**
  - **Tag-based mode:** For the release tag, use the confirmed previous baseline to define the range.
    List **PRs merged** and **commits** in that range.
    In the in-repo tier, `git log prev_tag..tag` supplements after tags are fetched; where no local clone is exposed, the GitHub API provides the commit list.
  - **Milestone enrichment:** If a milestone is scoped, fetch its items and **split** issues vs PRs (`pull_request` key on REST issue objects, or GraphQL); GitHub UI "closed" counts include **both**, so do not treat that number as the issue count.
    When the title is semver-shaped, **default** to milestone issues **plus** commits/PRs in `prev_release..this_tag` (not milestone-only).
  - **Date-range mode (repos without releases, "mimic mode"):** Use the start and end date from Step 1.
    The range is inclusive.
    List **merged PRs** whose merge date falls in the range.
    **Treat each calendar day in the range as a separate release:** group commits and PRs into per-day buckets; only days with activity get an output file.
- **3b.
  Enrich each PR and the commit set**
  - For each merged PR: get **body**, **labels**, and **comments**.
  - For commits in range: get **commit message** (subject + body).
    Prefer API so issue refs in commit body are not missed.
- **3c.
  Discover repo convention for issue refs**
  - Fetch **CONTRIBUTING.md** (or linked docs) when accessible; detect patterns (e.g.
    "Closes #N", "Refs #N", "(#N) in commit message") and commit prefixes for Step 4.
- **3d.
  Parse and classify `#N` references**
  - Extract numbers using patterns: `#(\d+)`, `Closes\s*#(\d+)`, `Refs\s*#(\d+)`, `\(#(\d+)\)`, `[Ff]ixes?\s*#(\d+)`, `[Ii]ssue\s*(\d+)`, and similar.
  - For each unique number, **resolve via API** whether it is an **issue** or a **pull request** (shared number space); do **not** invent “extra issues” from PR numbers.
  - Build grouping entries only from **issues** (plus PRs that close/ref them); commits with no issue may be standalone or noise.
- **3e.
  Summarise each issue**
  - For each **unique issue**: fetch the **full issue** (description + **all comments**) via API or `gh issue view`.
  - Produce a **concise summary of the whole issue until closed** (requested, decided, done), not only the title or first comment.
  - Attach this **issue summary** for Step 4c.
- **3f.
  Build grouping input**
  - Produce a unified **entries** list: (PR + issues + labels + issue_summaries) or (commit + issues + commit_prefix + issue_summaries); attach inferred commit type when the repo uses prefixes like `[feat]`.
- **3g.
  Dependency / maintenance inventory**
  - Collect Dependabot / label `dependencies` / subject `Bump …` / explicit framework bumps from range commits and merged PRs.
  - Collapse to **final version per package** (oldest→newest, last wins); group: Python / Docker-runtime / observability / Actions-pre-commit (adjust to the repo's stack).
  - **Skip noise:** `chore: … pre-commit … licenses`, `CITATION.cff`, pure `main`↔`test` merges.
- **3h.
  Gap check**
  - Classify range commits into: milestone/issue-covered / deps / chore-noise / other.
  - If **other** remains non-trivial, flag it before drafting or fold into Ostatní / Other (detail in the working companion).

#### Step 4 — Group by semantics and draft notes

- **Date-range (mimic) mode:** Repeat steps 4a–4d **for each day** with activity; produce one **publishable** draft per day (no `.working.md`).
- **4a.
  Define category mapping**
  - **First:** use `.github/release.yml` label→category if present.
  - **Else:** default mapping (Breaking changes, Features, Bug fixes, Other).
  - **Fallback for entries without labels:** Map commit prefixes: `feat` → Features, `fix` → Bug fixes, `docs`/`chore`/`style`/`refactor`/`perf`/`test` → Other; no prefix → Other.
- **4b.
  Group entries**
  - Group by category; **Deduplicate** by issue (prefer the PR that "Closes" it).
- **4c.
  Draft bullet text (publishable)**
  - Prefer **issue summary** when available, else issue title; always link the issue (and PR if useful); else PR title; commit-only noisy items are omitted from publishable and noted in the working companion.
  - Produce one Markdown section per category; empty sections MUST use `_(žádné)_` (Czech) or `_(none)_` (English) — required by `validate_release_yml.py`.
  - **Language:** For date-range mode, use **Czech** section headings and bullet text by default.
    For tag-based mode, use the language chosen in Step 1.
    Czech headings: "## Zásadní změny", "## Nové funkce", "## Opravy chyb", "## Ostatní".
    The report **title** carries the same language as the sections — `# Poznámky k vydání — <repo> (<date>)` in Czech, `# Release notes — <repo> (<tag>)` in English — and `validate_release_yml.py` rejects a title whose language does not match.
  - When bumps exist and dependency coverage is enabled: under **Other / Ostatní**, add subsection **Závislosti a infrastruktura** / **Dependencies and infrastructure** with the **grouped final-version list** (not one bullet per Dependabot PR); keep deps in maintenance/Other, not Features.
  - Publishable files MUST NOT contain working-only headings.
- **4c-working.
  Draft working companion (tag-based)**
  - Write `<repo>_<tag>.working.md` with: Step 1 decisions, `prev..target`, gap-check, issue/PR classification notes, Nasazení/ops follow-up tables, assembly footnotes, tag-without-Release warnings, open-issue rationale.
  - With no non-publishable context, still write a minimal stub stating working notes are empty, so the split stays habitual.
  - Ops "Nasazení" detail that is not end-user facing lives in working notes; a one-line public maintenance notice in publishable Other only if the user explicitly wants it.
- **4d.
  Review**
  - Review publishable draft: duplicates, wrong category, broken links, clarity; confirm no working-only sections leaked.

#### Step 5 — Write to reports only

- **Tag-based mode:** Save **both** `.agents/reports/release-notes/<repo>_<tag>.md` (publishable) and `.agents/reports/release-notes/<repo>_<tag>.working.md` (working).
- **Date-range mode (mimic mode):** Save **one publishable file per day** with activity as `.agents/reports/release-notes/<repo>_YYYY-MM-DD.md`; use a deterministic command for "today"/end date; Czech headings and bullet text by default.
- Create the directory if missing; do **not** update the release body or wiki unless the user opted in (Step 5b).

#### Step 5b — Optionally update GitHub release body (tag-based, user opt-in)

- **When:** User chose "Yes" in Step 1 **and** mode is tag-based; skipped in date-range mode.
- **Preconditions:** A **GitHub Release object** must exist for the tag (not merely a git tag / tag page); the notes file path MUST be the **publishable** basename — **refuse** `.working.md` or any working companion.
- **Scope:** Propagation scope from Step 1 (single / range / all) over **publishable** reports only; present each exact publishable report for explicit per-release approval.
- **How:** `gh release edit <tag> --notes-file <publishable-path>` with `-R owner/repo` when needed; or an optional GitHub-capable MCP/plugin update-release tool.
- **Safety:** no release-body overwrite without Step 1 choice (B) and per-release approval of the exact publishable content.

#### Step 6 — Propagate `.github/release.yml`

- Before any approved target-repository write, state that repository's current branch and obtain confirmation; git delivery remains a separate explicit request.
- **Tag-based mode:** **Always** produce a recommended `.github/release.yml` reflecting this run's categories and label mapping; save it to `.agents/reports/release-notes/<repo>_release.yml`.
  **Optionally (with explicit user approval):** create or update `.github/release.yml` in the target repo; do not overwrite customisations without confirmation.
- **Date-range mode:** same recommended file to reports; populate the target repo only after explicit approval; keep `.github/release.yml` **title** values in **English**.

#### Step 7 — Validate and hand off

- Validate: publishable file(s) exist; tag-based runs also have a working companion; Markdown is valid; links point to the target repo.
  For report-only runs, use `python .agents/scripts/validate_release_yml.py --root <report-checkout> --release-config .agents/reports/release-notes/<repo>_release.yml` with the repository interpreter.
  This validates the recommended config and reports without requiring `.github/release.yml` or target propagation.
  Relative config paths resolve from `--root`; absolute paths are also accepted.
  Missing or invalid selected configs fail without fallback.
  Report structure, populated sections and publishable-vs-working checks remain enabled; optionally add `--check-git-count` for date-based reports.
- If target configuration propagation was approved, also run `python .agents/scripts/validate_release_yml.py --root <target-checkout> --skip-reports`.
  Omitting `--release-config` validates the target's actual `.github/release.yml`; `--skip-reports` skips only Markdown report checks.
  Keep the invoking report checkout and the target checkout distinct, even when they happen to be the same directory.
- Confirm the recommended `.github/release.yml` in reports; when target-repo propagation was approved, confirm the target file.
- Hand off: wiki copying is **manual**; release body updated only when the user opted in (Step 5b), using the **publishable** file only.

### Validation

- Tag-based: both `<repo>_<tag>.md` and `<repo>_<tag>.working.md` exist; publishable has required category sections, no working-only headings; gap-check done; deps section present or explicitly N/A; issue/PR classification done.
- Date-range: one `<repo>_YYYY-MM-DD.md` per active day; Czech sections as required.
- Recommended `.github/release.yml` in `.agents/reports/release-notes/`.
- Content is semantic; bullets prefer **issue summaries**; Dependabot collapsed, not dumped.
- When "supplement missing" was used: only non–pre-releases were processed.
- If the user opted in to release-body push: only publishable in-scope files were used; Release objects existed; no `.working.md` was passed to `gh release edit`.
- No automation pushes to wiki, updates a release body, or writes the target `.github/release.yml` without explicit user approval.

### Notes / Adaptation per repo

- **Repos without GitHub Releases (no-GitHub-Releases "mimic mode"):** Date-range mode: one file per active day; Czech report prose; English `release.yml` titles; no `.working.md` for date files.
- **Webapps**: expect high Dependabot volume — collapse into grouped final versions under Other; semver-titled milestones imply `prev_release..tag` enrichment merged with milestone issues.
- **API/docs**: fewer releases; "supplement missing" can fill historical gaps.

<!-- aiscr:ecosystem-only -->
AIS CR examples: webapps are `aiscr-webamcr` and `aiscr-digiarchiv-2`; API/docs is `aiscr-api-home`.
<!-- aiscr:ecosystem-end -->

- **Label convention**: if a repo lacks `.github/release.yml`, document the default mapping; Step 6 always writes a recommended copy to reports.
- **Commit and issue-ref conventions:** Fetch CONTRIBUTING when present (`[typ] desc (#N)`, `Closes #N`, `Refs #N`).
- **Issues as primary source:** Summarise full issue threads; dependency coverage is additive maintenance, not a replacement for issue-first product bullets.

### Execution using subagents

**Posture: registers `survey`.**
Acquisition across a release range — every pull request with its body, labels and comments, every referenced issue thread, and the commits — is a survey whose inventory carries a per-item `summary` this assignment names: for an issue, what it covered through to closure.
Semantic grouping, the publishable draft, and any write to a release body stay in this session.

The posture vocabulary, the declared return contracts, and the admission test are owned by `aiscr-quality-first-execution`.
Acquire one route per invocation: the delegate definition where it resolves, or the shared library ([common](../../../.agents/skills/_dispatch/common.md), the contract part, and the lens part) run as a pass in this session.
Reading both delivers the contract twice.

<!-- aiscr:gen:id=guardrails -->

## Iron Law

**IRON LAW:** `NEVER PUSH RELEASE NOTES TO GITHUB (gh release edit) WITHOUT FIRST PRESENTING THE GENERATED CONTENT TO THE USER AND RECEIVING EXPLICIT PER-RELEASE APPROVAL.`

No exceptions.
Publishing release notes is a public-facing action that cannot be undone silently.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The notes look good — I'll just push them" | Present the **publishable** Markdown first; wait for explicit approval. |
| "The user asked for backfill — I'll push all at once" | Per-release approval; never batch-push without explicit confirmation. |
| "gh release edit is reversible" | Still requires preview and per-release approval. |
| "Milestone issues cover the whole release" | Inventory deps and gap-check the range. |
| "Milestone title is v1.4.0 but I'll only list milestone issues" | Propose `prev_release..this_tag` merged with milestone issues. |
| "Every #N is an issue" | Resolve issue vs PR via API. |
| "Tag page ⇒ can edit release body" | Check a GitHub Release object exists. |
| "release.yml excludes deps ⇒ omit from curated notes" | Curated publishable notes get collapsed deps. |
| "One Markdown file is fine for draft + publish" | Split publishable vs `.working.md`; never publish working notes. |

<!-- aiscr:endgen -->

## Verification before completion

Before claiming this workflow complete, confirm:

- [ ] Publishable release notes presented to the user before any `gh release edit` call.
- [ ] Per-release explicit approval obtained for each updated release body.
- [ ] Publishable (and, for tag-based, working) files exist under `.agents/reports/release-notes/`, correctly named.
- [ ] Publishable file has no working-only headings; `.working.md` not used for remote update.
- [ ] Gap-check and dependency inventory completed (or N/A).
- [ ] `.github/release.yml` conventions followed (label grouping, bot exclusion).

## Governance

- Output is stored in `.agents/reports/release-notes/` by default; no wiki push is automatic.
- Updating a GitHub release body requires explicit per-release user approval and the **publishable** file only.
- Follow `.github/release.yml` conventions (exclude bots, assign labels); curated notes still cover collapsed dependencies.

## Valid next steps

- Hand the prepared **publishable** release notes to their owner; publishing is outside this skill.
- `/aiscr-write-release-notes` — re-run this workflow for the next release.
- Before using another installed workflow, read its skill and load the context its own instructions require.

## Bundled scripts

The enrollment bundle installs these repository-local runtime scripts:

- `.agents/scripts/validate_release_yml.py`
- `.agents/scripts/lib/__init__.py`
- `.agents/scripts/lib/log_utils.py`
- `.agents/scripts/lib/proc_utils.py`
