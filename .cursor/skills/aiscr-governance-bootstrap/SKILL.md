---
name: aiscr-governance-bootstrap
description: Bootstrap AIS CR-style governance and .agents/ in a new or existing repo;
  optionally port assets from a mature source repo, run redundant-assets cleanup,
  or register in .agents/sync and run direct-bundle sync (with approval).
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-governance-bootstrap.md -->

# aiscr-governance-bootstrap

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Bootstrap AIS CR-style governance and `.agents/` structure in a new or existing repository.

## Phase awareness

This skill operates within the **implement** phase of the OpenSpec lifecycle and runs as a **bidirectional alignment loop** with five mutually exclusive modes (catalogued under "Bootstrap modes" in `.agents/canonical_configs/references/governance_stable_ids.md`):

| Mode | Stable id | When proposed |
|------|-----------|---------------|
| Greenfield | `bootstrap-mode-greenfield` | No governance, no `.agents/`, no `openspec/` |
| Introduce-OpenSpec | `bootstrap-mode-introduce-openspec` | Governance exists, no `openspec/`, user wants to adopt |
| Align | `bootstrap-mode-align` | Drift detected from hub baseline |
| Audit | `bootstrap-mode-audit` | User requests read-only drift and conformance report |
| Reverse-surface | `bootstrap-mode-reverse-surface` | Target-only patterns worth considering for hub adoption |

It is typically invoked as part of `/opsx:apply` or a standalone approved task. Before executing, check for an active OpenSpec change or domain spec under `openspec/`. If one exists, load its context files as the primary authority. If none exists for this domain, run `/opsx:propose`, stop for human approval, and only continue after that change becomes the active context of the run. It must not create new OpenSpec changes directly, promote backlog items, or escalate scope beyond the approved task boundary.

Mode auto-detection is a **recommendation**, not a decision — always obtain explicit user confirmation of the proposed mode (with the evidence that drove it) before any write.

## Context to load first

1. `openspec/specs/repository-governance-setup/spec.md` — durable behavioral requirements, bootstrap architecture, and the mode model
2. `AGENTS.md` — governance and scope
3. `.agents/README.md` — structure of `.agents/`
4. `.agents/plans/governance-bootstrap.plan.md` — execution-layer runbook organised as bootstrap packages (`pkg.detect`, `pkg.greenfield.*`, `pkg.introduce-openspec.any`, `pkg.align.any`, `pkg.audit.any`, `pkg.reverse-surface.any`, plus cross-cutting packages); see its **Canonical sources** and **Vendor coverage** tables for path resolution.
5. `.agents/prompts/repository_setup.md` — generation-time prose for what bootstrap generates inside the target (reverse-flow backlog body template, `.agents/local_overrides.toml` shape, mode-aware generation rules)
6. `.agents/canonical_configs/references/ecosystem_map.md` and `.agents/sync/repos.toml` - sibling registry (human / machine)
7. `.agents/canonical_configs/references/governance_stable_ids.md` — Bootstrap modes section (stable ids)
8. `.agents/canonical_configs/references/agent_tool_feature_matrix.md` and `.agents/canonical_configs/references/mandatory_vendor_doc_urls.toml` — active assistant-integration matrix; reference rather than inline vendor lists

### Mode-detection inputs (detect phase)

- Presence/absence of target's `openspec/` directory and `openspec/config.yaml` (schema and context when present)
- Presence/absence of target's `.agents/local_overrides.toml` (declared `[bootstrap]` metadata and override paths when present)
- Hub baseline reference: the committed state of `.agents/canonical_configs/`, workflow skills, governance rules, and canonical references in `aiscr-management` at session start
- `.agents/sync/repos.toml` entry for the target (when registered for sync)

## Phases (load prompts only when entering that phase)

- **Asset port** (optional): load `.agents/prompts/asset_port_instructions.md`
- **Redundant-assets cleanup** (optional): load `.agents/prompts/redundant_assets_cleanup_instructions.md`

## Steps

1. Ask the user: repository path / URL and (if known) desired intent (fresh bootstrap / introduce OpenSpec / align / audit / surface patterns). Collect optional inputs (SOURCE_REPO and asset allow-list; redundant cleanup; propagation / sync).
2. Log model usage per `.agents/canonical_configs/governance_rules/aiscr-model-logging.md` at the start.
3. **Run `pkg.detect`** per plan: detect repo type, OpenSpec / overrides state, drift; propose one mode with evidence; obtain explicit user confirmation; run guardrail checks. **Refuse** hub-self-bootstrap and submodule / monorepo-directory targets; **warn and require acknowledgment** on dirty targets or unknown / deprecated schemas. Do not proceed to any write-capable step until the user confirms the mode.
4. **Execute the confirmed mode by running the matching package(s) from `.agents/plans/governance-bootstrap.plan.md`:**
   - `bootstrap-mode-greenfield`: `pkg.greenfield.app` / `pkg.greenfield.docs` / `pkg.greenfield.data` (per detected repo type), which themselves invoke `pkg.deploy-logging-governance`, the optional packages when requested, `pkg.validation`, and `pkg.feedback-and-usage-log`.
   - `bootstrap-mode-introduce-openspec`: `pkg.introduce-openspec.any` only (native OpenSpec CLI scaffolding; leave existing governance untouched unless drift is separately detected).
   - `bootstrap-mode-align`: `pkg.align.any`, then `pkg.deploy-logging-governance` only for fixes that were classified as "fix" by the user.
   - `bootstrap-mode-audit`: `pkg.audit.any` (read-only; no writes).
   - `bootstrap-mode-reverse-surface`: `pkg.reverse-surface.any` (no hub-side writes; user invokes `/aiscr-note-idea <slug>` in the hub).
