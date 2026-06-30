# AIS CR — repository guidance for GitHub Copilot

This file is the **repository digest for GitHub Copilot** in `aiscr-webamcr`. It
is **committed directly** in this repository. The canonical reference and the
authoring source live in the `aiscr-management` hub; the assistant surfaces in
this repo are delivered from that hub by config sync.

<!-- aiscr:stop-anchor -->

## Entry scope

- Stay in this Copilot surface first; do not open parallel vendor trees by default just in case.
- Use `.github/copilot-instructions.md` plus the shared governance docs below before touching `.cursor/`, `.claude/`, `.codex/`, or `.gemini/`.
- Cross into another vendor tree only for explicit parity checks or governance maintenance.
- When a directory has both `README.md` and `README_en.md`, prefer the English counterpart for operational reading.

## Vendor-specific entry points (read this first)

AIS CR mirrors the same **`aiscr-*` workflow slugs** into **separate config roots**, because **each product loads its own tree** — there is no single universal skills file:

| Product / runtime | Typical entry in this repo |
| --- | --- |
| **GitHub Copilot** | **This file** for governance context, plus **`.github/skills/aiscr-*/SKILL.md`** self-contained Agent Skills (Copilot CLI + cloud agent) for the `aiscr-*` workflows. |
| **Cursor** | `.cursor/skills/`, `.cursor/rules/` |
| **Claude Code** | `.claude/skills/`, `.claude/rules/` |
| **Codex** | `.codex/skills/`, `CODEX.md` |
| **Gemini** | `.gemini/skills/`, `.gemini/context/`, `GEMINI.md` |

So this digest **does not substitute** for the mirrored `skills/` trees when you work in those products — open the matching tree there. When you work **in Copilot**, use this digest and the shared kernel below.

## Shared kernel (governance)

- **`AGENTS.md`** — scope, planning-first workflow, agent behaviour, and the **Governance baseline** (planning, usage logging, model logging) and **OpenSpec** sections.
- **`CONTRIBUTING.md`** — branch model (`test` → `main`), commit format, testing, OpenSpec workflow.
- **`CLAUDE.md`**, **`CODEX.md`**, **`GEMINI.md`** — per-vendor entry docs into the same shared governance.
- **Delivered rule readers** — `.github/instructions/`, `.claude/rules/`, `.cursor/rules/`, and `.gemini/context/` carry the generated rule readers for this repo (for example `aiscr-ecosystem-governance`, `aiscr-workspace-boundary-safety`, `aiscr-model-logging`, `aiscr-quality-first-execution`). The canonical bodies are authored at the `aiscr-management` hub and delivered here by config sync.

**Planning and usage:** non-trivial or mutating work follows a **single planning phase** with human approval before mutating steps; record **one** rolling usage-log entry (with agent/runtime and backend model id) for significant work. See the **Governance baseline** section in `AGENTS.md`.

## Where workflows live

- **Workflow skills (this repo's enrolled set):** delivered as `.github/skills/aiscr-*/SKILL.md` for Copilot and as matching `aiscr-*` skills under `.cursor/skills/`, `.claude/skills/`, `.codex/skills/`, `.gemini/skills/`. Enrolled here: `aiscr-codebase-review`, `aiscr-prod-ui-crawl-review`, `aiscr-ci-review-integration`, `aiscr-incident-postmortem`, `aiscr-release-notes`, `aiscr-api-doc-alignment`, `aiscr-ai-data-exposure-policy`, `aiscr-doc-hygiene-audit`, `aiscr-docs-language-review`, `aiscr-review-pr`, `aiscr-ci-scriptification`, `aiscr-workstation-assistant-sandbox`.
- **Skillset / workflow map:** `.agents/canonical_configs/references/aiscr_skillset_mapping.md`; topic-to-tool routing in `.agents/canonical_configs/references/governance_by_tool.md`.
- **OpenSpec requirement layer:** `openspec/specs/` for persistent capability contracts and `openspec/changes/` for change-scoped artefacts.
- **Scripts:** `.agents/scripts/` (this repo carries the delivered subset). Do **not** run high-impact automation without explicit human approval and an approved plan.

## OpenSpec

This repo versions OpenSpec artefacts directly:

- Capability specs: `openspec/specs/<domain>/spec.md`
- Change artefacts: `openspec/changes/<change>/`
- Repo config and schema selection: `openspec/config.yaml` (schema `spec-driven`)

Copilot-specific OpenSpec prompts are delivered under `.github/prompts/opsx-*.prompt.md`. OpenSpec is the `what` layer for migrated workflows; `AGENTS.md` and the delivered governance readers remain the `how` and approval layer. Validate edits with `npm run openspec:validate`.

### OpenSpec Mode Transfer Gating

When using OpenSpec workflows (`/opsx:*`), agents MUST follow mode-transfer gating:

- **Iron Law:** `NEVER TREAT ARTIFACT COMPLETION AS IMPLICIT APPROVAL TO IMPLEMENT`
- **Mode boundaries requiring explicit approval:**
  - Explore → Plan: when exploration concludes
  - Plan → Implement: when planning artefacts are complete
  - Any → Archive: when archiving a change
- **Hard stop:** after completing planning artefacts, stop and offer `/opsx:apply <slug>` — do not silently continue.

Full requirements are in the delivered `aiscr-planning-core` rule (see the **Governance baseline** section of `AGENTS.md`).

## Ecosystem-wide workflows (hub)

Cross-repo config sync, tool-parity / manifest maintenance, and registry changes are **run from the `aiscr-management` hub** (a local clone next to this repo, or via GitHub / `gh`), not from this repository. For the short routing summary, see the delivered `aiscr-ecosystem-hub-workflow-routing` reader (for example `.github/instructions/aiscr-ecosystem-hub-workflow-routing.instructions.md` or `.cursor/rules/aiscr-ecosystem-hub-workflow-routing.mdc`). This digest does not replace the per-assistant skill surfaces enrolled for this repository.

## Secrets and boundaries

- Do not commit secrets or paste production PII into prompts.
- Stay inside the workspace unless the user explicitly requests otherwise; state the impact for any out-of-workspace work (see the delivered `aiscr-workspace-boundary-safety` reader).

## Adding or renaming a standard `aiscr-` workflow

Standard `aiscr-*` workflows are authored and registered at the `aiscr-management` hub and delivered here by sync. When a workflow is added or renamed and this repo is enrolled in it, the matching `.github/skills/aiscr-<name>/SKILL.md` (and the other vendor `skills/` trees) are delivered together, and this digest is refreshed so the new slug is discoverable. Do not hand-create workflow skills in this sibling; propose the change at the hub and let sync deliver it. The cross-assistant registration checklist lives in the delivered `aiscr-ecosystem-governance` reader.
