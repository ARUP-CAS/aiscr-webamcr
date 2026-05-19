---
description: Legacy commands directory (README only); workflows live in .claude/skills
---

# Claude Code — commands folder

([Czech](README.md))

```text
Language entry scope: This README_en.md is the sole operational instruction source for agents. README.md is the Czech human-facing twin; update both together when operational behaviour changes.
```

This directory is kept in AIS CR only as a historical pointer. Standard workflow entry points live under `.claude/skills/aiscr-*/SKILL.md`.

## Use

- Use `.claude/skills/` for active workflows.
- Use `.agents/canonical_configs/references/canonical_workflows_context.md` for the registry and parity map.
- Run `generate_workflow_skills.py` after changing a canonical workflow document.

## Note

- Do not reintroduce per-workflow `.md` files here; the README is intentionally the only file.

[Czech version](README.md)
