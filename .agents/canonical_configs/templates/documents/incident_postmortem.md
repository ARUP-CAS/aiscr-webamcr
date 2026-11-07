---
title: Incident and postmortem report template
intent: >
  Reusable document shape for AIS CR incident and postmortem reports. This file
  defines the deliverable's structure only; the procedure that collects inputs
  and generates the report is owned by the aiscr-write-incident-postmortem workflow.
audience:
  - maintainers of AIS CR services
  - AI assistants drafting reports based on human-provided inputs
version: 1
---

<!-- SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- delivery-version: 083eb1bc1a0c628b2d6d48b806b6568be3f67ac2 2026-11-07T12:31:37+01:00 -->

## Scope

This is a **document template**, not a workflow.
It defines the required section layout of an AIS CR incident/postmortem report.
The executable procedure — collecting structured inputs, generating the draft, presenting it for approval, and writing it to `.agents/reports/incidents/` — lives in the canonical workflow body `aiscr-write-incident-postmortem`.
Durable requirements live in `openspec/specs/documentation/incident-documentation/spec.md`.

Reports are written in **Czech**, preserving technical terms and identifiers (error codes, metric names) in their original form.
Individual repositories may extend the layout with additional sections (for example SLO/SLA detail, compliance notes, or communication logs).

## Required section layout

The report MUST follow this structure.
Subsections that are genuinely not applicable may be omitted, but the top-level headings are kept.
Where an input was not provided, omit the specific bullet or mark it explicitly as **unknown**.

```markdown
# Incident <ID>: <Krátký název>

## Shrnutí
- 2–4 odrážky: co se stalo, jaký byl dopad a jak byl incident vyřešen.

## Kontext
- Služba / repozitář.
- Prostředí.
- Další důležité pozadí (pokud je potřeba).

## Dopad
- Koho nebo čeho se incident týkal.
- Závažnost a délka trvání.
- Projevy viditelné pro uživatele.
- Dopad na SLO / SLA (pokud je relevantní).

## Časová osa
- Chronologický seznam událostí ve formátu:
  - YYYY-MM-DD HH:MM TZ – aktér – popis události

## Kořenová příčina

### Známá fakta
- Faktická tvrzení o příčině incidentu, podložená evidencí.

### Hypotézy / Neznámé
- Hypotézy, otevřené otázky nebo nejistoty, které je ještě třeba ověřit.

## Mitigace a vyřešení
- Okamžité kroky mitigace.
- Finální oprava nebo změny nasazené do produkce.
- Kdy byl obnoven běžný provoz.

## Detekce a reakce
- Jak byl incident detekován (monitoring, hlášení uživatelů apod.).
- Co v reakci fungovalo dobře.
- Co nefungovalo dobře nebo způsobilo zpoždění.

## Následné akce
- Kontrolní seznam kroků s vlastníky a případně termíny, například:
  - [ ] <akce> — Vlastník: <jméno>, Termín: <YYYY-MM-DD>

## Odkazy a reference
- Související issue.
- Související PR.
- Dashboardy, runbooky nebo externí tikety.
```

## Content constraints

- The report must be understandable to future readers who were not involved in the incident.
- Do not include unredacted PII or secrets.
  Prefer summaries or redacted descriptions over verbatim sensitive data or full log dumps.
