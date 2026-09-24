# AIS CR Skillset Mapping

This reference explains how AIS CR workflow skills relate to plans, prompts,
scripts, and OpenSpec requirement specs without duplicating the live workflow
catalogue.

## Authoritative Sources

| Concern | Source |
| --- | --- |
| Workflow slugs, display names, backing plans, contracts, context, and distribution locus | `.agents/canonical_configs/asset_manifest.toml` |
| Human-readable workflow context and assistant entry points | `canonical_workflows_context.md` |
| Persistent behavioral requirements | `openspec/specs/<capability>/spec.md` |
| Canonical workflow document (single human-readable reader) | `.agents/canonical_configs/workflow_skills/<slug>.md` |
| Generated assistant skill surfaces (routing stubs) | `.cursor/skills/`, `.claude/skills/`, `.codex/skills/`, `.gemini/skills/`, `.clinerules/workflows/`, `.github/prompts/`, `.gemini/commands/aiscr/` |
| Cross-assistant support matrix and vendor docs | `agent_tool_feature_matrix.md`, `mandatory_vendor_doc_urls.toml` |
| Sync and sibling delivery policy | `.agents/canonical_configs/asset_manifest.toml`, `.agents/sync/repos.toml`, `.agents/scripts/sync_policy.py` |

Do not maintain a second exhaustive skill inventory here. Add or rename a
workflow in the registry and canonical workflow skill source, then regenerate
and validate the emitted surfaces.

## Mapping Rules

- Skill slugs use the `aiscr-<name>` form and must match the registry row.
- Plan-backed workflows name their plan in `asset_manifest.toml`;
  no-plan workflows keep behavior in their skill body, OpenSpec spec, or script.
- Migrated workflows load the relevant `openspec/specs/<capability>/spec.md`
  first; plans remain the execution layer and scripts remain the deterministic
  implementation layer.
- Prompts are execution aids, not authorities. When both a plan and prompt
  exist, keep them separate: the plan defines when/why/how to verify, while the
  prompt defines model-facing instructions.
- High-impact scripts such as direct-bundle sync remain inspect/dry-run first
  and apply only after explicit human approval.

## Maintenance Checklist

When adding, renaming, or retiring a standard workflow:

1. Update `asset_manifest.toml` and regenerate `canonical_workflows_context.md`.
2. Create or update `.agents/canonical_configs/workflow_skills/<slug>.md`.
3. Add or update the OpenSpec capability spec or change delta when behavior
   changes.
4. Refresh direct references in prompts, plans, and assistant entry docs only
   where the workflow is load-bearing.
5. Run `python .agents/scripts/generate_workflow_skills.py`.
6. Run `python .agents/scripts/validate_tool_parity.py --strict`.
7. Run `npm run openspec:validate` when OpenSpec artifacts changed.

## Workflow Families

Use this grouping only as orientation. The registry remains authoritative for
the live set and exact plan/spec mapping.

| Family | Examples | Primary authority |
| --- | --- | --- |
| Lifecycle and OpenSpec | `aiscr-note-idea`, `aiscr-plan-from-idea`, `openspec-*` skills | OpenSpec schemas and change artifacts |
| Validation and planning | `aiscr-workflow-review`, `aiscr-workflow-registry-maintenance` | Plan/schema scripts, workflow-review state, and OpenSpec requirement governance |
| Governance and sync | `aiscr-governance-bootstrap`, `aiscr-config-sync`, `aiscr-agent-vendor-introduction` | OpenSpec specs, sync policy, registry files |
| Documentation and reports | `aiscr-doc-hygiene-audit`, `aiscr-docs-language-review`, `aiscr-release-notes`, `aiscr-incident-postmortem` | Domain specs, plans, prompts, report layout validators |
| CI, review, and production checks | `aiscr-ci-review-integration`, `aiscr-ci-scriptification`, `aiscr-review-pr`, `aiscr-prod-ui-crawl-review`, `aiscr-codebase-review` | Domain specs and execution plans |
| AI usage governance | `aiscr-ai-data-exposure-policy` | `security-privacy-ai-usage` spec and governance surfaces |
| Workstation setup | `aiscr-workstation-assistant-sandbox` | `workspace-safety-config` spec and `port_workspace_safety_config.py` |
| Overhead measurement | `aiscr-overhead-analysis` | `overhead-measurement` / `plugin-coverage` specs and `.agents/scripts/` |
| Ecosystem inventory | `aiscr-ecosystem-mapper`, `aiscr-sibling-branch-audit` | `ecosystem_map.md`, `repos.toml`, sibling branch spec/script |

## Generation Contract

The hub edits canonical sources and generated surfaces are refreshed by scripts:

- Workflow skills: `python .agents/scripts/generate_workflow_skills.py`
- Governance rule surfaces: `python .agents/scripts/generate_governance_rules.py`
- Agent definitions: `python .agents/scripts/generate_agent_definitions.py`

Sibling repositories receive selected generated assets only through reviewed
direct-bundle sync. Do not infer propagation from the mere existence of a hub
file.
