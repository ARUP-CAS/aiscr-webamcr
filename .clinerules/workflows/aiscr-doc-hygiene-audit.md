<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-doc-hygiene-audit.md -->

# aiscr-doc-hygiene-audit

Run a documentation hygiene audit on this repository (or a target repo). Identifies duplication, drift, token inefficiency, and broken links. Use the aiscr-doc-auditor subagent for the analysis phase.

**Route**: Load [`.claude/skills/aiscr-doc-hygiene-audit/SKILL.md`](.claude/skills/aiscr-doc-hygiene-audit/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-doc-hygiene-audit/SKILL.md`](.cursor/skills/aiscr-doc-hygiene-audit/SKILL.md) when Cursor reader body is preferred.

`.agents/plans/doc-hygiene-audit.plan.md`
Load openspec/specs/documentation-consistency/spec.md first for the durable behavioral contract; then run `python .agents/scripts/doc_discovery.py --output json` and `python .agents/scripts/link_check.py` for deterministic inventory; follow doc-hygiene-audit.plan.md for report-only or report+safe-fixes mode execution.
