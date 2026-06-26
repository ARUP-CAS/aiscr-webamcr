---
name: aiscr-docs-language-review
description: Run language and typo review of repo docs; user-facing Czech, agent-facing
  English, README_en equivalents, report language split, GFM formatting. Use when
  the user asks to review docs language, fix typos, add README English versions, or
  align with GitHub Markdown.
---

<!-- aiscr:compiled=aiscr-docs-language-review -->

<!-- aiscr:stop-anchor -->
**Entry scope (compiled)**

- This `.github/skills/` skill is self-contained; use the workflow body and embedded execution plan below.
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
