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

## Shared kernel pointers

- **`AGENTS.md`** — scope, agent behaviour, and the generated AIS CR governance kernel.
- **`CONTRIBUTING.md`** — branch model (`test` → `main`), commit format, testing, OpenSpec workflow.
- **`CLAUDE.md`**, **`CODEX.md`**, **`GEMINI.md`** — per-vendor entry docs into the same shared governance.
- **Delivered rule readers** — `.github/instructions/`, `.claude/rules/`, `.cursor/rules/`, and `.gemini/context/` carry the generated rule readers for this repo (for example `aiscr-ecosystem-governance`, `aiscr-workspace-boundary-safety`, `aiscr-model-logging`, `aiscr-quality-first-execution`). The canonical bodies are authored at the `aiscr-management` hub and delivered here by config sync.

Use the generated kernel in `AGENTS.md` and Copilot instruction readers under
`.github/instructions/` for the rule bodies; this digest only routes to them.

## Enrolled workflow discovery

- **Workflow skills (this repo's enrolled set):** delivered as `.github/skills/aiscr-*/SKILL.md` for Copilot and as matching `aiscr-*` skills under `.cursor/skills/`, `.claude/skills/`, `.codex/skills/`, `.gemini/skills/`. Enrolled here: `aiscr-codebase-review`, `aiscr-prod-ui-crawl-review`, `aiscr-ci-review-integration`, `aiscr-incident-postmortem`, `aiscr-release-notes`, `aiscr-api-doc-alignment`, `aiscr-ai-data-exposure-policy`, `aiscr-doc-hygiene-audit`, `aiscr-docs-language-review`, `aiscr-review-pr`, `aiscr-ci-scriptification`, `aiscr-workstation-assistant-sandbox`.
- **Skillset / workflow map:** `.agents/canonical_configs/references/aiscr_skillset_mapping.md`; topic-to-tool routing in `.agents/canonical_configs/references/governance_by_tool.md`.

## Local OpenSpec entry points

Copilot-specific OpenSpec prompts are delivered under
`.github/prompts/opsx-*.prompt.md`. Validate OpenSpec edits with
`npm run openspec:validate`; shared OpenSpec gating is in the generated
orientation below and the delivered `aiscr-planning-core` reader.

## Ecosystem-wide workflows (hub)

Cross-repo config sync, tool-parity / manifest maintenance, and registry changes are **run from the `aiscr-management` hub** (a local clone next to this repo, or via GitHub / `gh`), not from this repository. For the short routing summary, see the delivered `aiscr-ecosystem-hub-workflow-routing` reader (for example `.github/instructions/aiscr-ecosystem-hub-workflow-routing.instructions.md` or `.cursor/rules/aiscr-ecosystem-hub-workflow-routing.mdc`). This digest does not replace the per-assistant skill surfaces enrolled for this repository.

## Safety pointers

Use `AGENTS.md` and the delivered `aiscr-workspace-boundary-safety` and
`aiscr-ai-data-exposure-policy` readers for workspace, secrets, and AI data
exposure rules.

## Adding or renaming a standard `aiscr-` workflow

Standard `aiscr-*` workflows are authored and registered at the `aiscr-management` hub and delivered here by sync. When a workflow is added or renamed and this repo is enrolled in it, the matching `.github/skills/aiscr-<name>/SKILL.md` (and the other vendor `skills/` trees) are delivered together, and this digest is refreshed so the new slug is discoverable. Do not hand-create workflow skills in this sibling; propose the change at the hub and let sync deliver it. The cross-assistant registration checklist lives in the delivered `aiscr-ecosystem-governance` reader.

<!-- begin:generated:vendor-digest-core -->
<!-- generated by generate_governance_rules.py — do not edit manually -->

## AIS CR shared assistant orientation

This repository is part of the AIS CR ecosystem. The entry doc you are reading follows the same shared governance as every other assistant integration in this repository; this section is generated from one shared canonical body and is identical across the vendor entry docs. Entry scope (which surfaces to stay in first) is defined once in this document's preamble and is not repeated here.

### Cross-vendor map

Each product loads its own configuration tree; workflow slugs stay aligned across them:

| Product | Entry surfaces |
| --- | --- |
| Cursor | `.cursor/` (rules, skills, agents) |
| Claude Code | `CLAUDE.md` + `.claude/` |
| Codex | `CODEX.md` + `.codex/` |
| Gemini | `GEMINI.md` + `.gemini/` |
| GitHub Copilot | `.github/copilot-instructions.md` + `.github/` (instructions, prompts, skills) |

Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

### Shared governance kernel

`AGENTS.md` is the governance authority for AI agents in this repository; `CONTRIBUTING.md` owns the branch and PR workflow. The generated `agents-governance-kernel` block in `AGENTS.md` carries the current cross-vendor minimums for planning and approval, usage and model logging, script/sync/git approval, workspace and sibling boundaries, and hub authority.

The full rule bodies are delivered per assistant; the vendor section below says where this product reads them. This digest points to the shared kernel instead of restating it.

### Where workflows live

Standard `aiscr-*` workflows are authored at the `aiscr-management` hub and delivered per repository enrollment as per-vendor skill trees with matching slugs. Do not assume every workflow is mirrored in this repository; when an ecosystem-wide workflow (config sync, parity validation, registry maintenance) is needed, use the management hub.

### OpenSpec

- `openspec/specs/` stores persistent capability specs, `openspec/changes/` stores change-scoped artifacts, and `openspec/config.yaml` selects the repo schema.
- Mode-transfer gating iron law: `NEVER TREAT ARTIFACT COMPLETION AS IMPLICIT APPROVAL TO IMPLEMENT.` The explore → plan → implement boundaries each need fresh, phase-local human approval; after planning artifacts are complete, stop and offer apply instead of continuing silently.
- Validate OpenSpec artifacts after editing them (`npm run openspec:validate` where available).

### Secrets and boundaries

- Do not commit secrets, tokens, or API keys; do not paste production data or real PII into prompts; abstract or redact when demonstrating behaviour.
- Stay inside the opened workspace; out-of-workspace access needs an explicit user request and a plain statement of impact.
- Do not weaken sandbox, permission, or other safety-related assistant configuration unless the user strictly orders it.

<!-- end:generated:vendor-digest-core -->

<!-- begin:generated:vendor-digest-copilot -->
<!-- generated by generate_governance_rules.py — do not edit manually -->

## GitHub Copilot in this repository

- **Instructions:** generated per-topic instruction files are delivered under `.github/instructions/*.instructions.md`; this digest is the Copilot entry point for governance context.
- **Skills:** `aiscr-*` workflows are delivered as self-contained Agent Skills under `.github/skills/aiscr-*/SKILL.md` (read by the Copilot CLI and the cloud coding agent); OpenSpec prompts are generated under `.github/prompts/opsx-*.prompt.md` and mirrored OpenSpec skills under `.github/skills/openspec-*/`.
- **Sibling-owned content:** repo identity, repo-specific notes, and the enrolled-workflow list live outside the generated blocks of this digest and are preserved when the generated blocks are refreshed.

<!-- end:generated:vendor-digest-copilot -->