5. **Dependency install hygiene (greenfield / align when repo uses Node / Python / Docker):** align `CONTRIBUTING.md` / tech guidance with `.agents/prompts/repository_setup.md` (Dependency and install hygiene): committed lockfiles, frozen-lockfile CI installs where applicable, digest-pinned images, post-incident lockfile / `npm ls` re-verification.
6. **Propagation (greenfield / align only, optional):** run `pkg.propagation-and-sync` - register in `.agents/sync/repos.toml`, run direct-bundle inspect/dry-run, then apply only with explicit user approval; state branch per target repo and obtain explicit user confirmation.
7. **Validation (mode-aware):** `pkg.validation` — hub-required minimums always (planning, usage logging, model logging, sync registration when applicable, `.agents/local_overrides.toml` `[bootstrap]` integrity). Add adopted-capability checks when relevant: `npx openspec validate --specs --strict` for OpenSpec-adopter targets; `python .agents/scripts/run_validation_all.py` in the hub.
8. **Close-out:** `pkg.feedback-and-usage-log` — update the single rolling usage log entry for the current uncommitted change set per `.agents/canonical_configs/governance_rules/aiscr-usage-logging.md`. Include agent / runtime, model / backend, subagents used, MCP servers used, mode(s) and packages executed, target repo, impacted paths.

### Reverse-flow handoff contract

When mode `bootstrap-mode-reverse-surface` surfaces a sibling-only pattern:

1. Workflow drafts a backlog body following the `/aiscr-note-idea` lightweight backlog schema (see `repository_setup.md` reverse-flow body template): title, `scope: hub-only`, primary artefacts (path in target repo), `status: backlog`, `priority`, `expected size`, body with rationale and target reference.
2. Workflow proposes a slug (kebab-case, descriptive of the pattern) and outputs the drafted body.
3. Workflow stops and instructs the user: "Run `/aiscr-note-idea <slug>` in the hub to capture this candidate. I will not invoke it myself and will not write to any hub path."
4. Classification is conservative: `sibling-only`, `drift-from-hub`, `hub-aligned`, `ambiguous` (defaults to drift-from-hub with an ambiguity flag). Only `sibling-only` candidates are surfaced; ambiguous ones go to the drift report.

## Iron Law

**IRON LAW:** `NEVER OVERWRITE EXISTING GOVERNANCE FILES IN A TARGET REPO WITHOUT FIRST READING THEIR CURRENT CONTENT AND DIFFING AGAINST THE HUB BASELINE.`

**IRON LAW:** `NEVER BOOTSTRAP THE HUB REPOSITORY (AISCR-MANAGEMENT) FROM ITSELF.`

**IRON LAW:** `NEVER WRITE TO HUB PATHS DURING A SIBLING-SIDE RUN; NEVER AUTO-INVOKE /aiscr-note-idea.`

**IRON LAW:** `NEVER HONOUR A TARGET OVERRIDE THAT REMOVES OR WEAKENS A HUB-REQUIRED MINIMUM.`

**IRON LAW:** `NEVER PROCEED PAST MODE PROPOSAL WITHOUT EXPLICIT USER CONFIRMATION.`

No exceptions. These overrides any "the repo is new", "it's just a template", "the diff looks safe", or "auto-detection is obviously correct" reasoning. The hub defines the patterns; changes to the hub flow through hub-local workflows (OpenSpec changes, `/aiscr-note-idea`, plan refinement) — not through bootstrap targeting itself. Reverse-flow is user-mediated (workflow drafts body, stops, user invokes `/aiscr-note-idea <slug>` in the hub). Hub-required minimums (planning, usage logging, model logging, registry-driven sync) are enforced regardless of target configuration. Auto-detection is a recommendation; always show evidence and wait for explicit user confirmation before any write-capable step.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "This repo has no .agents/" | Check for hidden dirs and non-standard locations before concluding it's absent. |
| "The template is standard — no diff needed" | Read current files; diff against hub baseline before any write. |
| "I'll overwrite and fix later" | Backup (branch or export) before any overwrite of governance files. |
| "The detect phase picked `align` so I can just start fixing drift" | Show the proposed mode with evidence; wait for explicit user confirmation. |
| "Auditing found drift — let me fix it" | Audit mode is read-only. If the user wants fixes, re-enter mode proposal for `bootstrap-mode-align`. |
| "I can write to the hub's `openspec/changes/` since I'm drafting the backlog body anyway" | Stop. The user invokes `/aiscr-note-idea <slug>` in the hub. No sibling-side writes to hub paths. |
| "This override is convenient — let me honour it even though it targets usage-logging" | Refuse. Hub-required minimums cannot be overridden without an explicit hub-policy decision outside `.agents/local_overrides.toml`. |
| "The schema is custom but works, so I'll scaffold anyway" | Flag unknown/deprecated schemas and stop; require an explicit hub-policy decision. |
| "The target is a subdir of a larger repo but similar enough" | Refuse. Bootstrap expects a repository-root anchor; submodule/monorepo-directory targets are rejected. |
| "The target has uncommitted changes but I'm sure it's fine" | Warn, list dirty paths, require explicit acknowledgment before any write. |

