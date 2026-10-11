---
name: aiscr-docs-language-review
description: Run language and typo review of repo docs; user-facing Czech, agent-facing
  English, README_en equivalents, report language split, GFM formatting. Use when
  the user asks to review docs language, fix typos, add README English versions, or
  align with GitHub Markdown.
disable-model-invocation: true
---

<!-- aiscr:compiled=aiscr-docs-language-review -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.gemini/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-docs-language-review — docs language, typos, and formatting

Run a detailed language and typo review of all repository documentation: user-facing docs in Czech, agent-facing in English, README English equivalents, and GitHub-compatible Markdown formatting.

**When to use vs alternatives:** Use for **language, spelling, audience-appropriate Czech vs English, README twins, and Markdown formatting** per `docs-language-quality`. For **duplication, cross-tree drift, doc discovery/link graphs, and structural hygiene** without a primary language pass, use **`/aiscr-doc-hygiene-audit`** instead (`documentation-consistency` spec).

## Phase awareness

This skill operates within the **implement** phase of the OpenSpec lifecycle.
It is typically invoked as part of `/opsx:apply` or a standalone approved task.
Before executing, check for an active OpenSpec change or domain spec under
`openspec/`.
If one exists, load its context files as the primary authority.
If none exists for this domain, run `/opsx:propose`, stop for human approval,
and only continue after that change becomes the active context of the run.
It must not create new **governance-driven** OpenSpec changes directly, promote backlog items, or
escalate scope beyond the approved task boundary, except for the backlog-only handoff governed by
the workflow contract summarized in this compiled skill after explicit per-run approval (see **Report-to-backlog handoff** below).

## Report-to-backlog handoff

For **deferred** language, README-pairing, translation, or GFM findings that stay report-only because inline fixes were not approved, follow the workflow contract summarized in this compiled skill (*Deferred language findings hand off to backlog*).

1. List backlog candidates after the review report exists (stable finding keys, proposed slug, source report path).
2. Ask for **explicit per-run** approval to emit backlog items.
3. If approved, draft the backlog candidate body inline — candidate slug, a one-line summary, `**Source report:**` (the approved report path), and `**Finding keys:**` — without copying sensitive evidence, then stop. Promotion into the management hub's backlog (creating the OpenSpec backlog change and refreshing the backlog overview) is a separate, explicit hub action by a maintainer; this workflow does not create hub changes or auto-invoke hub commands.
4. Record slugs in the review report or explain report-only outcomes.

Do not promote or implement spawned backlog inside this skill.

## Context to load first

1. the workflow contract summarized in this compiled skill — behavioral requirements and architecture
2. the workflow contract summarized in this compiled skill — backlog emission contract (when emitting follow-ups)
3. `AGENTS.md` — governance and scope
4. The repository's `.agents/` layout (structure of agent assets)
5. The repo's docs audience/language classification (this workflow creates or updates it)
6. the embedded execution plan below — execution procedures

## Language rules

- **User-facing docs**: Czech (README.md, CONTRIBUTING.md, root docs)
- **Agent-facing docs**: English (AGENTS.md, CLAUDE.md, `.agents/**`, `.cursor/**`, `.claude/**`, `.codex/**`)
- **Reports**: Czech narrative + English agent-facing sections
- **Release notes** (`.agents/reports/release-notes/*.md`): fully Czech including bullet text
- **Config** (`.github/release.yml`): English — do not translate category titles

## Steps

1. Ask the user: target repo (default: this repo), optional scope (root only or full `.agents/`).
2. Discover and classify all docs: update `docs_language_classification.md`.
3. Language/typo pass: correct typos; enforce Czech for user-facing, English for agent-facing.
4. Add `README_en.md` equivalents where missing (for Czech README files).
5. GFM formatting pass: fix heading hierarchy, blank lines around lists/headings, table formatting.
6. Run validation scripts (read-only):

   ```bash
   python .agents/scripts/link_check.py
   python .agents/scripts/doc_discovery.py --check
   ```

   If the repository provides an additional plan or Markdown validator, run its
   documented command as part of the same read-only validation pass.

