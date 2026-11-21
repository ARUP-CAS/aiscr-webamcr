# .agents/

Configuration, review state, delivered governance tooling, and outputs for AI coding agents.
Rules and governance: see [AGENTS.md](../AGENTS.md).

## Structure

```text
.agents/
  analysis/                 — Machine-readable review task outputs (JSON summaries per task)
  canonical_configs/        — Delivered hub references and templates (read-only here)
    references/             — Governance topic index and documentation conventions
    templates/              — Delivered templates (incident postmortem, workstation safety)
  config/
    review_config.toml      — Review task definitions, tech stack, directories in scope
    review_cache.json       — Persistent state and progress of review sessions
  reports/
    review_reports/         — Per-task reports (<task_id>.md); final_audit.md carries the Changelog
    bugs.toml / bugs.md     — Confirmed bug findings (TOML source, rendered Markdown)
    refactoring_backlog.toml / refactoring_backlog.md — Structural improvement backlog
  scripts/                  — Delivered review and workflow tooling (codebase_review.py, github/, lib/)
                              plus repository-owned helpers; see scripts/README.md
  skills/                   — Shared workflow and OpenSpec skill tree, including the _dispatch library
  delivery-manifest.json    — Record of the last hub delivery (source commit, delivered assets)
  local_overrides.toml      — Alignment metadata for the hub governance baseline
```

## Canonical sources

- **Governance:** `AGENTS.md`
- **Configuration values:** `config/review_config.toml`
- **Review state:** `config/review_cache.json`
- **Operational review workflow:** the hub-canonical `aiscr-review-codebase` workflow (modes full / update), delivered as a skill in `.claude/skills/` and `skills/`; this repository carries no long-form review prompt.

Delivered surfaces (`canonical_configs/`, `skills/`, and the hub tooling under `scripts/`) are read-only here: propose changes at the `aiscr-management` hub.
See also [CONTRIBUTING.md](../CONTRIBUTING.md) § Správa dokumentace repozitáře.
