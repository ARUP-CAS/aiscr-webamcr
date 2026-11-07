---
name: aiscr-review-codebase
description: Use when the user asks for a full codebase review or incremental review
  update of a target AIS CR repository. Detect scope, propose with evidence, and obtain
  confirmation; the management hub is excluded. Own the cache, report schema, and
  findings handoff, with English-default output and repository-local review_config.toml
  scope.
effort: high
license: CC-BY-4.0
author: AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
---

<!-- SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- aiscr:compiled=aiscr-review-codebase -->
<!-- delivery-version: b257a1a89279be5e17cda3c133aa77b8c4d2706c 2026-11-07T11:18:12+01:00 -->

<!-- aiscr:entry-scope -->

**Entry scope (compiled)**

- This `.claude/skills/` skill is self-contained; use the workflow body below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-review-codebase — codebase-review lifecycle (full and update)

Run the codebase-review lifecycle against a **target repository** — the repository this workflow is invoked in, or a registered sibling designated from the management hub (see *Execution tiers*).
Repo-specific scope (apps, file lists, vendored exclusions, thresholds, analysis families) stays in the target repo's `.agents/config/review_config.toml`; the detailed runbook is the Steps section below.

**When to use vs alternatives:** Use this for a **static codebase review** (architecture, data layer, security, async, frontend, docs, CI/CD, scripts) producing `.agents/reports/review_reports/` and analysis JSONs.
For **GitHub PR review** use `/aiscr-review-pr` (`github_pr_review.py`); for **live deployed UI / SEO** checks use `/aiscr-review-prod-ui` (optional T12); for **API spec/doc alignment** use `/aiscr-review-api-doc` (optional T13).
**Not in scope:** GitHub PR review (`aiscr-review-pr`, `github_pr_review.py`), deployed live-UI/SEO verification, and API specification/doc alignment are separate workflows — do not conflate them with the static codebase review here.

Consume `aiscr-review-conduct` through the invoking repository's delivered rule reader; this body owns the procedure and output destination.

## Phase awareness

This is an **operational execution skill**: its subject is a codebase-review pass in the target repository, not spec-governed repository state.
It runs without gating on OpenSpec context and never invokes `/openspec-propose`; when a domain spec governs the review work it is honored as the durable contract.
Execution boundaries: produce the review pass for the approved task; do not merge or modify product code beyond the agreed pass, and do not create new OpenSpec changes, promote backlog items, or expand scope past the agreed task.

The workflow exposes two modes — `codebase-review-mode-full` and `codebase-review-mode-update` — selected by the `detect → propose-with-evidence → user-confirms` pattern; see *Modes and dispatch* for the selection table and the verification rules.
It **refuses** to run with the management hub `aiscr-management` as the target.

## Context to load first

1. The target repository's `AGENTS.md` — repo-specific agent instructions take precedence.
2. `.agents/config/review_config.toml` (target) — Tier 3 scope: app/module names, key file lists, vendored exclusions, analysis families, severity thresholds, task-size guardrails, `phase_outputs` mapping, `open_issues`.
3. `.agents/config/review_cache.json` (target) — task status, file hashes, sub-task entries, `last_updated`.
4. `.agents/reports/review_reports/` (target) — presence of final_audit.md and per-task reports.

If `.agents/scripts/codebase_review.py` exists in the target repo, use it for mechanical detection (`hash`, `status`, `coverage-gaps`, `cross-validate`, `id-inventory`, `lint-artifacts`, `issue-transfer`, `record-issue`, `reconcile-issues`, `all`); it is repo-local plumbing, not a hub contract, and the canonical engine resides in the hub script tree at the same path.

## Steps

### Execution tiers

This workflow supports both execution tiers.
Their semantics — target designation and resolution, eligibility, whose governance binds, and write scope — are defined under *Workflow execution tiers* in the `aiscr-ecosystem-governance` governance rule.
This body declares applicability and does not restate them.

- **In-repo tier.**
  A developer runs the review in their own checkout; the target repository is the one the workflow is invoked in.
- **Hub-cockpit tier.**
  A maintainer runs the review from the management hub against a registered sibling the operator names.
  The run reads that sibling's `AGENTS.md`, review configuration, cache, and reports, and writes every artifact in its working tree.

The review takes no target argument: the bundled engine receives the resolved target through the `--repo-root` argument it already accepts.
The detect phase evaluates enrolment **under the resolved target repository root** — a `review_config.toml`, `review_cache.json`, or `review_reports/` in the invoking checkout is not evidence about the target.

Both tiers share the same target guarantees: the management hub is never a review target, and a repository with no review setup is reported not-enrolled rather than scaffolded.

### Context

This workflow lives in **aiscr-management** (the AIS CR / ARUP-CAS management hub) and defines the codebase-review lifecycle for any AIS CR repository.
The **target repository** is the repository a run is bound to under the tier it uses — the invoking checkout in the in-repo tier, the designated sibling in the hub-cockpit tier — and every "target repo" reference below means that repository in either case.
The management hub `aiscr-management` is **refused** as a target in both tiers (it carries no review configuration or state by design); running *from* the hub does not make the hub a permissible target.

The workflow owns the lifecycle, policy, and schemas; **repo-specific scope** (app and module names, key file lists, vendored exclusions, analysis families, severity thresholds, task-size guardrails, the `phase_outputs` mapping, and the GitHub open-issues count) lives in the target repo's `.agents/config/review_config.toml` (Tier 3 — see *Three-tier authority split*).
Per-repo state lives in `.agents/config/review_cache.json` and `.agents/reports/review_reports/`.

A repository is **enrolled** in the lifecycle when it has review setup (`review_config.toml`, `review_cache.json`, or `review_reports/`).
Receiving the skill stub through the shared sync surface does **not** enrol a repo: the workflow refuses to auto-scaffold review artifacts in a repo that has none.
Initial enrolment is a deliberate, separately-approved step (governance bootstrap, or a controlled change that introduces `review_config.toml`) — **not** something the sibling-delivery tooling performs.

Each optional lens is switched by the per-analysis toggle in the target repository's `review_config.toml` — not by a hub-side enrollment judgment — and writes into `review_reports/` in the target's established style.

### Modes and dispatch

Two modes are selected by the bootstrap-style `detect → propose-with-evidence → user-confirms` pattern (stable ids under *Codebase-review modes* in the governance stable-ids reference):

| Mode | Stable id | When proposed |
|------|-----------|---------------|
| Full pass | `codebase-review-mode-full` | No prior pass, a partial cache to resume, or a full re-run is warranted |
| Incremental update | `codebase-review-mode-update` | A completed pass exists and the goal is a delta refresh |

The detect phase runs **even when the operator typed a mode argument**, so the requested mode is verified against evidence: **refuse** when incompatible (for example `update` requested but no prior pass exists → recommend `codebase-review-mode-full`); **warn** on partial match; reject any other mode value, stating both supported ids.
Mode auto-detection is a **recommendation, not a decision** — present the proposed mode with its evidence and obtain explicit user confirmation before any write.
Cache-aware resumption is **intrinsic to `codebase-review-mode-full`**; there is no third mode.

**Datetime discipline.**
Apply spec requirement *Review timestamps use verifiable sources*.

### Canonical lifecycle phases

Phase names are **abstract and stack-neutral**.
The target repo's `review_config.toml` `phase_outputs` mapping binds each canonical phase id to that repo's concrete analysis output filenames (preserved without rename); per-task report headers MAY append a stack-specific descriptor for reader clarity (for example *T03 — Data-layer analysis (Django ORM)* or *T03 — Data-layer analysis (Solr / XSLT)*), but cross-references in `final_audit.md` and the findings sources use the canonical phase id.

**Full pass (T01–T11):**

- **T01 — Repository map.**
  Structural index: directories and their purpose, application/module boundaries, file sizes and types, infrastructure components.
  Update whenever structure changes.
- **T02 — Dependency graph.**
  Internal and external dependencies; production code only (exclude test directories from the architectural import graph).
  Distinguish module-level imports (load-time, higher circular-dependency risk) from lazy imports.
  Detect circular dependencies (module-level vs lazy carry different severity per Tier 3 thresholds), high fan-in modules (decomposition candidates) and high fan-out modules (high-responsibility candidates), and outdated dependency versions.
  Record architectural issues in `refactoring_backlog.toml`.
- **T03 — Data-layer analysis.**
  Persistence and data-access patterns: models/schemas read directly (not via summary), migrations, query patterns, eager-vs-lazy loading, signal/handler chains that can cause hidden N+1 queries, custom managers/query helpers.
  Detect N+1 queries, counting anti-patterns, missing eager-loading, missing change-detection caching, deprecated data-layer APIs, unindexed filtered fields, and queries in templates or property methods.
  Record severe issues as bugs.
- **T04 — Build and container analysis.**
  All build/container/orchestration files and infrastructure service configs.
  Detect oversized images, build-only dependencies leaking into production images, poor layer caching, outdated/insecure base images, hardcoded secrets, incorrect secret-injection mechanisms per service, dev/prod version parity gaps, services placed in the wrong environment, multi-process containers lacking a supervisor or exec pattern, and admin/monitoring interfaces exposed without isolation or auth.
- **T05 — Security analysis.**
  Production security audit.
  Run the framework's deploy check first and record warnings.
  Inspect framework security settings (including dangerous fallback values), secrets management (distinguishing placeholder from real-looking credentials), authentication/authorization, proxy-level controls (HTTPS/HSTS/headers, defense-in-depth), CORS, CSRF, injection risks (raw queries), and XSS risks (unsafe-HTML helpers) classified by input provenance: hardcoded static → acceptable; model/DB value without escaping → medium; request/user input → high.
  Audit dependencies for known CVEs; when scanners are unavailable, record "CVE audit recommended".
  Cross-reference build-level findings from T04 by ID rather than duplicating them.
  For security-sensitive areas consider a dedicated security review before merge.
- **T06 — Async and background-processing analysis.**
  Asynchronous/scheduled task processing: task definitions, schedule configuration, retry and error handling, shared state, timeouts, routing/priority.
  Detect tasks without error handling, race conditions, long synchronous operations inside tasks, missing idempotence in critical tasks, synchronous calls that should be async, leaks in long-running tasks, and external calls without timeout or retry.
  Summarize trivial wrapper tasks; describe domain-significant tasks in detail.