## Verification before completion

Before claiming this workflow complete, confirm:

- [ ] Target repo state was detected (repo type, OpenSpec state, overrides, drift against hub baseline, registry entry).
- [ ] A mode was proposed **with evidence** and **the user explicitly confirmed** it before any write-capable step.
- [ ] Edge-case guardrails were checked (not the hub; not a submodule/monorepo directory; not a dirty target without acknowledgment; schema is hub-known or flagged).
- [ ] Current governance files in target repo were read and diffed before any write.
- [ ] Mode-specific contract held: greenfield scaffolded as required; introduce-openspec touched only `openspec/` tree; align made only surgical fixes for confirmed drift; audit wrote nothing; reverse-surface wrote no hub paths.
- [ ] `.agents/local_overrides.toml` `[bootstrap]` metadata refreshed (when write-capable mode and overrides exist or were created).
- [ ] Hub-required minimums validated (planning, usage logging, model logging, sync registration when applicable).
- [ ] Adopted-capability validations ran where relevant (`npx openspec validate --specs --strict` for OpenSpec adopters).
- [ ] Branch stated and user confirmed before any changes applied to target repo; sibling-side runs made no hub-side writes.
- [ ] If assistant roots or assistant roots are materialized at repo root, `.gitignore` matches `repository_setup.md` (root-anchored where applicable).
- [ ] Rolling usage log entry updated per `usage-logging.mdc` (agent/runtime, model/backend, subagents used, MCP servers used, mode(s) executed, impacted paths).

## Plan and workflow

`.agents/plans/governance-bootstrap.plan.md`

**Registry fallback:** Load openspec/specs/repository-governance-setup/spec.md first for the durable behavioral contract (mode model, idempotency, hub authority, reverse-flow architecture, validation layers, edge-case guardrails) and `governance_stable_ids.md` for the `bootstrap-mode-*` slug catalogue. The execution-layer runbook is `.agents/plans/governance-bootstrap.plan.md`, organised as bootstrap packages (`pkg.detect`, `pkg.greenfield.app` / `pkg.greenfield.docs` / `pkg.greenfield.data`, `pkg.introduce-openspec.any`, `pkg.align.any`, `pkg.audit.any`, `pkg.reverse-surface.any`, plus cross-cutting `pkg.deploy-logging-governance`, `pkg.optional-asset-port`, `pkg.optional-redundant-cleanup`, `pkg.optional-overhead-readme-en`, `pkg.propagation-and-sync`, `pkg.validation`, `pkg.feedback-and-usage-log`); the plan's Canonical sources and Vendor coverage tables resolve paths and matrix exceptions. Vendor scope references `.agents/canonical_configs/references/agent_tool_feature_matrix.md` rather than inlining vendor lists. `pkg.introduce-openspec.any` uses native OpenSpec CLI (`npm ci` precondition; `npx openspec instructions … --json`; `npx openspec validate --all`; fallbacks `bin/openspec`, `bin/openspec.cmd`, `npm run openspec:cli`). Inspect target-side mode-detection inputs when present: target `openspec/config.yaml` and target `.agents/local_overrides.toml`. Diff target paths against the hub baseline (committed `.agents/canonical_configs/`, workflow_skills, governance_rules, canonical references at session start). Propose one of the five mutually exclusive modes (`bootstrap-mode-greenfield`, `bootstrap-mode-introduce-openspec`, `bootstrap-mode-align`, `bootstrap-mode-audit`, `bootstrap-mode-reverse-surface`) with evidence and obtain explicit user confirmation before any write-capable step. Audit mode writes nothing; reverse-surface drafts a backlog body and stops (user invokes `/aiscr-note-idea <slug>` in the hub as a separate action). Never target the hub from itself; never write to hub paths from a sibling-side run; never auto-invoke `/aiscr-note-idea`. Respect declared overrides in `.agents/local_overrides.toml`; refuse overrides that target hub-required minimums.

## Governance

- Do **not** run `sync_agent_configs.py` unless the user explicitly asks.
- Before applying changes to a target repo, state the planned branch and obtain user confirmation.
- Never guess — use prompt artifacts for asset port and redundant-assets classification criteria.
- Full workflow: `.agents/plans/governance-bootstrap.plan.md`

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow