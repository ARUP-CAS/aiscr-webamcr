---
name: aiscr-plugins-enablement
description: Enable relevant plugins and document fallbacks when unavailable. Use
  when the user asks to enable plugins, document plugin fallbacks, update the plugin/fallback
  catalog, or audit installed plugins for AIS CR relevance.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-plugins-enablement.md -->

# aiscr-plugins-enablement

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Enable and use relevant plugins (MCP, skills, hooks) across **IDE assistants** (e.g. **Cursor** and others; see `agent_tool_feature_matrix.md`); document and apply fallbacks when a plugin is not installed or unavailable. Preferred approach: **learn and integrate** — internalize plugin patterns into AIS CR skills before enabling external dependencies.

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

1. `openspec/specs/plugin-coverage/spec.md` — behavioral requirements and architecture (5-class audit, internalization-first philosophy)
2. `AGENTS.md` — governance and scope
3. `.agents/canonical_configs/references/plugin_enablement_and_fallback.md` — current plugin and fallback catalog
4. `.agents/canonical_configs/references/automation_recommendations.md` — Disciplined-workflow plugin patterns section for learn-and-integrate philosophy
5. `.agents/plans/plugins-enablement.plan.md` — execution procedures for Mode A/B/C workflow

## Steps

**Step 0 — Mode selection (pre-flight):** Determine mode before proceeding:

- **(A) Enablement** — add or document new plugins.
- **(B) Audit / learn-and-integrate** — assess installed plugins for AIS CR relevance; identify internalization candidates; produce disable suggestions.
- **(C) Both** — enablement + audit in the same session.

For Mode B/C: load the installed plugin list per product, read the full current `plugin_enablement_and_fallback.md`, apply the 5-class classification (Step 6).

**Step 1** — Ask the user: target scope (management repo vs sibling repos), mode (A/B/C), optional focus on tools (Cursor / Claude / Codex) or use cases (docs, GitHub, Figma, API, ML).

**Step 2** — Catalog plugins by assistant product and use case: list available MCP servers, skills, and hooks.

**Step 3** — Document enablement: how to install, verify, and activate each plugin.

**Step 4** — Define the fallback matrix: what to do when a plugin is unavailable (alternative tool, manual step, or skip).

**Step 5** — Update `plugin_enablement_and_fallback.md` with new or revised entries.

**Step 6 - Plugin relevance audit (Mode B/C)** - for each installed plugin, classify using the internalization-first lens:

1. **AIS CR-relevant + documented** — already in the matrix; no action.
2. **AIS CR-relevant + undocumented** — add to the matrix.
3. **Pattern-learnable** — the capability can be embedded into an AIS CR skill; document the pattern and mark as disable candidate.
4. **Overlaps an existing AIS CR skill** — consolidation candidate; propose which skill absorbs it.
5. **No AIS CR relevance** — disable candidate.

Produce a table and present to user. No uninstalls or disables executed without explicit consent.

**Step 7 - Proactive recommender mode (optional)** — satisfies **Proactive recommendation mode** in `openspec/specs/plugin-coverage/spec.md` (minimum required set + extras with estimated per-session token cost; advisory only). When the user asks "for workflow X what is the minimum required plugin set?", treat this as the proactive counterpart to `/aiscr-overhead-optimizer`:

1. load the workflow row from `canonical_workflows_context.md` (and `canonical_workflows_context.toml` when you need machine-authoritative slug alignment)
2. inspect current per-vendor plugin/skill/agent overhead with:

   ```bash
   python .agents/scripts/measure_workflow_overhead.py --dry-run --output json
   ```

3. distinguish required workflow context from currently enabled extras
4. report the minimum required set for the named workflow and estimate the per-session token cost of extras

This mode remains advisory. It must not disable or reconfigure plugins automatically.

**Step 8** - Update `automation_recommendations.md` "Plugins and fallbacks" section or add a link. Optional: add a cross-reference in `/aiscr-hooks-governance`.

## Iron Law

**IRON LAW:** `NEVER MERGE CONTENT INTO plugin_enablement_and_fallback.md WITHOUT READING THE FULL CURRENT FILE FIRST.`

**IRON LAW:** `NEVER RUN sync_agent_configs.py AS PART OF THIS WORKFLOW WITHOUT AN EXPLICIT APPROVED PLAN.`

No exceptions. These override any efficiency pressure or "it looks straightforward" reasoning.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The fallback is obvious" | Read the full `plugin_enablement_and_fallback.md`; check for conflicting entries. |
| "This plugin is universally useful" | Evaluate per repo category; check if the pattern can be internalized first. |
| "Just add a row to the matrix" | Read the full matrix; check for duplicates and ordering. |
| "No AIS CR repos use this language/tool" | Verify against `repos.toml` before excluding. |

## Verification before completion

Before claiming this workflow complete:

- [ ] `plugin_enablement_and_fallback.md` is internally consistent - no duplicate rows, fallbacks defined for each entry.
- [ ] `automation_recommendations.md` updated if new patterns were identified.
- [ ] Every enabled plugin verified as actually installed/accessible in the target environment.
- [ ] Internalization candidates documented: which patterns could replace the plugin in AIS CR skills.
- [ ] Proactive mode findings, when requested, name the workflow slug, minimum required set, and estimated cost of extras.
- [ ] Uninstall/disable candidates presented to user - no action taken without explicit consent.
- [ ] Self-review gate passed: no placeholder content, every entry names a concrete artefact or action.

## Plan and workflow

`.agents/plans/plugins-enablement.plan.md`

**Registry fallback:** Load openspec/specs/plugin-coverage/spec.md first for the durable behavioral contract; catalog plugins by assistant product (Cursor MCP, Claude skills, Codex skills) and use case (docs, GitHub, Figma, Elastic, Hugging Face); document enablement steps and verification; define fallback matrix for when plugins are unavailable; update automation_recommendations.md or create plugin_enablement_and_fallback.md; follow plugins-enablement.plan.md for Mode A/B/C workflow and 5-class relevance audit.

## Governance

- Do **not** run `sync_agent_configs.py` unless the user explicitly asks with an approved plan.
- Before applying to sibling repos, state the branch and obtain user confirmation.
- Coordinate with `/aiscr-hooks-governance` for hook-related changes.
- Learn-and-integrate first: prefer internalizing plugin patterns into AIS CR skills over adding external dependencies.
- Full workflow: `.agents/plans/plugins-enablement.plan.md`

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow