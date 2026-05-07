<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-note-idea.md -->

# aiscr-note-idea

Capture an idea as an OpenSpec backlog change using the lightweight backlog schema, then stop before promotion.

**Route**: Load [`.claude/skills/aiscr-note-idea/SKILL.md`](.claude/skills/aiscr-note-idea/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-note-idea/SKILL.md`](.cursor/skills/aiscr-note-idea/SKILL.md) when Cursor reader body is preferred.

_No backing plan file;_ follow fallback and governance.
Create `openspec/changes/<slug>/` with schema `backlog`, fill `proposal.md` from the backlog template, refresh `.agents/backlog-overview.md`, and stop before planning or promotion.
