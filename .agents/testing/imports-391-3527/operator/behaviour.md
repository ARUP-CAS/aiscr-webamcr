# Behaviour session

Read `START-HERE.md` first. This suite covers all 46 CSV classes, permitted/prohibited
operations, niche ownership and relationship paths, constraints, failure/recovery and
UX. Its result does not include load testing.

The vocabulary is pinned in `terminology.json`. Use Fieldwork events (Akce), Sites
(Lokality), Spatial unit (PIAN), Archaeological documentation point (ADB), Elevation
points (Výškové body), Unidentified fieldwork (Neidentifikovaná akce), Individual find
(Samostatný nález) and Announcer (Oznamovatel). Technical CSV names remain unchanged.

## Agent procedure

1. Complete preflight and select a fresh namespace. Inspect the coverage ledger and
   manifest before asking for uploads. Resolve references and later generated keys;
   `.template.zip` inputs are blocked. No source record selected for structure is
   authorized for mutation merely because its metadata is accessible.
2. Review batch dependencies. Baseline batches create foundations, connected records,
   files, distributions/paradata and explicit history, then full/partial updates.
   Explicit child DELETEs are partitioned into dependency layers to avoid cascades
   masking unvisited child operations. Parent-cascade scenarios use isolated contexts.
3. Complex branches use separate synthetic contexts and compatible operation batches.
   Parser/whole-batch failures are kept separate. A specific expected error must be
   observed for every negative row; an unrelated earlier error cannot satisfy it.
4. Controlled-state cases need the specified absent/present companion, cadastral
   spatial-unit state, disposable operator or history/backfill baseline. Obtain
   target-specific setup authorization. Acceptance ambiguities such as cycles remain
   explicit; do not silently define application policy or call an unexplained rejection
   a pass. Keep these rows in coverage and produce a clear blocked/failed result.
5. Render and present one human instruction card/checkpoint at a time. Prepare all
   safe data/SQL/API work yourself. The human uploads/selects/confirms/observes/downloads.
   Do not operate the browser or replace the import step with an HTTP request.
6. Read each report and supplied screenshot. Run the read-only comparisons where
   authorized; otherwise consume the exact operator export. Preserve earlier evidence
   on a failure, reconcile partial commit state and stop dependent steps.
7. Report class/operation/branch, DB, history, Fedora and human UX outcomes separately.
   Every mandatory check needs actual current evidence for a complete result.

## Deferred by a known importer defect

Four batches are deferred until the `VazbaLookupImportField` fix is deployed:
`N07x-deferred-known-defects`, `V17-branches-update`, `V18-branches-update` and
`V19-branches-update`. They hold the three owner `missing-lookup` probes and the
user, cooperation and file history owners. They get no card, and their coverage is
`blocked`. N07 runs without them. See `operator/known-source-risks.md`. The defect is
reported as source-confirmed, separately from live outcomes.

## Cases that must remain visible

- All 138 baseline operation cells: 125 permitted operations and 13 prohibited UPDATEs.
- Both Fieldwork event types, Sites, optional/missing multi-model data, both component
  owners and document-part linkage alternatives; old/new parent metadata after moves.
- Both coordinate systems, supported geometries, elevation, empty/omitted/cleared
  fields, cadastral spatial-unit reuse/creation and derived-object rollback.
- Vocabulary families/hierarchies, uniqueness, forward references, composite/prefixed
  keys, all three RUIAN levels, cooperation peers, permission/notification changes.
- History owners including user, file and cooperation formats defined by the attached
  `historie.sql`. The confirmed resolver defect keeps user/cooperation/file owners
  in coverage as `blocked` and deferred, never as removed or passed.
- All file owners, replacement/path/size/hash/page metadata, GPS removal, thumbnails,
  distributions/paradata, exact MIME/name, protected paths, tombstones and download rights.
- Validation purity, maintenance/ownership, two administrators, phase-specific stop,
  reload/polling failure, report agreement and evidence-based recovery.

Use `operator/evidence.md` for the exact retrieval and retention procedure. Do not
discard the evidence after the final batch or after synthetic-data cleanup.
