---
title: Testing scenario report template
intent: >
  Reusable living-file shape for testing-scenario reports: a durable
  body amended across runs, a current point-in-time verification that
  supersedes its predecessor, and a bounded verification log. This file defines
  the deliverable's structure only; the procedure that verifies and files
  reports is owned by the aiscr-review-live workflow.
audience:
  - maintainers of the deployed service
  - AI assistants running live acceptance verification
version: 1
---

<!-- SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- delivery-version: a9e7178f2056994b3ac481702b0ec38cdb13c576 2026-11-28T16:49:05+01:00 -->

## Scope

This is a **document template**, not a workflow.
It defines the required layout of one testing-scenario report — a single living file at `.agents/reports/testing_scenarios/<scenario-key>.md`, where the path never changes between verifications, so every past verification stays recoverable from the repository's history at that stable path.
The executable procedure is owned by the canonical workflow body `aiscr-review-live`; durable requirements are owned by the live-acceptance-verification capability.

The file separates two halves with opposite update semantics:

- **Durable knowledge** — the half that outlives any single run: environments, architecture and endpoint facts, the feature or entity model, discovery recipes, verification commands.
  A newer verification **amends** this half where the run found it incomplete or wrong; it is never re-derived from scratch or discarded because the verification is newer.
- **Current verification** — what was true at one verification: the behaviour matrix, the known defects, and the corrections made during that run.
  A newer verification **supersedes** this half, and the superseded run moves into the verification log as one entry.
  Superseded matrices do not accumulate in the file.

Reports are written in **English**, preserving domain entity names (record types, fields, identifiers, domain codes) verbatim in their native form.

## Scenario key and ownership

The `<scenario-key>` is the file's stable identity and the index's primary key:

- keyed on a **feature** by default — one feature under test across entities and surfaces;
- keyed on an **entity** only where that entity's own introduction or rework is the subject under test.
  An entity scenario cites the feature scenario for any mechanism it depends on and records only that entity's deviations from it, because a mechanism restated in two scenarios has two owners and drifts;
- never keyed on a surface — surfaces (pages, endpoints, APIs) are dimensions exercised within a scenario and recorded in the index.

## Defect identity scheme

Each recorded defect carries an identifier of the form `<scenario-key>-D<nn>`:

- minted at first recording, **never renumbered and never reused** — the digits record minting order, not position in a list, so the identity survives the report being reordered or rewritten;
- reused verbatim when a later verification walks the same defect to *still present*, *fixed*, or *changed*;
- never derived from a date or any other value that changes between verifications.

## Required section layout

The scenario file MUST follow this structure.
Subsections under the durable headings may be adapted to the subject; genuinely not-applicable top-level headings may be omitted, but the durable/current split and the log are kept.
Checks that require a role, credentials, or a browser the run did not have are recorded as **maintainer-assisted** with what they require — never inferred from an anonymous result.

```markdown
# <Feature or entity> — testing scenario

**Key:** <scenario-key> (feature | entity)
**Scope:** what this scenario covers — the feature or entity, the surfaces it
exercises, and the issues that drove it.
**Principle:** concrete record ids are deliberately not embedded — record
states drift. Use the discovery recipes below to find fresh candidates; a
verification command may carry an identifier placeholder the recipe fills.

## Durable knowledge

> Amend this half where a run found it incomplete or wrong; never re-derive it.

### Environments and endpoints
- environments (URLs, builds, quirks) and the surfaces and endpoints this
  scenario exercises, with what each is for.

### Architecture and implementation facts
- the non-obvious facts that were expensive to rediscover: how the surfaces
  fit together, where behaviour is decided, configuration that shapes it.

### Feature or entity model
- the model the feature implements or the entity's data model — rules,
  roles, states, and the deviations per entity where they differ.

### Discovery recipes
- the durable procedures that yield fresh test candidates. Numbered steps a
  reader can follow without the original records.

### Verification commands
- re-runnable commands, with identifier placeholders where a recipe must
  fill them. Rate limits and credential needs stated.

## Current verification (<date>, <instance or build verified>)

### Verified behaviour matrix
| Capability | Result |
| --- | --- |

### Known defects
- <scenario-key>-D<nn>: <description, with evidence and where it was verified>.

### Corrections made during this run
- claims corrected by later evidence in the same run, with the original
  conclusion visible.

## Verification log

| Date | Instance / build verified | What changed |
| --- | --- | --- |
```

## Content constraints

- The verification log holds exactly one entry per past run — its date, the instance or build verified, and what changed — and nothing else; superseded matrices and dated detail stay in the repository's history, not in the file.
- A defect the run did not examine is stated as *not examined* in the current verification; its absence from the matrix is never allowed to read as fixed.
- Do not include unredacted PII, credentials, or secrets; redact before recording.
- Update the corpus index and regenerate its view whenever this file changes; the index — not the filename — is what makes the scenario discoverable.
