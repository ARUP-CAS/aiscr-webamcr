## AIS CR Skillset Mapping – Plans, Prompts, and Candidate Skills

This document sketches a **mapping** between:

- reusable **plans** in `.agents/plans/`,
- execution **prompts** in `.agents/prompts/`,
- and potential shared **skills** (same `aiscr-<name>` slug under each assistant product's native `skills/` tree; Cursor carries the full reader, non-Cursor skill files route to that reader, and managed sibling payloads live under `.agents/local_configs/<repo>/`; see `canonical_workflows_context.md` and `agent_tool_feature_matrix.md`).

It does **not** implement skills directly; it defines interfaces and responsibilities so that a future skillset can be created safely.

---

### Principles

- Skills should be **thin orchestration layers**:
  - they invoke plans, prompts, and scripts,
  - they must not bypass governance (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`).
- Skills should:
  - keep side effects explicit,
  - avoid running high‑impact scripts (like config sync) without clear user approval.
- When a skill has both a plan and a prompt, keep them in separate files: plan in `.agents/plans/`, prompt in `.agents/prompts/`. The plan describes when, why, and how to verify; the prompt describes how to instruct the model during execution. Do not merge.

### OpenSpec relationship

For migrated plan-backed workflows in `aiscr-management`, the reusable plan remains the execution and governance layer while the persistent requirement contract now lives in `openspec/specs/`. Use the plan to decide when and how to execute; use the OpenSpec capability spec to understand the stable behavioral contract being executed or changed.

| Workflow skill | OpenSpec capability |
| --- | --- |
| `aiscr-config-sync` | `openspec/specs/agent-config-distribution/spec.md` |
| `aiscr-governance-bootstrap` | `openspec/specs/repository-governance-setup/spec.md` |
| `aiscr-doc-hygiene-audit` | `openspec/specs/documentation-consistency/spec.md` |
| `aiscr-hooks-governance` | `openspec/specs/ai-automation-governance/spec.md` |
| `aiscr-release-notes` | `openspec/specs/release-documentation/spec.md` |
| `aiscr-api-doc-alignment` | `openspec/specs/api-specification-sync/spec.md` |
| `aiscr-ci-review-integration` | `openspec/specs/ci-artifact-review/spec.md` |
| `aiscr-incident-postmortem` | `openspec/specs/incident-documentation/spec.md` |
| `aiscr-security-ai-usage` | `openspec/specs/security-privacy-ai-usage/spec.md` |
| `aiscr-plugins-enablement` | `openspec/specs/plugin-coverage/spec.md` |
| `aiscr-automation-recommendations` | `openspec/specs/openspec-requirement-governance/spec.md` |
| `aiscr-sibling-branch-audit` | `openspec/specs/sibling-branch-inventory/spec.md` |
| `aiscr-port-workspace-safety-config` | `openspec/specs/workspace-safety-config/spec.md` |
| `aiscr-review-pr` | `openspec/specs/pr-review-workflow/spec.md` |
| `aiscr-prod-ui-crawl-review` | `openspec/specs/production-ui-verification/spec.md` |
| `aiscr-docs-language-review` | `openspec/specs/docs-language-quality/spec.md` |
| `aiscr-agent-vendor-introduction` | `openspec/specs/agent-vendor-onboarding/spec.md` |
| `aiscr-ci-scriptification` | `openspec/specs/ci-plan-scriptification/spec.md` |
| `aiscr-overhead-evaluator` | `openspec/specs/overhead-measurement/spec.md` |
| `aiscr-overhead-optimizer` | `openspec/specs/plugin-coverage/spec.md` |

### Workflow skills per `AGENT_FOLDERS` root (e.g. `.cursor/`, `.claude/`, … — see `repos.toml` / `agent_tool_feature_matrix.md`)

**One skill entry point per workflow and per slug across every emitted `skills/` tree.** **Mechanics:** edit `.agents/canonical_configs/workflow_skills/<slug>.md` (the single source of truth for the workflow body), then run `python .agents/scripts/generate_workflow_skills.py` - this writes full readers to `.cursor/skills/` and routing/safety stubs to the non-Cursor repo-root `<tool>/skills/` trees. `validate_tool_parity.py` enforces canonical documents, guardrails, pointers, target existence, and vendor frontmatter drift under the **`parity.*`** ids catalogued in `governance_stable_ids.md` (not legacy numeric rule labels). **Vendor-specific** rule and skill load paths (e.g. `.gemini/context/`, VS Code settings) live in `agent_tool_feature_matrix.md` and each product's entry doc (`governance_by_tool.md`) - not duplicated here.

---

### Candidate skills and their building blocks

The following entries are plan-backed skills (each has a plan in `.agents/plans/`). Prompts without an accompanying plan are used directly in the target repo and are not listed here.

#### 1. `aiscr-governance-bootstrap`

- **Purpose**: Bootstrap and maintain AIS CR–style governance and `.agents/` structure in a new or existing repo as a **bidirectional alignment loop** with five mutually exclusive modes (`bootstrap-mode-greenfield`, `bootstrap-mode-introduce-openspec`, `bootstrap-mode-align`, `bootstrap-mode-audit`, `bootstrap-mode-reverse-surface`; see `governance_stable_ids.md` Bootstrap modes). The durable behavioral contract lives in `openspec/specs/repository-governance-setup/spec.md`.
- **OpenSpec capability**: `openspec/specs/repository-governance-setup/spec.md`
- **Plan**: `governance-bootstrap.plan.md` as the execution-layer workflow and operator runbook (Step 1 mode detection + confirmation; mode-specific Steps 3x/3y/3z/3w; idempotency contract; edge-case guardrails)
- **Prompts**: `.agents/prompts/repository_setup.md` (mode-aware generation rules, reverse-flow body template, `.agents/local_overrides.toml` shape); when entering optional phases, `.agents/prompts/asset_port_instructions.md` and/or `.agents/prompts/redundant_assets_cleanup_instructions.md` (plan specifies which context to load per phase).
- **Canonical sibling list**: `.agents/canonical_configs/references/ecosystem_map.md`. Load when generating Ecosystem connection or listing related repos; after adding a repo to local_configs, update the map (Step 8 or use aiscr-ecosystem-mapper skill).
- **Mode-detection inputs (target-side):** target's `openspec/config.yaml` and `.agents/local_overrides.toml` when present. **Hub baseline reference:** committed state of `.agents/canonical_configs/`, `workflow_skills/`, `governance_rules/`, and canonical references at session start.
- **Inputs/Outputs:** repository path/type, desired intent (fresh/introduce/align/audit/surface), create/overwrite confirmation, optional SOURCE/cleanup/propagation → (greenfield) updated `README*`, `CONTRIBUTING.md`, `AGENTS.md`, `.agents/` tree; (introduce-openspec) new `openspec/` tree only; (align) surgical per-path fixes + refreshed `.agents/local_overrides.toml`; (audit) drift and conformance report (stdout or optional persisted `.agents/reports/conformance/`); (reverse-surface) drafted backlog body for user-invoked `/aiscr-note-idea <slug>` in hub; optional ported assets and cleanup/propagation reports.
- **Iron laws:** never target the hub from itself; never write to hub paths from a sibling-side run; never auto-invoke `/aiscr-note-idea`; never proceed past mode proposal without explicit user confirmation; never honour an override that weakens a hub-required minimum.

#### 2. `aiscr-doc-hygiene-audit`

- **Purpose**: Run a documentation hygiene audit and apply safe, governance‑aligned fixes.
- **Plan**: `doc-hygiene-audit.plan.md`
- **Prompts**: `.agents/prompts/audit_doc_hygiene.md`
- **Inputs/Outputs:** target repo path; report-only vs report+safe-fixes → audit report under `.agents/reports/`, optional reviewed fixes.

#### 3. `aiscr-hooks-governance`

- **Purpose**: Review and harden AI‑related automation and hooks in a repo while the durable behavioral contract lives in `openspec/specs/ai-automation-governance/spec.md`.
- **OpenSpec capability**: `openspec/specs/ai-automation-governance/spec.md`
- **Plan**: `hooks-governance.plan.md` as the execution-layer workflow and operator runbook
- **Prompts**: may reuse local prompts or ad‑hoc instructions.
- **Inputs/Outputs:** target repo path; hooks-only, skills-only, or full automation scope → recommendations and, if approved, updated automation configs.

#### 4. `aiscr-api-doc-alignment`

- **Purpose**: Align API specs and documentation in API‑focused repos.
- **Canonical sibling list**: `.agents/canonical_configs/references/ecosystem_map.md`. Load when listing in-scope API/docs-api and consumer repos; align plan `relatedRepos` with the map. After run, if local_configs or related repos changed, update the map (use aiscr-ecosystem-mapper or procedure in ecosystem_map.md), keep plan `relatedRepos` in sync, and update canonical_workflows_context and this mapping if the API doc alignment workflow context or outputs changed.
- **Plan**: `api-doc-alignment.plan.md`
- **Prompts**: none specific; may use ad‑hoc instructions.
- **Inputs/Outputs:** API repo path and OpenAPI/docs entry points → updated docs/specs and governance notes on canonical sources.

#### 5. `aiscr-incident-postmortem`

- **Purpose**: Help document incidents and postmortems in a consistent way.
- **OpenSpec capability**: `openspec/specs/incident-documentation/spec.md`
- **Prompts**: `.agents/prompts/postmortem_template.md` (to be created per service repo).
- **Inputs/Outputs:** incident metadata (time, impact, logs, timeline) and service id → `INC-*.md` under `.agents/reports/incidents/`, optional follow-up tasks.

#### 6. `aiscr-automation-recommendations`

- **Purpose**: Maintain `.agents/canonical_configs/references/automation_recommendations.md` as a living document.
- **OpenSpec capability**: `openspec/specs/automation-patterns/spec.md`
- **Prompts**: none specific; uses spec and manual input.
- **Inputs/Outputs:** maintainer feedback and observations from repos → updated recommendations doc, follow-up issues/PRs.

#### 7. `aiscr-security-ai-usage`

- **Purpose**: Apply and validate security- and privacy-aware AI usage rules while the durable behavioral contract lives in `openspec/specs/security-privacy-ai-usage/spec.md`.
- **OpenSpec capability**: `openspec/specs/security-privacy-ai-usage/spec.md`
- **Plan**: `security-ai-usage.plan.md` as the execution-layer workflow and operator runbook
- **Prompts**: possible future security‑focused prompts per repo.
- **Inputs/Outputs:** target repo path and sensitive-surface description → updated governance/prompts, checklist or adherence report.

#### 8. `aiscr-plan-builder`

- **Purpose**: Create new OpenSpec requirement surfaces by default and only create reusable `.agents/plans/` artifacts when the workflow remains execution-layer or meta-governance in `aiscr-management`.
- **Plan**: `plan-builder.plan.md`
- **Prompts**: `.agents/prompts/plan_builder.md`
- **Inputs/Outputs:** capability/change name, optional repos/categories, scope, schema choice, and high-impact script guardrails → validated OpenSpec `spec.md` and optional change artifacts, plus `.agents/plans/` updates only when a meta workflow still needs a reusable plan file.

#### 9. `aiscr-plugins-enablement`

- **Purpose**: Enable and use relevant plugins (MCP, skills, hooks) across IDE assistants; document and apply fallbacks when a plugin is not installed or unavailable while the durable behavioral contract lives in `openspec/specs/plugin-coverage/spec.md`.
- **OpenSpec capability**: `openspec/specs/plugin-coverage/spec.md`
- **Implemented**: Canonical workflow skill sources under `.agents/canonical_configs/workflow_skills/`, generated into repo-root assistant `skills/` trees; propagate to sibling repos via `sync_agent_configs.py ApplyLocalConfigsToRepos` (run with `--dry-run` first).
- **Plan**: `plugins-enablement.plan.md` as the execution-layer runbook for Mode A/B/C workflow, audit steps, and validation.
- **Prompts**: none specific; plan and `plugin_enablement_and_fallback.md` drive execution.
- **Inputs/Outputs:** target repo/scope and tooling focus → updated `plugin_enablement_and_fallback.md`, automation_recommendations cross-links, optional hooks-governance references.

#### 10. `aiscr-config-sync`

- **Purpose**: Execute the management-hub config-distribution workflow while the durable behavioral contract lives in `openspec/specs/agent-config-distribution/spec.md`.
- **OpenSpec capability**: `openspec/specs/agent-config-distribution/spec.md`
- **Pre-flight**: Before `orchestrate_local_agent_sync.py` **inspect** or **apply**, run **`aiscr-sibling-branch-audit`** (`sibling_repos_branch_audit.py`) so siblings get `git fetch --prune` locally and unpublished/upstream-gone branches are surfaced; inspect alone does not replace this.
- **Canonical sibling list**: `.agents/canonical_configs/references/ecosystem_map.md`. When listing in-scope repos, align with the map; after local_configs subfolders change, refresh the map (see plan After run / Validation or use aiscr-ecosystem-mapper skill).
- **Plan**: `config-sync.plan.md` as the execution-layer orchestration and operator runbook.
- **Scripts**: `sibling_repos_branch_audit.py` (pre-flight), `orchestrate_local_agent_sync.py`, `sync_agent_configs.py`, `report_local_configs_sync_matrix.py`; see `.agents/scripts/README.md`.
- **Repo-policy evaluation:** After branch audit, run `report_local_configs_sync_matrix.py` before inspect; optionally compare resolved `repos.toml` sync recipes or overrides across repos sharing the same `type` in `repos.toml` for commendable peer alignment; approve repo-policy changes before `populate --apply`; re-run `--strict` after repo-policy edits. See `config-sync.plan.md` for the execution-layer runbook. When **`mandatory_vendor_doc_urls.toml`** or **`agent_tool_feature_matrix.md`** changes in the same work, also run **`validate_agent_tool_feature_matrix.py`** and **`validate_matrix_local_configs_cells.py`** (sync matrix alone does not cover every TOML cell).
- **References**: `.agents/canonical_configs/references/specialized_sync_assets.toml`, `.agents/canonical_configs/references/plan_demotion_policy.md` (sync-adjacent decisions and criteria; full plan inventory workflow: **`aiscr-plans-validation`** / `plans-validation.plan.md` Step 8).
- **Plan inventory / demotion**: **`aiscr-plans-validation`** / `plans-validation.plan.md` **Step 8** and `plan_demotion_policy.md`.
- **Prompts**: `.agents/prompts/sync_cleanup_review.md`, `.agents/prompts/specialized_asset_review.md`.
- **Core rules (summary):** Default automation: inspect and dry-run; apply stays human-approved; same-name intended mirrors stay byte-identical; specialization must be registry-backed.

#### 10a. `aiscr-agent-vendor-introduction`

- **Purpose**: Execute vendor onboarding while the durable behavioral contract lives in `openspec/specs/agent-vendor-onboarding/spec.md`.
- **OpenSpec capability**: `openspec/specs/agent-vendor-onboarding/spec.md`
- **Plan**: `agent-vendor-introduction.plan.md` as the phased execution workflow
- **Prompt**: `.agents/prompts/agent_vendor_introduction.md`
- **Registry**: `agent_tool_feature_matrix.md`, `mandatory_vendor_doc_urls.toml`
- **Sync policy**: `sync_policy.py` — `AGENT_FOLDERS`, `REPO_ROOT_HUB_ENTRY_DOCS`, `REPO_ROOT_SYNC_IDS`
- **References**: `config-sync.plan.md` (sync vocabulary), `.agents/canonical_configs/governance_rules/aiscr-ecosystem-governance.md` (**Cross-tool entry-point anti-drift** when chartered), `governance_stable_ids.md`
- **Scripts**: `generate_workflow_skills.py`, `generate_agent_definitions.py`, `generate_governance_rules.py`, `validate_tool_parity.py`, `validate_agent_tool_feature_matrix.py`, `validate_matrix_local_configs_cells.py`
- **Session charter**: Records vendor class, surfaces in scope, and whether Phase 6 (cross-tool **`aiscr-*`** registration) applies.
- **Core rules (summary)**: Charter records vendor class and surfaces; matrix rows honest; sync policy aligned; validation suite passes; Phase 6 only when chartered.

#### 10b. `aiscr-ecosystem-mapper`

- **Purpose**: Create, refresh, or update `.agents/canonical_configs/references/ecosystem_map.md` so it stays the single source of truth for AIS CR siblings; optionally check consistency between the map and `.agents/local_configs/` subdirs.
- **Rule**: The map includes **only** repos that have a subfolder under `.agents/local_configs/`. Do not add repos that merely exist in Git or are mentioned in plans; add a repo to the map only after it has been added to local_configs.
- **Plan**: No separate plan file; procedure in `.agents/canonical_configs/references/ecosystem_map.md` (“When to refresh”, “How to use”) and ecosystem-map-and-cleanup-improvements plan. **Artefact**: `.agents/canonical_configs/references/ecosystem_map.md`.
- **Inputs/Outputs:** add | remove | refresh | check; optional repo metadata when adding → updated `ecosystem_map.md`, optional consistency report.
- **Governance**: Skill only edits ecosystem_map.md and optionally runs read-only checks; no high-impact scripts. Log usage when updating the map (`model-logging.md`, `usage-logging.md`).

#### 12. `aiscr-ci-review-integration`

- **Purpose**: Integrate `review_tools.py` and related AI-review checks into CI for web application repositories so that review runs consistently in CI, not only locally.
- **Plan**: `ci-review-integration.plan.md`
- **Prompts**: none specific; plan and repo CI docs drive execution.
- **Inputs/Outputs:** webapp repo path; optional review_tools tasks for PRs vs scheduled → updated CI workflow(s), governance docs for CI + AI review.

#### 14. `aiscr-plans-validation`

- **Purpose**: Run recurring validation of `.agents/plans/*.plan.md` and helper scripts so that schema, content conventions, and reset behaviour stay consistent; support CI integration and documentation.
- **Plan**: `plans-validation.plan.md`
- **Plan inventory / demotion (periodic)**: `plans-validation.plan.md` **Step 8** — review keep vs demote for each `.plan.md`, apply `.agents/canonical_configs/references/plan_demotion_policy.md`, record outcomes there; optionally refresh `central_assets_inventory.md` when plans are added or removed.
- **Scripts**: `validate_plans.py`, `reset_plan_status.py`; see `.agents/plans/README.md` (Strategie validace).
- **Prompts**: none; plan and scripts/README drive execution.
- **Inputs/Outputs:** scope (local vs CI); optional strict/dry-run prefs → validation report, fixes to plans/README/CI, updated workflow docs.

#### 15. `aiscr-ci-scriptification`

- **Purpose**: Evaluate which prompts, plans, or skills can be turned into reproducible scripts; define script-only steps and CI jobs so validation and hygiene run in CI without agent calls; update READMEs and governance with script vs prompt split.
- **OpenSpec**: `openspec/specs/ci-plan-scriptification/spec.md` — behavioral requirements, scriptification methodology, capability categories, CLI conventions, repo-type adaptation patterns.
- **Plan**: `ci-scriptification.plan.md` — execution procedures and operator runbook.
- **Prompts**: none; spec and plan drive execution. **Scripts**: as per plan (e.g. plan/schema validation, todo/reset dry-run, doc-hygiene discovery/link-check); CI workflow in the target repo.
- **Inputs/Outputs:** target repo path; management vs application scope → scriptification inventory, new/extended scripts and CI jobs, updated READMEs/governance, testing concept.

#### 17. `aiscr-docs-language-review`

- **Purpose**: Run a detailed language and typo review of all repository documentation; enforce user-facing docs in Czech, agent-facing in English, README English equivalents, report language split (Czech with agent parts in English), and GitHub-compatible Markdown formatting while the durable behavioral contract lives in `openspec/specs/docs-language-quality/spec.md`.
- **OpenSpec capability**: `openspec/specs/docs-language-quality/spec.md`
- **Plan**: `docs-language-review.plan.md` as the execution-layer workflow and operator runbook
- **Prompts**: none; plan and `docs_language_classification.md` drive execution.
- **Inputs/Outputs:** target repo (default: aiscr-management); optional doc scope → updated `docs_language_classification.md`, README_en gaps, language/typo/GFM fixes, CONTRIBUTING/.agents README references.

#### 18. `aiscr-release-notes`

- **Purpose**: Generate semantic, issue-aligned release notes in GitHub Wiki–compatible Markdown for a target AIS CR repo while the durable behavioral contract lives in `openspec/specs/release-documentation/spec.md`; optionally backfill missing past releases (skipping pre-releases); store output in `.agents/reports/release-notes/`; optional push to GitHub release body with propagation scope single / range / all (user opt-in, tag-based only; gh or GitHub MCP); propagate recommended `.github/release.yml` to reports and optionally to the target repo with user approval. `.github/release.yml` format follows [GitHub Docs](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes) (categories and optional exclude).
- **OpenSpec capability**: `openspec/specs/release-documentation/spec.md`
- **Plan**: `release-notes.plan.md` as the execution-layer workflow and operator runbook
- **Prompts**: none; plan and GitHub API / `gh` CLI drive execution.
- **Inputs/Outputs:** target repo; single vs backfill mode and tags; optional release.yml propagation and release-body scope → Markdown under `.agents/reports/release-notes/`, optional `release.yml` artefacts and semantic grouping; no wiki push; optional release-body push when opted in.

#### 19. `aiscr-canonical-workflows-context`

- **Purpose**: Run standard management-repo workflows with the correct context loaded (what to read first, which plan/script, in what order); the canonical registry pair (`canonical_workflows_context.toml` + `canonical_workflows_context.md`) maps each workflow to ordered context and plan/script.
- **Plan**: `canonical-workflows-context.plan.md`
- **Prompts**: none; plan and reference drive execution.
- **Inputs/Outputs:** workflow name or task description → context-loaded execution (identify row → load paths in order → run per governance).

#### 20. `aiscr-canonical-workflows-context-maintenance`

- **Purpose**: Maintain the canonical-workflows-context routing layer: update the workflow registry/reference pair, keep the execution and maintenance workflow skills aligned, refresh direct doc consumers, and regenerate the touched workflow surfaces.
- **Plan**: `canonical-workflows-context-maintenance.plan.md`
- **Prompts**: none; plan drives execution.
- **Inputs/Outputs:** intent to maintain workflows context → registry/reference/skill/doc updates and validation per maintenance plan.

#### 21. `aiscr-sibling-branch-audit`

- **Purpose**: Audit local branches across sibling AIS CR repositories: fetch and prune remote-tracking refs locally, list detached or unpublished local branches, produce a per-repo report so the user can decide what to do (delete local, push to create remote, keep). Never change the remote while the durable behavioral contract lives in `openspec/specs/sibling-branch-inventory/spec.md`.
- **OpenSpec capability**: `openspec/specs/sibling-branch-inventory/spec.md`
- **Canonical sibling list**: `.agents/canonical_configs/references/ecosystem_map.md`. Load when resolving repo list and paths.
- **Script**: `.agents/scripts/sibling_repos_branch_audit.py` — execution via script directly (plan deleted)
- **Prompts**: none; spec and script README drive execution.
- **Inputs/Outputs:** repos-root or paths; optional repo subset and output path → per-repo branch report (unpublished/upstream-gone); no automatic remote changes.

#### 22. `aiscr-port-workspace-safety-config`

- **Purpose**: Merge validated **safety templates** from `aiscr-management` (`.agents/canonical_configs/safety_config_templates/`) into the user's app-level Cursor `sandbox.json`, Codex `config.toml`, and Claude `settings.json` using `port_workspace_safety_config.py` while the durable behavioral contract lives in `openspec/specs/workspace-safety-config/spec.md`. Template keys override matching keys; extra user keys are preserved where the merge logic allows. Missing **`jsonschema`** / **`tomli-w`** may be **auto-installed** via `requirements_subset_install.py` (pins read from `requirements-ci.txt`); prefer repo **`.venv`**. Timestamped `.bak.*` files only with **`--backup`** (default off).
- **OpenSpec capability**: `openspec/specs/workspace-safety-config/spec.md`
- **Plan**: `port-workspace-safety-config.plan.md` as the execution-layer workflow and operator runbook
- **Prompts**: none; script README and plan drive execution.
- **Inputs/Outputs:** optional `--target-dir`, `--backup`, tool skips, `--list` / `--dry-run`, explicit confirm before writes → merged or previewed app-level configs.
- **Governance**: Do not run `sync_agent_configs.py` or sibling-repo writes as part of this skill without a separate approved plan; respect config protection in `AGENTS.md` and `.cursor/rules/workspace-boundary-safety.mdc`.

#### 23. `aiscr-note-idea`

- **Purpose**: Capture a new user-supplied idea as an OpenSpec backlog change under `openspec/changes/<slug>/` using the lightweight `backlog` schema and its short `proposal.md` header/body shape. Refreshes the generated backlog inventory (`.agents/backlog-overview.md`) and stops before promotion into governance-driven planning.
- **Plan**: none; backlog proposal creation only. Backlog schema and template: `openspec/schemas/backlog/`.
- **Prompts**: none; user provides the idea text.
- **Inputs/Outputs:** idea slug, body, optional clarifications → new backlog change under `openspec/changes/<slug>/` with `.openspec.yaml` (`schema: backlog`), `proposal.md`, and refreshed `.agents/backlog-overview.md`; no broader governance edits.

#### 24. `aiscr-plan-from-idea`

- **Purpose**: Start from a user-chosen OpenSpec backlog proposal (`openspec/changes/<slug>/proposal.md`), run one governed structured exploration pass, then enter one formal planning phase that produces a structured plan with an impacts assessment and a go/no-go recommendation; after approval, promote the same slug into a full governance-driven OpenSpec change and stop before implementation. The backlog proposal headers seed Impacts and planning scope, and directly related backlog proposals may be inspected only when needed for the same planning task.
- **Plan**: none as backing plan; behaviour is defined in the command/skill body itself and produces governance-driven OpenSpec artifacts under the same slug.
- **Prompts**: `.agents/prompts/plan_builder.md` (used during planning phase to shape the output plan).
- **Inputs/Outputs:** backlog slug and optional scope clarification → structured exploration output (problem framing, impacts, trade-offs, open questions, readiness signals) plus planning output with Impacts and Evaluation/recommendation, then `proposal.md`, `specs/`, `design.md`, and `tasks.md` under the same OpenSpec change slug after approval; refreshed `.agents/backlog-overview.md`; readiness-sensitive next step `/opsx:continue <slug>` or `/opsx:apply <slug>`; implementation intentionally not started.

#### 25. `aiscr-review-pr`

- **Purpose**: End-to-end GitHub PR review workflow: auto-discover prior review context
  (most recent submitted review, PR author's response, existing inline threads), structure
  findings into four severity-labelled buckets (resolved / disputed / not addressed / new),
  and post results as a formal GH review with inline comments and thread replies via the
  GH API. Supports optional bot identity via `GH_TOKEN`.
- **OpenSpec capability**: `openspec/specs/pr-review-workflow/spec.md`
- **Plan**: `review-pr.plan.md` as execution-layer orchestration
- **Script**: `.agents/scripts/review_pr.py`
- **Inputs/Outputs:** PR number; optional `GH_TOKEN` → formal GH review (body + grouped inline comments), thread replies, returned URLs.

#### 26. `aiscr-overhead-evaluator`

- **Purpose**: Measure and estimate the whole-workflow token cost and friction of the current assistant/tool
  setup (baseline, workflow body, explicit transitive references, runtime surcharge, plugin/skill/agent overhead).
  Produces Markdown or JSON reports under `.agents/reports/overhead/`. Read-only; no approval required for analysis.
- **OpenSpec capability**: `openspec/specs/overhead-measurement/spec.md`
- **Script**: `.agents/scripts/measure_workflow_overhead.py` - execution via script directly (plan deleted)
- **Prompts**: none; workflow is entirely script-driven.
- **Inputs/Outputs:** `--dry-run`, `--repo-root`, `--date`, `--output {markdown,json}`, `--verbose` → overhead report under `.agents/reports/overhead/` (summary, detail, workflows, session estimate, redundancy, recommendations, delta).

#### 26a. `aiscr-overhead-optimizer`

- **Purpose**: Turn whole-workflow overhead and sanitized cross-user usage evidence into reactive optimization findings.
  It identifies skills/agents that do not appear in measured contributors' recent session windows and estimates
  the per-session baseline cost of those extras without changing workstation configuration automatically.
- **OpenSpec capability**: `openspec/specs/plugin-coverage/spec.md`
- **Scripts**: `.agents/scripts/aggregate_skill_usage.py`, `.agents/scripts/log_skill_usage.py`, `.agents/scripts/measure_workflow_overhead.py`
- **Prompts**: none; workflow is script- and report-driven.
- **Inputs/Outputs:** local raw NDJSON under the resolved sink (default gitignored `<repo>/.venv/aiscr-skill-usage/raw/`), cumulative sanitized stats under `.agents/reports/overhead/skill-usage/stats.json`, derived observed summaries, and reactive findings tied to measured plugin overhead.

#### 27. `aiscr-prod-ui-crawl-review`

- **Purpose**: Optional **live deployed** UI and on-page SEO verification (plus optional Tier-2 signals) for **any user-facing environment reachable over the public internet** (webapps, public docs/marketing/static sites, etc.), as part of the target repo's `review_codebase.md` workflow—typically optional task **T12** `deployed_ui_analysis` (or a session equivalent) with `deployed_verify:` URL allowlists in `review_config.yaml` while the durable behavioral contract lives in `openspec/specs/production-ui-verification/spec.md`. **Not** GitHub PR review; **not** a substitute for private-only or non-HTML API testing unless those URLs are explicitly in scope.
- **OpenSpec capability**: `openspec/specs/production-ui-verification/spec.md`
- **Plan**: `prod-ui-crawl-review.plan.md` as the execution-layer runbook for Tier 1/2 signal collection, staging-first execution, and output generation.
- **Prompts**: `.agents/prompts/repository_setup.md` (optional deployed verification subsection for new/adopting repos).
- **Inputs/Outputs:** checkout with `review_codebase.md` + `review_config.yaml`, allowlisted public URLs, prod approval when needed → `deployed_ui_analysis.json`, T12-style report, optional backlog/cache updates per repo rules.

**Background examples:** see `workflows/prod-ui-crawl-review.md`. Narrative language follows **each target repo's** `review_codebase.md` rules.

---

### Workflow-to-plan registry

The sole active workflow-to-plan registry is the pair:

- `.agents/canonical_configs/references/canonical_workflows_context.toml` — machine-authoritative slug and `plan_file` ownership
- `.agents/canonical_configs/references/canonical_workflows_context.md` — human-readable workflow routing, context order, and fallback notes

Do not maintain a second plan-file index in this document. Update the registry pair directly when a workflow gains, loses, or changes a backing plan.

---

### Next steps for implementing the skillset

- For each, create concrete skill/config definitions in the relevant tool ecosystems (e.g. **Cursor** and other assistants per `AGENT_FOLDERS`), using the interfaces above.
- Add references to the new skills into `AGENTS.md` and `.agents/canonical_configs/references/automation_recommendations.md` once they are live.