- **T07 — Frontend analysis.**
  Only first-party code authored by the project's developers; skip vendored/third-party assets per `vendored_exclusions`.
  Inspect custom JS/CSS architecture, async patterns, template inline scripts (extraction candidates), server→client data-passing patterns, and CDN loading (SRI/integrity, fallback).
  Detect logic/anti-pattern errors, API-misuse silent failures, logical-operator (De Morgan) mistakes in guards, missing SRI on external `<script>`/`<link>`, missing minification of custom assets, and inconsistent data-passing.
  Third-party library internals, vendored bundles, and npm-package CVEs (the latter belong to T05) are out of scope.
- **T08 — Documentation analysis.**
  Documentation and documentation generators: site config, generator scripts (including subprocess return-code and stderr/stdout handling), auto-generated tables, license docs.
  Detect generators that may fail, fragile parsing without error handling, outdated generated content, duplication, broken/outdated links, inconsistent formatting, and docs that no longer match code behavior.
- **T09 — CI/CD analysis.**
  Automation, testing, and deployment pipeline: workflow definitions, pre-commit hooks, linting config, test infrastructure, and security/supply-chain tooling (image scanning, SBOM, signing, provenance, static analysis, dependency-update bots).
  Detect workflows without timeouts, missing coverage reporting, secrets exposed in logs, missing branch protection, suboptimal cache use, hooks that fail in CI, and missing security scanning.
  Summarize how the pipeline supports supply-chain security so T05 and T11 can cross-reference.
- **T10 — Operational scripts analysis.**
  Operational and development scripts (the repository-root scripts directory; documentation generators belong to T08).
  Treat config files (cron tables, service inis) as related artifacts, not line-by-line scripts.
  Detect missing error handling (`set -e`/`-u`/`-o pipefail` where applicable), unvalidated inputs before destructive operations, hardcoded paths/hostnames, unvalidated environment assumptions, duplicated functionality, and missing help text.
  Each issue entry carries `id`, `severity`, `summary`, affected `scripts`, and `recommendation`.
- **T11 — Final audit.**
  Consolidated synthesis written only after T01–T10 are complete.
  See *Report schema* for the fixed English section ordering.
  Run `codebase_review.py all` (when present) and verify referenced IDs before finalizing.

**Incremental update (U01–U06):**

- **U01 — Change detection.**
  Identify what changed since the last review: changed/deleted files (hash comparison), new untracked files (new source modules, build files, scripts, workflows, frontend assets, templates), and the affected phases.
- **U02 — Coverage audit.**
  Find files, modules, or directories missed or under-covered by the initial cycle (apps without data-layer coverage, custom frontend files not analyzed, uncovered scripts, new directories not in the repository map).
  Resolve small gaps in-session via the coverage-gap sub-task workflow; defer large gaps to a recommended `full` re-run with a clear action item.
- **U03 — Cross-validation and consistency.**
  Run mechanical checks (orphan bugs, backlog-prefix mismatches, severity mismatches, cache-path validity, orphan/duplicate IDs, JSON/schema/entry-completeness lint).
  Manually verify final-audit accuracy (top-findings list references valid IDs; no high-severity finding missing; section content matches task reports).
- **U04 — Spot-check findings validity.**
  Targeted (not full) re-verification: read the referenced file/line for every Critical/High bug and a sample of Medium bugs; confirm or invalidate; re-check key architectural findings; flag fixed-but-not-updated entries for status update.
- **U05 — Workflow-evolution integration.**
  Classify accumulated workflow-improvement feedback (`incorporated` / `pending` / `rejected` / `partially incorporated`) and produce a prioritized list of pending suggestions with concrete, copy-pasteable diffs for the human reviewer.
  Apply spec requirement *Workflow-evolution feedback uses hub-mediated backlog handoff* for the no-self-modification boundary and handoff path.
- **U06 — Artifact refresh.**
  Update all artifacts from U01–U05 in one atomic pass, in this order: analysis JSONs (append/update in place, never overwrite); `bugs.toml` (new + fixed-status) and `refactoring_backlog.toml`; `codebase_review.py render` to regenerate the Markdown twins; the cache (`file_hashes`, `last_updated`); and `final_audit.md` in two passes — (a) body sections to reflect the current consolidated state, (b) a dated changelog entry.
  Collect findings first, write once at U06.

U05 implementation detail: legacy `.agents/prompts/prompt_evolution/*_prompt_update.md` files are migration evidence, not active prompt patches.
Record evidence paths, proposed hub targets, and dispositions; prepare human-readable handoff candidates; keep well-formed pending suggestions non-blocking.
Do not write hub backlog items unless the user explicitly approves backlog handoff for the current review run.
Approved handoff uses `report-to-backlog-handoff` and hub note-idea workflow semantics, creates or updates only `schema: backlog` items, cites sibling evidence, and stops before planning or implementation.

#### DONE MEANS DONE

Never mark a task `done` until **every file in scope was directly read** — not via a subagent summary, search snippet, or directory listing.
If the review-complexity budget is exhausted before a phase is fully covered: split into sub-tasks, mark the completed part `done`, mark the parent `split`, and leave the remainder `pending`.
Do not silently escalate `update` mode into a `full` re-run within the same session — document the gap and recommend a separate `full` invocation.

### Cache schema

`.agents/config/review_cache.json` is repo-local and conforms to this canonical schema.
**Canonical `schema_version`: `"2"`.**

Reference format 1: [review-schemas.md](../../../.agents/skills/aiscr-review-codebase/review-schemas.md).

Required fields: `schema_version`, `last_updated`; per task `status` and (when complete) `completed_at` / `report_path`; for split phases a `sub_tasks` map whose entries carry `scope` and `report_path`; and `file_hashes` keyed by relative path.

A repo whose cache predates this schema is brought to `schema_version: "2"` by an **incremental field add** only — introduce `schema_version` and any missing fields (`sub_tasks`, `scope`, per-task `report_path`).
Do **not** move payload between fields, rename existing task or sub-task ids, or invalidate completed tasks.

### Findings schema

Review findings are **structured sources of truth**, not prose. `.agents/reports/bugs.toml` and `.agents/reports/refactoring_backlog.toml` are authored by the agent; the Markdown files `bugs.md` and `refactoring_backlog.md` are **generated twins** produced by `codebase_review.py render` and must never be hand-edited.
Tooling reads typed fields from the TOML; no machine-read field is recovered by matching a Markdown heading or a bold label.

**Canonical `schema_version`: `"1"`** for both files. `lint-artifacts` rejects an unrecognized version by name rather than reading absent fields.

`preamble` carries the file-level narrative that belongs to the document, not to a finding (the bugs header with open-issue count and status vocabulary, and the backlog note distinguishing refactoring priority from bug severity), and is part of the source so regeneration cannot discard it.

Reference format 2: [review-schemas.md](../../../.agents/skills/aiscr-review-codebase/review-schemas.md).

`alignment` is the **only** place a documented severity-versus-priority divergence is recorded. `cross-validate` reads that field; it never infers intent from wording in `description` or `recommended_fix`.

Reference format 3: [review-schemas.md](../../../.agents/skills/aiscr-review-codebase/review-schemas.md).

Required per bug: `id`, `severity`, `task`, and at least one `files` entry.
Required per backlog item: `id`, `priority`, `task`, `description`.
Severity and priority values outside the canonical vocabularies are a `lint-artifacts` error naming the offending identifier.
Both finding kinds accept optional `github_issue` and `tracking_status` fields. `tracking_status` is one of `tracked-open` or `tracked-closed` and is present only after `github_issue` resolves to an actual issue; absence remains valid for legacy or untracked findings.

**Label normalization.**
Repositories that authored backlog items with `Finding` and `Proposal` labels map them to `description` and `recommendation`.
`Impact` has no synonym and is retained as its own optional field rather than folded into `description`.

**Identifier discipline.**
A finding's identifier is durable.
Where a backlog heading carries no identifier but the repo's analysis artifacts already name one for the same finding (for example `SOLR-001` in `solr_analysis.json`, `ARCH-01` in `dependency_graph.json`), that identifier is carried forward.
Identifiers are never bound to headings by automated title similarity, and a newly assigned identifier requires maintainer review.

**Merging duplicates.**
Findings are preserved by default.
When two items describe the same defect, the superseded one is removed only with explicit maintainer approval, and the surviving item lists what it absorbed in `supersedes` so the merge stays traceable instead of reading as a silent deletion.
Tooling never infers a merge on its own.

### Repository configuration schema

Repo-specific scope lives in `.agents/config/review_config.toml` (Tier 3).
The engine reads only a structural subset; the remaining keys are agent-facing.
TOML orders bare keys before tables, so top-level scalars and arrays precede every `[table]` header.

Reference format 4: [review-schemas.md](../../../.agents/skills/aiscr-review-codebase/review-schemas.md).

The engine parses this with the standard library (`tomllib`), carries **no hand-maintained parser** for any structured format, and requires Python 3.11 or newer.

### Report schema

The produced `final_audit.md` (T11) uses this fixed **English** section ordering:

Section-order lookup: [review-schemas.md](../../../.agents/skills/aiscr-review-codebase/review-schemas.md).

Repo-specific findings fit **inside** these sections; do not introduce parallel report layouts.
**Body sections (1–11) must reflect the current consolidated state** — a reader of the body alone must get the complete picture.
The changelog records *what changed and when*; incremental updates append a dated changelog entry and update the affected body sections (never the changelog alone).

#### Coverage-gap resolution

When `coverage-gaps` or a U02 audit finds missed files/modules: create sequentially named sub-tasks (letter-suffix convention), each covering a cohesive group reviewable in one DONE-MEANS-DONE pass; read every in-scope file; write the sub-task report; then in a single atomic pass, in this order: update the analysis JSON (append), write `bugs.toml` and `refactoring_backlog.toml`, run `codebase_review.py render` to regenerate the Markdown twins, update the cache sub-task entry (`status`, `completed_at`, `scope`, `report_path`), and update `final_audit.md` body **and** changelog.
Rendering belongs inside the pass so the twins are never stale between phases.
Common pitfall: updating only the changelog while leaving body sections stale — update both.

### Shared English severity vocabulary with typed fields

Consume severity from the shared conduct; findings-store severity and backlog priority remain typed fields.
The priority vocabulary belongs to the findings schema.
Proven pre-existing observations use a separated section in the `bugs.toml` preamble, with evidence and provenance and no verdict-bearing severity; the generated twin preserves that section.
Do not create a second backlog copy of those observations.
The numeric thresholds that map a finding to a severity (fan-in/fan-out cutoffs, version-gap sizes, etc.) are Tier 3 values in the target repo's `review_config.toml`; this workflow names the rule, the repo supplies the value.

