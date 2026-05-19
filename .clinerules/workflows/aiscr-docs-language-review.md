<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-docs-language-review.md -->

# aiscr-docs-language-review

Run language and typo review of repo docs; user-facing Czech, agent-facing English, README_en equivalents, report language split, GFM formatting. Use when the user asks to review docs language, fix typos, add README English versions, or align with GitHub Markdown.

**Route**: Load [`.claude/skills/aiscr-docs-language-review/SKILL.md`](.claude/skills/aiscr-docs-language-review/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-docs-language-review/SKILL.md`](.cursor/skills/aiscr-docs-language-review/SKILL.md) when Cursor reader body is preferred.

`.agents/plans/docs-language-review.plan.md`
Load openspec/specs/docs-language-quality/spec.md first for the durable behavioral contract; run `python .agents/scripts/doc_discovery.py` to inventory docs; classify by audience (user-facing = Czech, agent-facing = English); define README English equivalent strategy; review language and typos per target language; add/update `README_en.md` files; align GitHub Flavored Markdown formatting; run `link_check.py`, `validate_plans.py`, PyMarkdown scan; follow docs-language-review.plan.md for execution workflow.
