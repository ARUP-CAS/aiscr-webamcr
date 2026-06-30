# .agents/reports - Review and Workflow Reports

([Czech](README.md))

```text
Language entry scope: This README_en.md is the sole operational instruction source for agents. README.md is the Czech human-facing twin; update both together when operational behaviour changes.
```

This directory stores durable outputs from the long-running codebase-review lifecycle.

## Structure

- `review_reports/` contains per-phase reports and the consolidated `final_audit.md` summary.
- `bugs.md` records confirmed bug findings with severity, source location, issue linkage, recommendation, and originating review task.
- `refactoring_backlog.md` records structural and architectural improvement candidates grouped by priority.
- `verification_prompt_evolution.md` is retained as a historical webamcr-only verification note from the legacy prompt-evolution channel; do not extend it as the active feedback path.

## Agent Rules

- Use `aiscr-codebase-review` from the delivered assistant workflow surfaces as the operational review workflow source.
- Keep new review workflow prose English by default.
- Preserve verbatim Czech quotations, source comments, docstrings, documentation excerpts, GitHub issue titles, and AIS CR domain identifiers when exact wording matters.
- Use severity values `Critical`, `High`, `Medium`, and `Low` in newly touched review artifacts.
- Do not recreate long-form review prompt files under `.agents/prompts/`; the operational workflow is the delivered `aiscr-codebase-review` skill (modes full / update).