**GitHub Issue cross-reference is mandatory.**
Before filing a `bugs.toml` or `refactoring_backlog.toml` entry, check the target repo's GitHub Issues and mark the entry as *already tracked (Issue #N)*, *extends existing Issue #N*, or *new candidate*.
When a bug also appears in the refactoring backlog, reconcile severity vs priority; document any intentional divergence in the bug entry.
When a `Critical` bug is found, record it and surface it at the top of the session summary before starting the next task.

Each bug entry carries: file path and line, severity, GitHub-Issue status, description, recommended fix, and source task id.
Backlog items prefixed `[TXX]` must match the task that discovered them.

### Findings-to-issues transfer and reconciliation

Transfer is an explicit, attended sub-flow.
It never deletes, empties, renumbers, or title-matches a finding.
The workflow owns the orchestration boundary: `codebase_review.py` owns the findings schema, while `aiscr-plan-issue` and its issue engine own the GitHub body and write.
Neither engine imports the other.

1. Select the finding identifiers and obtain explicit approval for this transfer run.
   Group findings only where they have the same owner and remediation path.
2. For each selected identifier, run the read-only deduplication gate:

   ```bash
   python .agents/scripts/codebase_review.py issue-transfer --finding <FINDING_ID>
   ```

   The command reads the finding's existing `github_issue` determination. `action=create` is emitted only for `new issue candidate`; a recorded or pre-existing issue reference emits `action=reuse`.
   It never substitutes title similarity for that determination.
3. For `action=create`, pass the emitted finding and `sources` payload to the **Capture** entry of `aiscr-plan-issue`.
   Present the exact rendered body and digest there before its engine creates anything.
   For `action=reuse`, cite or update the recorded issue; do not open a second one.
4. After the create or reuse result is known, record the exact reference and current state locally:

   ```bash
   python .agents/scripts/codebase_review.py record-issue \
     --finding <FINDING_ID> --issue OWNER/REPO#NUMBER --state open
   ```

   Re-running with the same reference is idempotent.
   Reassignment to a different issue is refused rather than guessed.
   The command writes the typed fields and regenerates both Markdown twins from staged content in the same pass.
5. On later review runs, gather the current state of every **recorded** reference through the authenticated GitHub API into `<BULK_DIR>/issue-states.json`, where `<BULK_DIR>` is `.venv/.cache/aiscr-review-codebase/<run>/`; do not search by title.
   This machine output is bulk under `workflow/artefact-placement`.
   The shape is:

   Reference format 5: [review-schemas.md](../../../.agents/skills/aiscr-review-codebase/review-schemas.md).

   Then reconcile:

   ```bash
   python .agents/scripts/codebase_review.py reconcile-issues --states <BULK_DIR>/issue-states.json
   ```

   Open references become `tracked-open`; closed references become `tracked-closed`.
   An unresolved recorded reference is reported and left unchanged.
   Findings remain in their TOML source regardless of issue state, and both generated twins are refreshed in the same staged write pass whenever a status changes.

### Output language and quotation discipline

Review outputs are authored in **English by default** — task reports, `final_audit.md` body and changelog, `bugs.toml` and `refactoring_backlog.toml` prose fields (`title`, `description`, `recommended_fix`, `recommendation`, `preamble`), analysis JSON descriptions/notes, workflow-evolution feedback, severity values, and `final_audit.md` section headings.

**Quotation carve-out.**
Czech-native repository content — source comments, docstrings, GitHub issue titles, documentation passages, and AIS CR domain identifiers (Projekt, Akce, Lokalita, Dokument, PIAN, Hesláře, Knihovna3D, and similar) — is preserved **verbatim** in Czech, with only the workflow's analytical voice in English; a parenthetical English gloss MAY be added when load-bearing, and identifiers and domain nouns are treated as code.

**Pre-existing Czech artifacts** (authored before a repo adopted the English-default rule) are converged conditionally, not in a forced sweep:

- **Severity labels** are normalized to the English vocabulary in a single targeted pass when the workflow first runs against a repo that still carries Czech labels — a label-value pass, distinct from prose translation.
- **`final_audit.md` section headings** are translated to the English ordering on that same first run.
- **Prose** converges under a **translate-on-touch** policy: a session that modifies a file translates that whole file in the same session.
- **Directory READMEs** follow the hub README audience tiering: a directory read only by admins and agents carries a single English `README.md`; a directory non-admin humans read keeps a bilingual pair, where `README_en.md` is the agent-facing English twin and `README.md` the Czech human-facing twin, both carrying the `Language entry scope:` marker (`parity.readme-language-entry-scope-fence`).

User-facing Czech surfaces (repo `README.md`, issue tracker, incident postmortems) are unchanged by the English-default rule.

### Review complexity budget and splitting

Split a phase on whether the operator can honestly complete a **coherent review unit** under DONE MEANS DONE with useful report and cache granularity — **not** on raw line count: `max_lines_per_task` / `max_lines_per_file` are coarse guardrails and caution/diagnostic signals only.

