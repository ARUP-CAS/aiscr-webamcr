---
name: aiscr-governance-bootstrap
description: Bootstrap AIS CR-style governance and .agents/ in a new or existing repo;
  optionally port assets from a mature source repo, run redundant-assets cleanup,
  or register in local_configs and run sync (with approval).
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-governance-bootstrap.md -->

# aiscr-governance-bootstrap

<!-- aiscr:stop-anchor -->
**Entry scope (stub)**

- Canonical reader: [`.cursor/skills/aiscr-governance-bootstrap/SKILL.md`](.cursor/skills/aiscr-governance-bootstrap/SKILL.md). Read that file before executing this workflow or when the workflow body is load-bearing.
- Stay in this `.codex/skills/` surface unless the task requires the Cursor reader body, a parity check, generator work, or governance maintenance.
- This stub preserves routing and safety boundaries while avoiding a second full workflow body.

## Topic summary

Bootstrap AIS CR-style governance and .agents/ in a new or existing repo; optionally port assets from a mature source repo, run redundant-assets cleanup, or register in local_configs and run sync (with approval).

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

## Workflow routing

Load [`.cursor/skills/aiscr-governance-bootstrap/SKILL.md`](.cursor/skills/aiscr-governance-bootstrap/SKILL.md) for the full workflow body, guardrails, implementation steps, and verification requirements.

`.agents/plans/governance-bootstrap.plan.md`

**Registry fallback:** Load openspec/specs/repository-governance-setup/spec.md first for the durable behavioral contract (mode model, idempotency, hub authority, reverse-flow architecture, validation layers, edge-case guardrails) and `governance_stable_ids.md` for the `bootstrap-mode-*` slug catalogue. The execution-layer runbook is `.agents/plans/governance-bootstrap.plan.md`, organised as bootstrap packages (`pkg.detect`, `pkg.greenfield.app` / `pkg.greenfield.docs` / `pkg.greenfield.data`, `pkg.introduce-openspec.any`, `pkg.align.any`, `pkg.audit.any`, `pkg.reverse-surface.any`, plus cross-cutting `pkg.deploy-logging-governance`, `pkg.optional-asset-port`, `pkg.optional-redundant-cleanup`, `pkg.optional-overhead-readme-en`, `pkg.propagation-and-sync`, `pkg.validation`, `pkg.feedback-and-usage-log`); the plan's Canonical sources and Vendor coverage tables resolve paths and matrix exceptions. Vendor scope references `.agents/canonical_configs/references/agent_tool_feature_matrix.md` rather than inlining vendor lists. `pkg.introduce-openspec.any` uses native OpenSpec CLI (`npm ci` precondition; `npx openspec instructions … --json`; `npx openspec validate --all`; fallbacks `bin/openspec`, `bin/openspec.cmd`, `npm run openspec:cli`). Inspect target-side mode-detection inputs when present: target `openspec/config.yaml` and target `.agents/local_overrides.toml`. Diff target paths against the hub baseline (committed `.agents/canonical_configs/`, workflow_skills, governance_rules, canonical references at session start). Propose one of the five mutually exclusive modes (`bootstrap-mode-greenfield`, `bootstrap-mode-introduce-openspec`, `bootstrap-mode-align`, `bootstrap-mode-audit`, `bootstrap-mode-reverse-surface`) with evidence and obtain explicit user confirmation before any write-capable step. Audit mode writes nothing; reverse-surface drafts a backlog body and stops (user invokes `/aiscr-note-idea <slug>` in the hub as a separate action). Never target the hub from itself; never write to hub paths from a sibling-side run; never auto-invoke `/aiscr-note-idea`. Respect declared overrides in `.agents/local_overrides.toml`; refuse overrides that target hub-required minimums.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow
