# .agents/reports - Review and Workflow Reports

This directory stores durable outputs from the long-running codebase-review lifecycle.

## Structure

- `review_reports/` contains per-phase reports and the consolidated `final_audit.md` summary; see `review_reports/README.md` for the per-file breakdown.
- `bugs.md` records confirmed bug findings with severity, source location, issue linkage, recommendation, and originating review task.
- `refactoring_backlog.md` records structural and architectural improvement candidates grouped by priority (high / medium / low).

## Agent Rules

- Use `aiscr-review-codebase` from the delivered assistant workflow surfaces as the operational review workflow source.
- Record every new bug and refactoring candidate here, not only in GitHub Issues, so the review history stays complete.
- Reports under `review_reports/` are generated as tasks T01-T11 complete.
- Keep new review workflow prose English by default.
- Preserve verbatim Czech quotations, source comments, docstrings, documentation excerpts, GitHub issue titles, and AIS CR domain identifiers when exact wording matters.
- Use severity values `Critical`, `High`, `Medium`, and `Low` in newly touched review artifacts.
- Do not recreate long-form review prompt files under `.agents/prompts/`; the operational workflow is the delivered `aiscr-review-codebase` skill (modes full / update).
- Ecosystem automation recommendations (MCP, skills, hooks, subagents) live only in the `aiscr-management` hub - see `AGENTS.md`.