Inputs to the split decision: file count, logical-unit boundaries, coupling/fan-out, risk class, statefulness, stack-family differences, artifact-update load, and prior cache coverage.
Each split must cite the coherent unit being separated (an app, module, configset, XSLT/template family, frontend feature group, high-risk boundary, or artifact-update batch).
A low-line-count change MAY still split or isolate when it touches coupled authentication, permission, async, persistence, deployment, or public-API behavior — cite the risk/coupling boundary in the rationale.

Sub-tasks use the **letter-suffix convention** (`T03a`, `T03b`, `T03c`, …); each produces its own per-task report and a `review_cache.json` sub-task entry with `scope`.
The per-sub-task scope and the numeric thresholds are Tier 3 in the repo config.
If a repo chooses to make the complexity budget machine-readable, it MAY add a `review_complexity` / split-trigger section to `review_config.toml`; this is repo-local and not a precondition for use.

#### Per-stack analysis-family extension

A repo adds stack-specific analysis families purely through its `review_config.toml` `phase_outputs` mapping — for example a search/index analysis output and a transform/stylesheet analysis output both mapping to the canonical **T03 — Data-layer analysis** phase.
No fork of the canonical source is required to add a stack-specific analysis family; the canonical phase id space stays stable across repos and stack detail lives in config (Tier 3).

#### Three-tier authority split

- **Tier 1 — Lifecycle (hub-canonical):** phase list and intent, report layout, cache and findings schemas and their versioning, artefact format classification, mode-dispatch contract, two-pass `final_audit.md` rule.
- **Tier 2 — Policy (hub-canonical):** shared-conduct reference, analysis heuristics, DONE MEANS DONE, GitHub-Issue cross-reference, review-complexity split rule, datetime discipline, bug-entry format, output-language and quotation discipline.
  Tier 2 names the *rule*; Tier 3 supplies the *value*.
- **Tier 3 — Scope (target repo `review_config.toml`):** app/module names, vendored exclusions, per-stack analysis families, severity thresholds, task-size guardrails, risk/coupling hints, key file lists, `phase_outputs`.
  Apply spec requirement *Sibling-local repo-specific scope* for the authority boundary.

### Execution approach

Log model usage at the start of the run per the `aiscr-model-logging` rule, before any write-capable step.

### Tiered analysis and direct-read coverage

Use the delivered [track catalogue](../../../.agents/skills/aiscr-review-codebase/review-tracks.md) for the shared dimensions, exclusions, cost tiers, and phase mapping.
T-family IDs remain lifecycle phases; the catalogue is the single mapping onto cross-cutting tracks, including the separate T12, T13, and live-acceptance evidence workflows.
Read optional `[review_facts]` in the target's existing `.agents/config/review_config.toml`: the target declares facts about itself — a database, a deployment pipeline, a public API surface, first-party frontend code — and lens applicability is derived from those facts by the mapping in the catalogue.
A target does not enumerate which lenses to run, because a lens omitted from a list is coverage lost while the run still reports complete.
Security applicability derives from the reviewed material and is not suppressible; any other suppression carries a recorded reason into the inactive-lens record.
Do not create or edit target configuration during a review.

Resolve the effort bound after the survey.
A codebase phase does not use the diff thresholds below: a phase inventory is a slice of a repository, so bounds derived for a change diff place substantially every phase in the widest band and cannot discriminate, and a signal that cannot discriminate is not a signal.
Select a phase's lenses from the character of its assigned material and the survey's signals, and bound effort by that phase's own declared scale where the target sets one.
Unreadable/binary material remains a gap, never zero-cost evidence.
The thresholds below bound effort on a diff only:

| Tier | Size signal | Track reviewers |
| --- | --- | --- |
| small | At most 50 lines AND 3 files | None; conductor reviews the material |
| standard | At most 400 lines AND 12 files, above small | Correctness and integration |
| full | Above either standard bound | All available analysis tracks |

Accept `--effort quick|standard|deep`: quick selects small, standard selects standard, and deep selects full in either direction from the size signal.
Without an override, the conductor may adjust exactly one tier downward for additive-only or test-only work, or upward for coupled boundaries, with a recorded reason; do not mistake additive authentication or migration code for low risk.
A small change touching authentication, secrets, cryptography, input validation, or access control always dispatches security, including under quick.
Security-sensitive standard material adds security; an enabled deployment track adds deploy-safety when rollout or migration behavior is in scope.
The security exception takes precedence over the codebase small-material zero-delegate default.

**Posture: registers `survey`, the seven analysis lenses, and `verify`.**
This workflow owns analysis outright, so its coverage is a property of the lenses it declares rather than of whichever engine a runtime happened to provide.
The survey establishes coverage once; the lenses the material's character selects receive that survey with narrowed material; the verifier adjudicates cited claims.
Acquisition, placement, deduplication and delivery stay with the conductor, which is why they are not delegated.

Before any lens is dispatched, establish coverage once: assign `aiscr-survey` the whole reviewed material under the `survey` contract, whose return set — the inventory, path/range/revision-or-digest receipts, and every named gap — it defines; that survey holds the run's coverage guarantee.
Where the material is small enough, the conductor performs the survey itself and records that it did.
Recall comes from this one complete read, never from issuing the whole material to each lens.

Select lenses from the character of the material — the behavior it affects and the boundaries it crosses — using the survey's signals as evidence; size bounds effort once relevance is established and never selects on its own.

