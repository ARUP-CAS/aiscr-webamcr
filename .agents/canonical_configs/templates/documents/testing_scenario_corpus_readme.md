<!-- SPDX-FileCopyrightText: 2026 AIS CR (Archaeological Information System of the Czech Republic) <https://ror.org/01a7rqj69> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- delivery-version: a9e7178f2056994b3ac481702b0ec38cdb13c576 2026-11-28T16:49:05+01:00 -->

# testing_scenarios — verified live-testing scenario corpus

This directory holds this repository's **testing scenario corpus**: living files of verified knowledge about how to test this repository's deployed service directly, produced by issue-driven live acceptance runs (the `aiscr-review-live` workflow).

## What a scenario file carries

Each scenario is **one living file** named `<scenario-key>.md`, at a path that never changes between verifications, so every past verification stays recoverable from the repository's history.
The file separates two halves with opposite update semantics:

- **Durable knowledge** — environments and endpoints, architecture and implementation facts, the feature or entity model, discovery recipes, verification commands.
  A newer verification **amends** this half; it is never re-derived from scratch.
- **Current verification** — the behaviour matrix, known defects (each under a stable `<scenario-key>-D<nn>` identity that survives reordering), and corrections made during the run.
  A newer verification **supersedes** this half, and the superseded run moves into the file's verification log as one entry.

Concrete record ids are deliberately **not** embedded — record states drift.
The discovery recipes are the means of reproducing a check; re-verify before relying on any id an earlier verification noted.

## The index and its view

`index.toml` is the corpus's source of truth: per scenario, its key, ownership kind (feature by default, entity by exception), covered features and entities, exercised surfaces, driving issues, and last verification date.
`INDEX.md` is **generated** from it — never hand-edit the view; change the index and regenerate:

```bash
python .agents/scripts/testing_scenario_corpus.py render
python .agents/scripts/testing_scenario_corpus.py check
```

`check` reports a stale view, an index entry whose file is missing, and a scenario file present with no index entry — an unindexed scenario is undiscoverable, so the omission is an error rather than a warning.
Resolve scenarios from the index's declared coverage, never from filenames.

## Conventions

- Reports are written in **English**; domain entity names (record types, fields, identifiers) stay verbatim in their native form.
- Checks that need a role, credentials, or a browser the run did not have are recorded as **maintainer-assisted** with what they require.
- A defect a run did not examine is stated as *not examined*; its absence from a matrix is never allowed to read as fixed.
- No placeholder file is ever added to hold this directory open; the corpus exists because a report was filed.
