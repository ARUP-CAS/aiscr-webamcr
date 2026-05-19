---
name: aiscr-note-idea
description: Capture an idea as an OpenSpec backlog change using the lightweight backlog
  schema, then stop before promotion.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-note-idea.md -->

# aiscr-note-idea

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Capture one new idea as an OpenSpec backlog change under `openspec/changes/`
without starting planning or promotion into the governance-driven workflow.

## Phase awareness

This skill operates at the **ideation** layer of the OpenSpec lifecycle.
It captures a new idea as a backlog change without planning or promotion.
After completing its workflow, it hands off to `/aiscr-plan-from-idea` for
governance-driven promotion or `/opsx:continue` for manual artifact work.
It must not promote, create governance-driven artifacts, or cross into planning.

## Steps

1. Ask the user for a short slug (descriptive kebab-case label) and rough body text.
   If the user did not provide a good slug, derive one and confirm it before
   creating anything.
2. If the backlog proposal would be hard to understand later, ask one or two
   short clarifying questions only.
3. Create the backlog change scaffold using the OpenSpec new-change flow.

   This wrapper should feel like `/opsx:new <slug>`, but it must use the
   `backlog` schema:

   ```bash
   openspec new change "<slug>" --schema backlog
   ```

   If `openspec/changes/<slug>/` already exists, stop and ask whether to
   continue that backlog item or choose a different slug.

4. Retrieve the backlog template dynamically and fill the proposal:

   ```bash
   npx openspec instructions proposal --change "<slug>" --json
   ```

   Use the retrieved template guidance to write `proposal.md`. The lightweight
   backlog shape:

   - **Title:** one sentence from the user's intent.
   - **Scope:** one of `hub-only`, `hub+siblings`, `sibling:<repo-name>`, `external`, `manual GitHub`, or a short clear combination.
   - **Primary artefacts:** concrete paths when known; otherwise `(refine when planning)`.
   - **Status:** usually `backlog`; use `partially addressed` only if the user says work already started.
   - **Priority:** add `high`, `medium`, or `low` only when the ordering is clear; otherwise omit it.
   - **Expected size:** add `S`, `M`, `L`, or `XL` only when the effort is reasonably guessable; otherwise omit it. Scale hint: `S` = hours / tiny scope; `M` = days / single area; `L` = days to a week / cross-file or multi-repo; `XL` = week+ / ecosystem-wide or phased.
   - **Before:** optional `<slug> - reason` sequencing hint.
   - **After:** optional `<slug> - reason` sequencing hint.
   - **Body:** keep it short, in normal Markdown. Use short prose or flat bullets; add `##` headings only when the idea is long enough to need structure. Do not paste a full plan schema, a large checklist, or a formal todos list.

5. Validate the new backlog item:

   ```bash
   npx openspec validate --all
   ```

6. Show the current change status:

   ```bash
   npx openspec status --change "<slug>" --json
   ```

7. Refresh the generated backlog inventory so the new item materializes in the
   shared report location:

   ```bash
   python .agents/scripts/generate_backlog_overview.py
   ```

   Default materialized report paths:

   - `.agents/backlog-overview.md`

8. Stop and point the user to the next valid entry points:

   - `/opsx:continue <slug>` if they want to continue artifact work manually
   - `/aiscr-plan-from-idea <slug>` if they want the AIS CR planning-first
     promotion flow

## Iron Law

**IRON LAW:** `NEVER PROMOTE A BACKLOG ITEM OR CREATE GOVERNANCE-DRIVEN ARTIFACTS INSIDE aiscr-note-idea.`

No exceptions. This workflow stops after the `backlog`-schema proposal exists and the user has a clear next step.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "I'll keep going and create specs or tasks too" | Stop. Let user initiate `/aiscr-plan-from-idea` or `/opsx:continue` instead. |
| "I should read the whole backlog first" | Stop. Stay scoped to this one backlog proposal unless the user names a directly related slug. |
| "I'll turn this into a full plan while I am here" | Stop. This workflow captures a backlog proposal only; planning happens later. |
| "I should update root governance docs too" | Stop. That belongs to a separate approved migration or governance task. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Exactly one new backlog change exists at `openspec/changes/<slug>/`.
- [ ] `.openspec.yaml` declares `schema: backlog`.
- [ ] `proposal.md` follows the backlog template and preserves the user's intent in short form.
- [ ] No governance-driven artifacts (`specs/`, `design.md`, `tasks.md`) were created.
- [ ] The backlog inventory report was refreshed (`.agents/backlog-overview.md`).
- [ ] The user was shown the resulting slug, the inventory location, and the next valid follow-up command.

## Plan and workflow

_No backing plan file;_ follow fallback and governance.

**Registry fallback:** Create `openspec/changes/<slug>/` with schema `backlog`, fill `proposal.md` from the backlog template, refresh `.agents/backlog-overview.md`, and stop before planning or promotion.

## Governance

- Create only one backlog proposal unless the user explicitly asked for closely
  related cleanup in the same task.
- Do not escalate into broad backlog review unless the user explicitly asked for it.
- Do not turn the backlog proposal into a plan, checklist, or full workflow proposal.
- After creating or updating a backlog item, refresh the generated backlog
  inventory report unless the user explicitly asked not to touch reports.
- Backlog schema and template: `openspec/schemas/backlog/`.

## Valid next steps

- `/aiscr-plan-from-idea <slug>` -- promote this backlog item into the AIS CR planning-first governance-driven flow
- `/opsx:continue <slug>` -- continue artifact work on this change manually
- `/aiscr-note-idea` -- capture another idea as a separate backlog item