7. Register convention in `CONTRIBUTING.md` and `.agents/README.md` if not already present.

<!-- aiscr:gen:id=guardrails -->
## Iron Law

**IRON LAW:** `NEVER APPLY LANGUAGE OR FORMATTING FIXES DIRECTLY. THE DEFAULT OUTPUT IS A REPORT. CHANGES REQUIRE EXPLICIT USER APPROVAL.`

No exceptions. Even "obvious" typos or GFM fixes must be presented before being applied.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The typo is obvious — I'll fix it inline while I'm here" | Report all findings first; apply fixes only after explicit approval. |
| "The language classification is clearly wrong — I'll correct `docs_language_classification.md` now" | Present the finding; update the classification file only after user confirmation. |
| "GFM formatting fixes are cosmetic — no approval needed" | Even cosmetic fixes are presented before applying; present the grouped list, then apply on approval. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Review report presented before any file edits were applied.
- [ ] `docs_language_classification.md` updated if audience classification changed (with user confirmation).
- [ ] Bundled validation scripts passed (`link_check.py`, `doc_discovery.py --check`).
- [ ] No structural changes (rename, delete, reorganize) applied without separate explicit approval.
<!-- aiscr:endgen -->

## Governance

- Do **not** run `orchestrate_local_agent_sync.py` `apply --approve` or invoke the retired `sync_agent_configs.py` operator/compatibility path unless the user explicitly asks.
- Present findings before applying; destructive changes require explicit confirmation.
- Full workflow: the embedded execution plan below

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- Read the identifiers and references stated in this workflow and follow the **Usage** section before loading a different workflow's context.

## Embedded execution plan

### Plan: Repository documentation – language, typos, and formatting review

> **OpenSpec migration:** Persistent behavioral requirements for this workflow now live in the workflow contract summarized in this compiled skill. This `.plan.md` file remains the reusable execution and governance layer for aiscr-management. See the identifiers and references stated in this workflow.

#### Context

This plan defines a **reusable workflow** for reviewing all repository documentation in aiscr-management (and applicable AIS CR repos) with three pillars: (1) **language and audience** (user-facing = Czech, agent-facing = English), (2) **README English equivalents** and **report language split** (reports in Czech; agent-oriented parts separated and in English), and (3) **GitHub-compatible Markdown formatting**. It lives in aiscr-management and targets the management repo first; the workflow is repo-agnostic so it can be applied to sibling repos (webapps, API, data-app, docs) with minor adaptation.

It **complements** [doc-hygiene-audit.plan.md](the embedded execution plan below) (which focuses on duplication, drift, token efficiency, and governance alignment). This plan focuses on **language, typos, and GFM formatting**, not on structural duplication or cross-reference integrity—those remain in the doc-hygiene plan.

#### Goals

- **Classify** every doc file by audience (user-facing vs agent-facing) and assign target language (Czech vs English).
- **User-facing docs in Czech**: Root README, CONTRIBUTING, CLAUDE (and any human-oriented sections); ensure consistent Czech and fix typos/grammar.
- **Agent-facing docs in English**: AGENTS.md, all the embedded execution plan below, `.agents/prompts/*.md`, SKILL.md files, agent-oriented sections in governance—keep English and fix typos/grammar.
- **READMEs have an English equivalent**: For each README (root and under `.agents/`), provide or verify an English version (e.g. `README_en.md` or a documented convention).
- **Reports**: Outputs in `.agents/reports/` primarily in Czech; where a report contains **agent-related** content, split that into a separate section or file in English so agents can consume it without mixing human-facing narrative. **Release notes:** `.agents/reports/release-notes/*.md` are **fully Czech** (headers, boilerplate, and individual bullet text); generated by the release-notes plan. **Config:** `.github/release.yml` is **English** (canonical categories for GitHub and release-notes generation).
- **GitHub-compatible formatting**: Align all touched files with GitHub Flavored Markdown (GFM): LF line endings, trailing newline at EOF, no trailing spaces, ATX-style headings (`#`), code fences with language tags, consistent list spacing, tables following GFM table syntax.