Apply the admission owner `aiscr-quality-first-execution`.
Every selected lens receives the survey plus the narrowest material its lens requires, and reports only its own dimension; a lens is not handed the whole material again, because the survey already holds recall.
A lens observing a concern outside its own dimension records a referral rather than widening scope, and the conductor routes it.
Start exactly one delegate and wait for completion before starting the next; order analysis lenses as correctness, security, integration, performance, duplication, dead-code, deploy-safety, omitting unselected ones.
Bound cost by the material each assignment causes to be read, never by concurrent fan-out.
Retry only the interrupted assignment if a runtime limit is reached.
With no custom-agent surface, run each selected prompt as a separate sequential pass and record that execution mode; the procedure remains available without a native review engine.

Acquire exactly one route per invocation.
Where the delegate definition resolves - `aiscr-survey`, `aiscr-analyse-<lens>`, or `aiscr-verify` - dispatch it and read nothing further; that definition is self-contained.
Where it does not, compose the fallback in this session from three parts of the shared dispatch library: [common](../../../.agents/skills/_dispatch/common.md) for the assignment, coordination and conduct, the [contract](../../../.agents/skills/_dispatch/) part naming what the assignment returns (`contract-survey.md`, `contract-findings.md`, or `contract-verification.md`), and the [lens](../../../.agents/skills/_dispatch/) part for the dimension (`lens-<name>.md`).
Reading both routes delivers the contract twice.
Supply run/scope identifiers, resolved scope and revision, the survey, the narrowed material, applicable phase heuristics, and required receipts with the assignment.

After analysis, send candidates and prior-resolution claims to `aiscr-verify` with the `verification` contract — its definition, or [common](../../../.agents/skills/_dispatch/common.md) with [contract-verification](../../../.agents/skills/_dispatch/contract-verification.md) and [lens-verify](../../../.agents/skills/_dispatch/lens-verify.md) — exact cited lines, and minimal call-path or probe evidence.
Verification waits until the active analysis delegate completes.
The conductor checks placement, track membership, duplicate identities, receipts, and ledger coverage without repeating the analysis.
In the small tier with no candidates or prior claims, no verifier is dispatched.
A missing receipt or unresolved evidence request leaves work incomplete; obtain a bounded supplement.
Accept the declared `NO_FINDINGS` token only inside a complete structured return with receipts; missing, failed, or truncated output is not an empty result.

Record line/file counts, size tier, effort override, final tier, adjustment and security-exception reasons, active tracks, every inactive track with its reason (including target-disabled tracks), assignments, execution mode, maximum observed concurrent delegates, receipts/gaps, and verification outcomes in the local review, PR review body, or per-phase report.
A direct conductor review is recorded as such, with zero dispatched tracks and its coverage; it still performs all applicable phase checks.
Vendor bot reviews remain auxiliary evidence.

DONE MEANS DONE requires direct reads of every in-scope file by the assigned reader.
Reconcile path/range/revision receipts against the phase inventory; missing reads keep that unit pending or split.
T11 consumes completed phase evidence and runs integrity checks without repeating analysis.
Write the analysis JSONs, findings sources and rendered twins, cache, and final-audit body and changelog atomically so cache completion never precedes its evidence.

### Validation

- Run `codebase_review.py all` (when present in the target repo) and fix inconsistencies (orphan IDs, severity mismatches, missing report paths) before marking a task `done`; run it again before finalizing `final_audit.md` (T11).
- Confirm the cache conforms to `schema_version: "2"` and that no completed task was invalidated by a schema field-add.
- Confirm the findings sources conform to `schema_version: "1"` and that `codebase_review.py render --check` reports no stale Markdown twin.
- Confirm `final_audit.md` uses the canonical English section ordering and that body sections and changelog were updated together.
- Confirm severity values are Critical/High/Medium/Low and that bug/backlog entries carry a GitHub-Issue cross-reference.
- Confirm each recorded issue has a canonical tracking status, unresolved references were reported rather than guessed, and `render --check` passes after reconciliation.
- Update the rolling usage-log entry per the `aiscr-usage-logging` rule.

<!-- aiscr:gen:id=guardrails -->

## Iron Law

**IRON LAW:** `NEVER MARK A TASK DONE UNTIL EVERY FILE IN ITS SCOPE WAS DIRECTLY READ — NOT VIA SUMMARY, SEARCH, OR DIRECTORY LISTING.`

**IRON LAW:** `NEVER RUN THE CODEBASE-REVIEW WORKFLOW AGAINST THE MANAGEMENT HUB (AISCR-MANAGEMENT) AS THE TARGET.`

**IRON LAW:** `NEVER CREATE REVIEW SCAFFOLDING (REVIEW_CONFIG.TOML, REVIEW_CACHE.JSON, .AGENTS/ANALYSIS/, .AGENTS/REPORTS/REVIEW_REPORTS/) IN A REPO THAT HAS NONE WITHOUT EXPLICIT, SEPARATELY-APPROVED ENROLMENT. THE SKILL STUB BEING PRESENT IS NOT ENROLMENT.`

**IRON LAW:** `NEVER PROCEED PAST MODE PROPOSAL WITHOUT EXPLICIT USER CONFIRMATION.`

**IRON LAW:** `NEVER HARDCODE REPO-SPECIFIC SCOPE (APP NAMES, FILE LISTS, VENDORED LIBRARIES, THRESHOLD VALUES) INTO THE HUB-CANONICAL SOURCE — IT BELONGS IN THE TARGET REPO REVIEW_CONFIG.TOML.`

