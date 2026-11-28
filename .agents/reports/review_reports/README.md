# review_reports - Codebase Review Phase Reports

This directory stores per-phase reports created by the codebase-review lifecycle.

## Structure

- `T01.md` through `T10.md` are phase reports for the full review pass.
- Letter-suffixed files such as `T03b.md` are sub-task reports created when a phase was split by scope or complexity.
- `final_audit.md` is the T11 consolidated audit and contains the `## Changelog` section used by incremental updates. Incremental update runs (`aiscr-review-codebase`, mode update) append there rather than creating separate files.

| File | Task | Scope |
| ---- | ---- | ----- |
| T01.md | T01 | Repository structure mapping |
| T02.md | T02 | Dependency graph |
| T03.md | T03 | ORM analysis |
| T03b.md | T03b | ORM analysis (remaining models and views) |
| T04.md | T04 | Docker analysis |
| T05.md | T05 | Security audit |
| T06.md | T06 | Celery analysis |
| T07.md | T07 | Frontend analysis |
| T08.md | T08 | Documentation analysis |
| T09.md | T09 | CI/CD analysis |
| T10.md | T10 | Scripts analysis |
| final_audit.md | T11 | Final consolidated audit |

## Agent Rules

- Use `aiscr-review-codebase` from the delivered assistant workflow surfaces as the operational workflow source.
- Use `.agents/config/review_config.toml` for the canonical phase-to-file mapping.
- Keep newly touched headings and workflow prose English by default.
- Preserve verbatim Czech quotations and identifiers when exact source wording matters.