#### Scope and assumptions

- **In scope**
  - All Markdown under repo root and `.agents/` (READMEs, governance, plans, prompts, reports, scripts README), and committed vendor-tree READMEs / SKILL.md files.
  - Language and typo pass per file according to its audience.
  - Introducing or updating `README_en.md` (or equivalent) for each README that currently has no English version.
  - Splitting existing reports that mix human narrative and agent-facing content into Czech main body + English agent section/file where appropriate.
  - GFM formatting pass (can be done via script or checklist; see Validation).
- **Out of scope**
  - Changing business rules or project conventions (only how they are written and formatted).
  - Running high-impact scripts (`sync_agent_configs.py`) unless explicitly requested.
  - Refactoring application code.
- **Assumptions**
  - Governance docs ([AGENTS.md](/AGENTS.md), [CLAUDE.md](/CLAUDE.md), [CONTRIBUTING.md](/CONTRIBUTING.md)) remain authoritative; this plan links to them and does not duplicate their content.
  - Doc discovery and link-check scripts ([doc_discovery.py](../../../.agents/scripts/doc_discovery.py), [link_check.py](../../../.agents/scripts/link_check.py)) are run before or after the review to avoid broken refs when renaming/splitting files.

#### Execution approach

- Inventory all `.md` files and classify by path and content (user vs agent audience); confirm which READMEs already have an EN counterpart.
- After language/typos and GFM edits, review a sample of changed files for consistency and correct audience/language assignment.
- Prefer **script-first** for deterministic checks (link_check, doc_discovery, optional GFM lint); reserve judgment for classification decisions and final review.

#### Steps

##### Step 1 — Discover and classify documentation

- Run **doc discovery** (e.g. `python .agents/scripts/doc_discovery.py --output json`) to get the list of instruction-bearing docs. Extend or maintain a **classification** (e.g. in [the identifiers and references stated in this workflow)):
  - **User-facing** (target language: Czech): root `README.md`, `CONTRIBUTING.md`, `CLAUDE.md` (human-facing sections), and `README.md` files throughout the repo's `.agents/` directories.
  - **Agent-facing** (target language: English): `AGENTS.md`, all the embedded execution plan below, `.agents/prompts/*.md`, all `SKILL.md` under committed vendor skill trees such as `.cursor/skills`, `.claude/skills`, `.codex/skills`, and `.gemini/skills`.
  - **Reports**: `.agents/reports/*.md` — primary language Czech; identify which reports (or sections) are consumed by agents and plan to split those into English (see Step 4).
- Record which READMEs already have an English equivalent (e.g. `README_en.md`) and which need one.

##### Step 2 — Define README English equivalent strategy

- Decide convention: either `README_en.md` alongside each `README.md`, or a single "English docs" index that links to EN versions. For aiscr-management, recommend: each README that is today Czech gets an English counterpart so both humans and tooling can use EN when needed.
- Create or update the list of files to add/update (from Step 1).

##### Step 3 — Language and typo review (user-facing, Czech)

- For each file classified as user-facing, perform a **language and typo pass** in Czech: fix typos, grammar, and style; ensure terminology is consistent with governance and existing Czech docs.
- Leave agent-facing files unchanged in this step.

##### Step 4 — Language and typo review (agent-facing, English)

- For each file classified as agent-facing, perform a **language and typo pass** in English: fix typos, grammar, and clarity; keep repo-agnostic wording where applicable.
- For **reports** that currently mix human narrative and agent-oriented content: keep the main report body in **Czech**; extract or add an **agent-facing part** in **English** (e.g. a dedicated section or separate file). Document the convention in `.agents/reports` or in the plan's Notes.

##### Step 5 — Add or update README English equivalents

- For each README without an EN version, add `README_en.md` (or the chosen naming) with equivalent content in English. Ensure links and paths in the EN version point to the same targets.
- Optionally add a short note at the top of each Czech README linking to the English version (and vice versa).

##### Step 6 — Align with GitHub-compatible formatting (GFM)

- Apply a **formatting pass** to all touched (or all repo) docs so they align with GitHub Flavored Markdown:
  - **Line endings**: LF (not CRLF).
  - **End of file**: Single trailing newline; no trailing spaces on lines.
  - **Headings**: ATX style (`#`, `##`, …); no underline-style headings.
  - **Code blocks**: Fenced with triple backticks and language tag where applicable.
  - **Lists**: Consistent spacing; use `-` or `*` consistently.
  - **Tables**: Use GFM table syntax; avoid broken or inconsistent column alignment.
- Run **PyMarkdown** (`pymarkdown scan .` or `python -m pymarkdown scan .`) and fix or document exemptions. Config: [.pymarkdown.yaml](/.pymarkdown.yaml); CI runs the same scan. PyMarkdown implements [markdownlint](https://github.com/DavidAnson/markdownlint)-style rules (GFM-aligned).

##### Step 7 — Validate and register

- Run **link_check.py** and **doc_discovery.py --check** to ensure no broken refs after renames or new files.
- If the repo has a plan validator, run its documented command and ensure no plan file was broken by edits.
- Run **pymarkdown scan .** (or scoped paths) and ensure it passes; fix any remaining violations from Step 6.
- Update any central doc that lists "language and formatting" expectations (e.g. CONTRIBUTING or [.agents/README_en.md](../../../.agents/README_en.md)) with a one-line reference to this plan so future contributors know the convention.

#### Validation

- **Classification**: Every relevant `.md` has an assigned audience and target language; READMEs have a documented EN equivalent strategy and, where required, an EN file.
- **Language**: User-facing docs in Czech; agent-facing in English; reports in Czech with agent-oriented content separated in English.
- **Typos**: No obvious typos or grammar errors in a spot-check of modified files.
- **GFM**: Touched files pass a GFM-oriented check (line endings LF, trailing newline, no trailing spaces, ATX headings, fenced code blocks with language, consistent list/table formatting).
- **Links**: `link_check.py` and `doc_discovery.py --check` pass after changes.
- **Plan validation**: the repository's plan validator passes when one is present.
- **Markdown**: PyMarkdown scan passes for all in-scope `.md` files (or for touched files when running the plan).

#### Notes / Adaptation per repo

- **aiscr-management**: Primary target; root README and CONTRIBUTING are Czech; AGENTS and CLAUDE are mixed—keep human-facing parts Czech, agent-facing parts English, or split sections by audience. Reports under `.agents/reports/`: decide per file whether to add an EN section or companion file for agent consumption.
- **Sibling repos**: Same rules apply; classify by audience, assign language, add README_en where needed, split report content if reports exist, then GFM pass. Adapt the file list to each repo's structure. To propagate Markdown linting: copy or reuse `.pymarkdown.yaml` from aiscr-management (if locally accessible), add `pymarkdownlnt` to CI dependencies, and run `pymarkdown scan .` (or scoped paths) in the validation job. **Note — management repo visibility:** `aiscr-management` may not be accessible outside a local environment with direct filesystem or CLI access; copy any needed config files locally before starting work in a sibling-repo context.

#### Options (planning phase)

**Delivery (choose before any commit or push):**

- **(A)** Create a branch and open a **draft** PR for the changes (recommended).
- **(B)** Create a branch only (no PR).
- **(C)** Local changes only (no branch, no push).

Do not commit or push until the user has chosen.

#### Plan refinement / Autoupdate

- After completing this plan (or after running it on several repos): update the plan with generic lessons (e.g. clearer classification criteria, or a small script that tags files by audience). **PyMarkdown (markdownlint-style rules) is adopted** and is run in CI and in this plan's validation. Keep the plan repo-agnostic; put repo-specific examples in "Notes / Adaptation per repo".

## Bundled scripts

The enrollment bundle installs these repository-local runtime scripts:

- `.agents/scripts/doc_discovery.py`
- `.agents/scripts/link_check.py`