**IRON LAW:** `NEVER SELF-MODIFY HUB CODEBASE-REVIEW WORKFLOW SOURCES OR EMIT HUB BACKLOG ITEMS FROM A SIBLING REVIEW RUN WITHOUT EXPLICIT CURRENT-RUN HANDOFF APPROVAL.`

No exceptions.
These override any "the file is obviously fine", "the cache says done so I can skip it", "auto-detection is clearly right", or "this scope detail is small enough to inline" reasoning.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The detect phase picked `full` so I can just start writing" | Present the proposed mode with evidence; wait for explicit user confirmation. |
| "The operator asked for `update`, so I'll run `update`" | Run detect first; if no prior pass exists, refuse and recommend `codebase-review-mode-full`. |
| "I read the summary / a subagent's report, that's enough to mark done" | DONE MEANS DONE — read every in-scope file directly, or split. |
| "This app name / file list belongs in the canonical body" | Tier 3 — it goes in the target repo `review_config.toml`, not the hub source. |
| "Update mode found a big gap; I'll just do a full re-run now" | Document the gap; recommend a separate `full` invocation. Do not escalate in-session. |
| "I'll add the new findings to the changelog only" | Update `final_audit.md` body sections **and** the changelog. |
| "The source comment is Czech; I'll translate it in the quote" | Preserve Czech-native quoted content and domain identifiers verbatim; only the analytical voice is English. |
| "This 2,000-line file is over the line limit, split it" | Line count is a caution signal, not the trigger — justify splits by coherent unit and complexity. |
| "The skill stub is here, so I'll create `review_config.toml` and start a pass" | If the repo has no review setup it is not enrolled — explain that enrolment is deliberate and separately approved, and stop. |
| "I'll target aiscr-management to test the workflow" | Refuse. The hub carries no review lifecycle; point to `run_validation_all.py` / `validate_tool_parity.py`. |
| "U05 found a good workflow fix, so I'll patch the hub source now" | Record the evidence and prepare a handoff candidate; hub backlog emission requires explicit approval for this run. |
| "This finding has the same title as Issue #N, so I can reuse it" | Use the existing typed cross-reference determination. Title similarity is not the deduplication gate. |
| "The issue is closed, so I can remove the finding" | Set `tracking_status = "tracked-closed"`; the finding remains durable. |

<!-- aiscr:endgen -->

## Verification before completion

- [ ] Detect phase ran (cache, reports, file-change recency) before any mode proposal; target is not the hub; a repo with no review setup was reported not-enrolled and not scaffolded.
- [ ] Hub-cockpit runs only: the applicable target-resolution governance was followed without filesystem guesswork, the branch was stated for the target repository and confirmed before the first write, and every artifact landed in the target working tree.
- [ ] A mode was proposed **with evidence** and the user **explicitly confirmed** it before any write; an operator-typed mode was verified against evidence.
- [ ] Every file in each completed task's scope was directly read (DONE MEANS DONE); splits used the letter-suffix convention with per-sub-task reports and cache entries citing `scope`.
- [ ] Cache conforms to canonical `schema_version: "2"`; no completed task invalidated by a field-add.
- [ ] `final_audit.md` uses the canonical English section ordering; body sections **and** changelog updated together.
- [ ] Severity labels use Critical/High/Medium/Low; bug/backlog entries cross-referenced with GitHub Issues.
- [ ] Transferred findings retained their identifiers; recorded issue references carry `tracked-open` or `tracked-closed`; unresolved references were reported without guessing.
- [ ] Any issue creation used `aiscr-plan-issue`, with the exact body and digest approved before the GitHub write; reruns reused recorded references.
- [ ] Output language is English by default; Czech-native quotations and AIS CR domain identifiers preserved verbatim.
- [ ] `codebase_review.py all` (when present) passed; inconsistencies fixed.
- [ ] Rolling usage-log entry updated (agent/runtime, model, subagents, MCP servers, mode, target repo, impacted paths).

## Governance

- The workflow writes review outputs **in the target repository's working tree**; in the hub-cockpit tier it makes no hub-side write, and the target branch is stated and confirmed before the first write-capable step.
- The management hub's configuration-sync path distributes the **skill surface** (the vendor stub and this canonical workflow body) to repositories; it does **not** create review configuration, state, or reports.
  Review artifacts are produced only by **running this workflow**, and initial enrolment of a repo that has none is a deliberate, separately-approved step — never a side effect of receiving the stub.
- Repo-specific scope is authoritative in the target repo `review_config.toml` (Tier 3); the hub-canonical workflow body never hardcodes it.
  The target configuration and review state remain sibling-local operational sources.
  Agents must not self-modify them during a review session; workflow-evolution feedback is human-mediated through report-to-backlog handoff and hub note-idea workflow semantics after explicit current-run approval.

## Valid next steps

- When review findings warrant coordinated work, open a governed backlog change.
- Read `.agents/canonical_workflows_context.md` and follow the **Usage** section before loading a different workflow's context.

## Bundled scripts

The enrollment bundle installs these repository-local runtime scripts:

- `.agents/scripts/codebase_review.py`
- `.agents/scripts/lib/__init__.py`
- `.agents/scripts/lib/log_utils.py`
