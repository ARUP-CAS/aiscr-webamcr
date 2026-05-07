<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-release-notes.md -->

# aiscr-release-notes

Generate semantic, issue/PR-aligned release notes for a target AIS CR repository. Stores output in .agents/reports/release-notes/. Optionally updates the GitHub release body (opt-in, requires user approval).

**Route**: Load [`.claude/skills/aiscr-release-notes/SKILL.md`](.claude/skills/aiscr-release-notes/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-release-notes/SKILL.md`](.cursor/skills/aiscr-release-notes/SKILL.md) when Cursor reader body is preferred.

`.agents/plans/release-notes.plan.md`
Load openspec/specs/release-documentation/spec.md first for the durable behavioral contract; gather target repo, mode (single release vs supplement missing vs date-range), and output scope; discover releases and `.github/release.yml` config; collect PRs, commits, and linked issues per release; group by semantic categories; write to `.agents/reports/release-notes/`; optionally push to GitHub release body with user approval and propagation scope (single/range/all).
