---
name: aiscr-write-incident-postmortem
description: Use when the user asks to document an AIS CR service incident or postmortem.
  Produce a Czech report from the structured template under .agents/reports/incidents/.
license: CC-BY-4.0
author: AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69>
---

<!-- SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- aiscr:compiled=aiscr-write-incident-postmortem -->
<!-- delivery-version: b257a1a89279be5e17cda3c133aa77b8c4d2706c 2026-11-07T11:18:12+01:00 -->

<!-- aiscr:entry-scope -->

**Entry scope (compiled)**

- This `.claude/skills/` skill is self-contained; use the workflow body below.
- Load repository-local configuration and state named by the workflow before acting.
- Do not look for management-hub specs, plans, or canonical source files at runtime.

# /aiscr-write-incident-postmortem — incident and postmortem documentation

Document a production or staging incident using the AIS CR postmortem template.
Output is a structured Czech Markdown report.

## Phase awareness

This is an **operational execution skill**: its subject is an incident or postmortem report, not spec-governed repository state.
It runs without gating on OpenSpec context and never invokes `/openspec-propose`.
Execution boundaries: document the incident only; do not remediate the incident
or modify product code, and do not create new OpenSpec changes, promote backlog items, or escalate scope, except for the backlog-only handoff after explicit per-run approval (see **Report-to-backlog handoff** below).

## Report-to-backlog handoff

For **hub-owned** corrective actions that need scheduling beyond the postmortem report, follow the report-to-backlog handoff contract and the incident-documentation capability (*Incident corrective actions can hand off to backlog*).

1. After the incident report path is set, identify corrective actions that qualify for backlog follow-up.
2. Ask for **explicit per-run** approval to emit OpenSpec backlog items.
3. If approved, branch on run context:

   - **Sibling or other non-hub run**: draft the candidate slug, a one-line summary, `**Source report:**`, and `**Finding keys:**` without copying sensitive evidence; stop before any management-hub write.
     Emission is a separate explicit hub action by a maintainer; this workflow does not create hub changes or auto-invoke hub commands.
4. Record backlog slugs in the incident report, or document external tracking / why no hub backlog item was created.

Do not promote or implement spawned backlog inside this skill.

## Context to load first

1. `AGENTS.md` — governance and scope
2. `.agents/canonical_configs/templates/documents/incident_postmortem.md` — the report's required section layout

## Steps

1. Read `.agents/canonical_configs/templates/documents/incident_postmortem.md` — it defines the output structure.
2. Collect structured inputs from the user.
   All communication with the user **and the final report itself** are in **Czech**, preserving technical terms and identifiers (error codes, metric names) in their original form.
   Paste the intake block below and ask the user to fill it in as concise bullet points or short paragraphs:

   ```markdown
   ### Identifikátor a název incidentu
   - ID:
   - Krátký název:

   ### Služba a prostředí
   - Služba / repozitář:
   - Prostředí (produkce / staging / jiné):

   ### Časy a data (s časovým pásmem)
   - Začátek dopadu:
   - Čas detekce:
   - Čas mitigace:
   - Čas úplného vyřešení:
   - Použité časové pásmo:

   ### Dopad
   - Koho nebo čeho se incident týkal (uživatelé, systémy, data)?
   - Závažnost a délka trvání dopadu:
   - Projevy viditelné pro uživatele:
   - Dopad na SLO / SLA (pokud je znám):

   ### Časová osa (stručně, chronologicky)
   - YYYY-MM-DD HH:MM TZ – aktér – událost
   - YYYY-MM-DD HH:MM TZ – aktér – událost

   ### Technické detaily
   - Zasažené systémy / komponenty:
   - Klíčové logy nebo chybová hlášení:
   - Metriky / dashboardy / screenshoty (ideálně jako odkazy):

   ### Poznámky k příčině
   - Známá fakta o příčině:
   - Aktuální hypotézy nebo nejistoty:

   ### Mitigace a vyřešení
   - Okamžité kroky mitigace:
   - Finální oprava:
   - Kdy byl obnoven běžný provoz:

   ### Detekce a reakce
   - Jak byl incident detekován?
   - Co v reakci fungovalo dobře?
   - Co nefungovalo dobře?

   ### Následné akce
   - Položky k dořešení (s vlastníky a případně termíny):

   ### Odkazy a reference
   - Související issue:
   - Související PR:
   - Externí tikety / záznamy na status page:
   ```

   If the inputs are incomplete, ask targeted follow-up questions before finalising the report.
3. Generate the Czech Markdown report following the template's section layout exactly, using only the information the user provided plus any clearly marked assumptions.
   Apply these content rules:
   - **Prioritise factual accuracy** over speculation.
   - Separate **facts** from **hypotheses or unknowns**, using the template's `Známá fakta` and `Hypotézy / Neznámé` subsections.
   - Use a **neutral, non-blaming** tone focused on learning and prevention rather than assigning fault to individuals.
   - Do not invent technical details, timestamps, or impact descriptions absent from the user's inputs; where something is unknown, say so explicitly.
4. Present the draft to the user for review.
5. After approval, write the report to:

   ```text
   .agents/reports/incidents/INC-<date>-<short-name>.md
   ```

   Use today's date:

   ```powershell
   Get-Date -Format "yyyy-MM-dd"
   ```

### Execution using subagents

**Posture: declines.**
This workflow delegates nothing.
The inputs are an intake block the operator fills in.
There is no acquired repository material for a delegate to read.

The posture vocabulary, the default that governs a workflow declaring none, the declared return contracts, and the admission test are owned by `aiscr-quality-first-execution`.

<!-- aiscr:gen:id=guardrails -->

## Iron Law

**IRON LAW:** `NEVER WRITE OR COMMIT THE POSTMORTEM REPORT FILE WITHOUT FIRST PRESENTING THE FULL DRAFT TO THE USER FOR REVIEW AND RECEIVING EXPLICIT APPROVAL.`

No exceptions.
Draft presentation is always Step 4; file write is always Step 5 and only after approval.

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
- [ ] Czech Markdown format confirmed per the template's section layout.
- [ ] Report not pushed or shared externally without explicit user request.

<!-- aiscr:endgen -->

## Governance

- **Only the in-repo tier applies.**
  The subject is an incident, not a repository: the workflow takes no target argument and writes its report to the invoking checkout's `.agents/reports/incidents/`.
  Documenting an incident in another repository's service therefore means running this workflow in that repository, not designating it from the management hub.
  Tier semantics are defined under *Workflow execution tiers* in the `aiscr-ecosystem-governance` governance rule.
- Reports contain potentially sensitive information — do not include real PII, production URLs, or unredacted credentials.
- Do not write the file until the user approves the draft.
- Completed reports live in `.agents/reports/incidents/` only; do not push without user request.
- The report must be understandable to future readers who were not involved in the incident.
- Individual service repositories may extend the template layout with additional sections (for example SLO/SLA detail, compliance notes, or communication logs).
- **Spec is primary authority:** When the spec and this skill differ, follow the spec and surface the discrepancy.

## Valid next steps

- Hand the incident postmortem report to its owner; corrective work is outside this skill.
- `/aiscr-write-incident-postmortem` — re-run this workflow to document another incident.
- Read `.agents/canonical_workflows_context.md` and follow the **Usage** section before loading a different workflow's context.

## Bundled scripts

The enrollment bundle installs these repository-local runtime scripts:

- `.agents/canonical_configs/templates/documents/incident_postmortem.md`
