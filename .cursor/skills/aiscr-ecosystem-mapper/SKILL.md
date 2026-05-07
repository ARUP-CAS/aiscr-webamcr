---
name: aiscr-ecosystem-mapper
description: Create, refresh, or update the AIS CR ecosystem map. Use when the user
  asks to update the ecosystem map, add a repo to the map, refresh the map, or check
  ecosystem map consistency.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-ecosystem-mapper.md -->

# aiscr-ecosystem-mapper

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Create, refresh, or update `.agents/canonical_configs/references/ecosystem_map.md` so it remains the single source of truth for AIS CR sibling repositories.

## Phase awareness

This skill is a **meta/orchestration** helper that supports the OpenSpec lifecycle
without participating in phase transitions. It loads context, builds plans, or
maintains registries. It does not create OpenSpec changes or execute implementation tasks.
Check for relevant domain specs when the task touches governed capabilities.
If no relevant domain spec exists, consider running `/opsx:propose` to formalize the capability before execution work begins.

## Context to load first

1. `AGENTS.md` — governance and scope
2. `.agents/canonical_configs/references/ecosystem_map.md` — current ecosystem map (read "When to refresh" and "How to use" blocks)

## Triggers for update

- New repo added under `.agents/local_configs/<repo>/`
- Repo removed from local_configs
- Category or branch model changed for an existing repo
- Do **not** add repos that are only mentioned in plans or Git — include only repos with a local_configs subfolder

## Steps

1. Ask the user: action — `add`, `remove`, `refresh`, or `check`; optional repo name, category, and branch model for `add`.
2. Read `ecosystem_map.md` and follow the "When to refresh" and "How to use" blocks at the top.
3. Apply the change:
   - **add**: insert new row with repo name, category, branch model, `in_local_configs: true`.
   - **remove**: remove the row; set `in_local_configs: false` or delete entirely.
   - **refresh**: review all rows for accuracy; update "Last updated" note.
   - **check**: compare subdirs under `.agents/local_configs/` with map rows; report mismatches.
4. Commit with a clear message (e.g. `Add aiscr-foo to ecosystem map`).

## Iron Law

**IRON LAW:** `NEVER ADD A REPO TO ecosystem_map.md WITHOUT A CORRESPONDING DIRECTORY UNDER .agents/local_configs/. INCLUDE ONLY REPOS THAT EXIST ON DISK.`

No exceptions. Repos mentioned only in plans or Git history are not eligible for the map.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The repo is mentioned in a plan — I'll add it to the map to be thorough" | Include only repos with an actual `.agents/local_configs/<repo>/` subdirectory; plans are not evidence. |
| "The `in_local_configs` flag looks right from memory" | Always compare the map against actual subdirectories under `.agents/local_configs/`; do not rely on memory. |
| "A small refresh is fine without a `check` action first" | Run `check` first to surface any existing mismatches before applying bulk changes. |

## Verification before completion

Before claiming this workflow complete:

- [ ] `ecosystem_map.md` updated and internally consistent — no duplicate rows, no orphaned entries.
- [ ] `repos.toml` reviewed: every repo in the map has a matching entry (or absence is intentional and noted).
- [ ] `in_local_configs` flag in `ecosystem_map.md` accurately reflects actual subdirectory presence under `.agents/local_configs/`.
- [ ] README or "Last updated" note in `ecosystem_map.md` reflects the change date.
- [ ] For `check` action: all mismatches reported to user; none silently auto-fixed.

## Plan and workflow

_No backing plan file;_ follow fallback and governance.

**Registry fallback:** Read ecosystem_map.md; update manually per governance.

## Governance

- Do **not** run `sync_agent_configs.py`; this command only edits `ecosystem_map.md` and runs read-only checks.
- For significant bulk refreshes, log model usage per `.cursor/rules/model-logging.mdc` and add a usage log entry under `.agents/reports/usage/`.
- Full interfaces: `.agents/canonical_configs/references/aiscr_skillset_mapping.md`

## Valid next steps

- `/aiscr-config-sync` -- sync configurations to sibling repos after map updates
- `/aiscr-canonical-workflows-context` -- load context for a specific workflow
- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change