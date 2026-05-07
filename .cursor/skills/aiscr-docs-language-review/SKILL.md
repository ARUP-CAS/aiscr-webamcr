---
name: aiscr-docs-language-review
description: Run language and typo review of repo docs; user-facing Czech, agent-facing
  English, README_en equivalents, report language split, GFM formatting. Use when
  the user asks to review docs language, fix typos, add README English versions, or
  align with GitHub Markdown.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-docs-language-review.md -->

# aiscr-docs-language-review

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Run a detailed language and typo review of all repository documentation: user-facing docs in Czech, agent-facing in English, README English equivalents, and GitHub-compatible Markdown formatting.

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

1. `openspec/specs/docs-language-quality/spec.md` — behavioral requirements and architecture
2. `AGENTS.md` — governance and scope
3. `.agents/README.md` — structure of `.agents/`
4. `.agents/canonical_configs/references/docs_language_classification.md` — audience and language per file
5. `.agents/plans/docs-language-review.plan.md` — execution procedures

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
   python .agents/scripts/validate_plans.py
   ```

7. Register convention in `CONTRIBUTING.md` and `.agents/README.md` if not already present.

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
- [ ] Validation scripts passed (`link_check.py`, `doc_discovery.py --check`).
- [ ] No structural changes (rename, delete, reorganize) applied without separate explicit approval.

## Plan and workflow

`.agents/plans/docs-language-review.plan.md`

**Registry fallback:** Load openspec/specs/docs-language-quality/spec.md first for the durable behavioral contract; run `python .agents/scripts/doc_discovery.py` to inventory docs; classify by audience (user-facing = Czech, agent-facing = English); define README English equivalent strategy; review language and typos per target language; add/update `README_en.md` files; align GitHub Flavored Markdown formatting; run `link_check.py`, `validate_plans.py`, PyMarkdown scan; follow docs-language-review.plan.md for execution workflow.

## Governance

- Do **not** run `sync_agent_configs.py` unless the user explicitly asks.
- Present findings before applying; destructive changes require explicit confirmation.
- Full workflow: `.agents/plans/docs-language-review.plan.md`

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow