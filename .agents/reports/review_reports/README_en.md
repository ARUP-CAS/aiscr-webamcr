# review_reports - Codebase Review Phase Reports

([Czech](README.md))

```text
Language entry scope: This README_en.md is the sole operational instruction source for agents. README.md is the Czech human-facing twin; update both together when operational behaviour changes.
```

This directory stores per-phase reports created by the codebase-review lifecycle.

## Structure

- `T01.md` through `T10.md` are phase reports for the full review pass.
- Letter-suffixed files such as `T03b.md` are sub-task reports created when a phase was split by scope or complexity.
- `final_audit.md` is the T11 consolidated audit and contains the `## Changelog` section used by incremental updates.

## Agent Rules

- Use `aiscr-codebase-review` from the delivered assistant workflow surfaces as the operational workflow source.
- Use `.agents/config/review_config.yaml` for the canonical phase-to-file mapping.
- Keep newly touched headings and workflow prose English by default.
- Preserve verbatim Czech quotations and identifiers when exact source wording matters.