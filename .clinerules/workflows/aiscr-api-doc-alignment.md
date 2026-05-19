<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-api-doc-alignment.md -->

# aiscr-api-doc-alignment

Align API specs and documentation in API-focused repos. Use when the user asks to align OpenAPI specs with docs, or define API doc governance.

**Route**: Load [`.claude/skills/aiscr-api-doc-alignment/SKILL.md`](.claude/skills/aiscr-api-doc-alignment/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-api-doc-alignment/SKILL.md`](.cursor/skills/aiscr-api-doc-alignment/SKILL.md) when Cursor reader body is preferred.

`.agents/plans/api-doc-alignment.plan.md`
Load openspec/specs/api-specification-sync/spec.md first for the durable behavioral contract; load `.agents/canonical_configs/references/ecosystem_map.md` for API repo list; inventory OpenAPI specs and docs per plan Step 1; map sources of truth per Step 2; follow api-doc-alignment.plan.md for alignment workflow and governance documentation.
