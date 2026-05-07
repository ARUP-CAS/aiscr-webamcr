---
name: aiscr-incident-postmortem
description: Document an incident or postmortem for an AIS CR service using the structured
  template. Produces a Czech Markdown report under .agents/reports/incidents/.
disable-model-invocation: true
---

<!-- aiscr:canonical=.agents/canonical_configs/workflow_skills/aiscr-incident-postmortem.md -->

# aiscr-incident-postmortem

<!-- aiscr:stop-anchor -->
**Entry scope**

- Stay in this `.cursor/skills/` surface and its same-vendor pointers first.
- Do not open parallel vendor trees by default just in case.
- Cross into another vendor tree only for explicit parity checks, generator work, or governance maintenance.

Document a production or staging incident using the AIS CR postmortem template. Output is a structured Czech Markdown report.

**Requirement authority:** [`openspec/specs/incident-documentation/spec.md`](/openspec/specs/incident-documentation/spec.md) — durable behavioral requirements for incident documentation.

## Phase awareness

This skill operates within the **implement** phase of the OpenSpec lifecycle.
It is typically invoked as part of `/opsx:apply` or a standalone approved task.
Before executing, check for an active OpenSpec change or domain spec under
`openspec/`.
If one exists, load its context files as the primary authority.
If none exists for this domain, run `/opsx:propose`, stop for human approval,
and only continue after that change becomes the active context of the run.
It must not create new OpenSpec changes directly, promote backlog items, or
escalate scope beyond the approved task boundary.

## Context to load first

1. `AGENTS.md` — governance and scope
2. [`openspec/specs/incident-documentation/spec.md`](/openspec/specs/incident-documentation/spec.md) — **primary authority** for incident documentation requirements
3. `.agents/prompts/postmortem_template.md` — template structure and required inputs

## Steps

1. Read `.agents/prompts/postmortem_template.md` — it defines required inputs and output structure.

2. Ask the user for the required inputs (as listed in the template):
   - Incident ID or title
   - Affected service(s) and repo(s)
   - Timeline (detection, mitigation, resolution)
   - Root cause
   - Impact (users, duration)
   - Corrective actions and owners

3. Generate the Czech Markdown report following the template structure exactly.

4. Present the draft to the user for review.

5. After approval, write the report to:

   ```text
   .agents/reports/incidents/INC-<date>-<short-name>.md
   ```

   Use today's date:

   ```bash
   python -c "import datetime; print(datetime.date.today().isoformat())"
   ```

## Iron Law

**IRON LAW:** `NEVER WRITE OR COMMIT THE POSTMORTEM REPORT FILE WITHOUT FIRST PRESENTING THE FULL DRAFT TO THE USER FOR REVIEW AND RECEIVING EXPLICIT APPROVAL.`

No exceptions. Draft presentation is always Step 4; file write is always Step 5 and only after approval.

## Red flags — STOP

| Thought | What to do instead |
| ------- | ------------------ |
| "The incident facts are clear — I'll write the file directly to save time" | Present the draft first; write to file only after the user has reviewed and approved it. |
| "The report contains no PII — I can include the full log output" | Redact all user data, internal hostnames, and credentials before including any log content; when in doubt, exclude. |
| "The report is complete enough — I'll commit it now" | Explicit user approval is required before any file write; committed reports also require an explicit push request. |

## Verification before completion

Before claiming this workflow complete:

- [ ] Draft presented to user before any file was written.
- [ ] No real PII, production URLs, or credentials in the report content.
- [ ] Report written to `.agents/reports/incidents/INC-<date>-<short-name>.md` with correct naming.
- [ ] Czech Markdown format confirmed per template.
- [ ] Report not pushed or shared externally without explicit user request.

## Plan and workflow

_No backing plan file;_ follow fallback and governance.

**Registry fallback:** Load openspec/specs/incident-documentation/spec.md first for the durable behavioral contract; skill is spec-first.

## Governance

- Reports contain potentially sensitive information — do not include real PII, production URLs, or unredacted credentials.
- Do not write the file until the user approves the draft.
- Completed reports live in `.agents/reports/incidents/` only; do not push without user request.
- **Spec is primary authority:** When the spec and this skill differ, follow the spec and surface the discrepancy.

## Valid next steps

- `/opsx:apply <slug>` -- continue implementing remaining tasks in the current change
- `/opsx:verify <slug>` -- verify implementation matches change artifacts
- `/opsx:archive <slug>` -- archive the change after implementation is complete
- `/aiscr-canonical-workflows-context` -- load context for a different workflow