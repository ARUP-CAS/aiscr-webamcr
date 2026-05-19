<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-plan-from-idea.md -->

# aiscr-plan-from-idea

Promote one OpenSpec backlog proposal into the governance-driven planning flow by running a governed structured exploration pass before the formal planning phase, then produce OpenSpec artifacts (proposal, specs, design, tasks), refresh backlog overview, and hard-stop before implementation unless the user explicitly starts a separate apply/implementation workflow afterward.

**Route**: Load [`.claude/skills/aiscr-plan-from-idea/SKILL.md`](.claude/skills/aiscr-plan-from-idea/SKILL.md) for the full workflow body, guardrails, and steps, then follow the instructions there.

**Full reader**: [`.cursor/skills/aiscr-plan-from-idea/SKILL.md`](.cursor/skills/aiscr-plan-from-idea/SKILL.md) when Cursor reader body is preferred.

_No backing plan file;_ follow fallback and governance.
Read `openspec/changes/<slug>/proposal.md` from the named backlog proposal first; run one governed structured exploration pass; run one formal planning phase using that exploration output; wait for approval; promote the same slug into a governance-driven OpenSpec change; refresh `.agents/backlog-overview.md`; stop before implementation and offer `/opsx:continue <slug>` or `/opsx:apply <slug>` based on readiness.
