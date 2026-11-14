# Agent execution and verification protocol

Read the runbook and selected manifest before presenting one human card. Run
`python tools/pack.py --help` in an exported pack. All commands prepare local files
or make explicitly selected GET requests. There is no import-submission command.

## Resolve the instance and each checkpoint

1. Fill `preflight-template.json` from verified deployment/operator facts. Request
   only missing non-secret values. Use `preflight` with the actual schema, references
   and initial scoped snapshot. Missing deployment identity, reference identities,
   ownership or source-volume paths block the dependent step. Future numeric keys
   are expected to remain blocked until their creation checkpoint.
2. Reference export fields contain real natural IDs plus sanitized `reference_rows`
   for independently resolving FK values. Compare the selected vocabulary families,
   map-sheet geometry and all used codes. Do not infer a DB key from its position.
3. `normalize-report` extracts separate normalized Import/Fedora sheets without
   overwriting XLSX. `bind` checks allocated numeric IDs against the correct DB table,
   synthetic natural key and file owner/name/path. Merge its new mappings into the
   retained bindings object only when existing values agree; a conflict stops binding.
   Rebuild into a **new** generated directory with these bindings and references.
   Render the next card from that directory. Do not re-upload already executed setup.
   Rendering registers an immutable `input-revisions/NNNN.json` and retains each ZIP
   below its checksum. Cards/indexes have revision-specific directories, so later
   binding and relocation preserve earlier inputs and instructions.
4. Capture each batch's before snapshot. Then run `snapshot --manifest ... --baseline
   DB_BEFORE --output AFTER_QUERY` to freeze existing numeric keys into the after query.
   This keeps deleted parents/children visible to orphan checks. Use exactly that
   after query even when roots have disappeared. Export JSON or a one-cell CSV.
5. Use `verify-batch` for all row values/FKs, companion models, omitted fields and
   normalized geometries. It reports unsupported/missing evidence as **blocked**.
   It cannot by itself establish history/Fedora/UX correctness. Supplement it with
   explicit `verify` checks for exact unaffected siblings and invariant constraints.

## Deployment parity and deferred batches

The test instance is deployed from release tags, so its commit is normally not the
inspected commit. Resolve the deployed tag to its full commit hash and run:

```powershell
.venv/Scripts/python.exe .agents/testing/imports-391-3527/tools/pack.py deployment-parity --manifest MANIFEST_JSON --deployed FULL_COMMIT --output PARITY_JSON
```

The command compares every pinned source file at that commit by line-ending-normalised
content. A PO catalog counts as equal when every entry the pack uses is unchanged.

- `source-equivalent`: start the run with `start-run --parity PARITY_JSON`.
- `different`: inspect each differing file. Either refresh the inventory against the
  deployed commit and rebuild, or write a reviewed-differences JSON that names, for each
  differing file, the exact `withheld_coverage` IDs (use `load.<workload>` for a
  workload), `reason` and `reviewer`. Rerun with `--reviewed REVIEW_JSON` to get
  `reviewed-difference`.
- Withheld coverage is reported `blocked`, and preflight, report and `load-analyse` all
  verify the same record.
- Without a computer that has the deployed commit, an exported
  `{"source_hash_mode", "deployed_commit", "hashes": {path: sha256}}` listing can be
  passed with `--listing`. Catalog entries are then not compared, so a catalog
  difference needs review.

Batches marked `deferred` in the manifest would trigger a known importer defect (see
`operator/known-source-risks.md` and `definitions/known-defects.json`). `render` gives
them no card and lists them in `deferred.json`. `checkpoint` refuses them, and `handoff`
never offers them as the next step. Their coverage is `blocked` with the fix as
prerequisite, and every report carries a `known_defects` section labelled
source-confirmed. Do not hand-edit a manifest to run a deferred batch. After a fix,
record `resolved_in` in the definition and rebuild.

## Complete the independent side-effect checks

For each `checks/<batch>.json`, resolve every declared ownership route from actual
before/after FK/link values. Use both former and new parents for reassignment. A
component's `komponenta_vazby` resolves through a documentation unit to its Fieldwork
event/Site, or through a document part to its Fieldwork event/document. Record these
exact identities in a separate expectation file before comparing actual changes.

Build the expected history multiset with the verified operator's numeric DB ID,
actual owner `historie` links, type and exact notes specified by the check contract.
Deduplicate a target shared by multiple CSV rows; do not deduplicate distinct files.
`import_pack.side_effects.history` compares the full multiset, preserved earlier history and
untouched control owners. Missing or extra history, wrong actors/notes or a missing
old parent fail even when totals match. Imported explicit history uses its synthetic
actor and supplied note rather than the session actor.

`links --snapshot ...` emits convenient credential-free Fedora links from real stored
paths, including paths without a leading slash. `soub-123` is an import/DB key, not
the file UUID. Use scoped paginated `fedora-search` for discovery, then `fedora-read`
for authoritative status/content/metadata/version evidence. A stale search index is
not proof of missing persistence. Retry only safe reads within a recorded bounded
index-lag interval; preserve the first response as well as the later one.

Compare semantic XML ownership/values and exact unchanged controls, with namespace-
aware parsing. Keep resource/version changes distinct from XML content changes.
`resource_check` and `side_effects.repository` check status, SHA-256/SHA-512, expected
MIME/name and exact newly added version IDs. Resolve version IDs from retained
version-list XML/JSON; do not substitute an aggregate index count. For originals,
also check stored size/page metadata and unchanged path on replacement. For synthetic
GPS JPEGs, inspect retained original EXIF (GPS present) and stored bytes (GPS absent),
then calculate the expected stored SHA-512 independently. A transformed JPEG need not
have the source hash. For paradata-only operations assert unchanged DB/history and
domain XML with `unchanged_resources`, while checking paradata bytes/status directly.

## Negative and controlled cases

`N07-field-boundaries` combines row errors that the inspected validator enumerates.
Match each CSV/row/field to its intended diagnostic; `import_pack.negatives.error_checks`
requires an explicit diagnostic pattern. Errors without a reported ID are matched
using the retained row-order/CSV position, never guessed by counts. If an earlier
batch/ordering/parser error prevents observation, use `split-negatives` to generate
one-row inputs and run only concealed probes. Some model constraints surface in the
data phase: after a clean validation, run an isolated probe to its expected terminal
failure and prove rollback. Do not start a large mixed negative batch whose actual
failure boundary has not been established.

The `T*` lifecycle cards perform update, deletion and reinsertion on the same key;
initial setup is a fourth required checkpoint. Require direct deleted/tombstone
status and recreated bytes/versions. The ledger cannot pass the lifecycle from just
one successful update. Inspect `scenarios.json` for every phase-specific stop/fault.
Record approved trigger/restoration method and exact isolated targets first. No
privileged injection, maintenance change or source-file move is performed by a tool
in this pack. Cycles/self-links/negative counts and MIME/extension acceptance remain
explicit policy questions; unexplained current behaviour is not a pass.

## Retain, report and recover

`checkpoint` accepts a JSON object mapping evidence kinds to original local paths;
select its actual `--phase` explicitly. A checked validation checkpoint does not
mean the import ran: the next action is approval/start of the same task, never a new
upload. Only a checked terminal checkpoint completes that batch's execution.

It copies immutable originals to `<batch>/originals/<kind>/<sha256><suffix>` and
appends an event with the selected manifest and input hashes. Repeat collection of
identical bytes reuses the same original; different stages/tasks retain separate
originals. Existing legacy checkpoint references remain readable. Required kinds are
listed per coverage item. Put actual human feedback in `human-ux` JSON with author,
observation time, task ID, observed facts and unobserved facts. An agent may transcribe
the human's feedback with its provenance. Supplied screenshots establish only what
is visible; they do not establish unrecorded timing, interactions or responsiveness.

Assessments passed to `report` name run ID, deployment, batch/task, retained evidence
objects and all machine assertion states. The report checks hashes/checkpoints and
mandatory evidence. Missing UX, stale identity, incomplete lifecycles or simulated
results cannot yield completeness. A fresh agent runs `handoff`, reads the last
checkpoint and **never repeats a mutation merely because the chat was lost**.

`recovery` accepts reconciled row states. For partial work use separate DB/history/
metadata/binary states. Unknown state blocks recovery. DB-committed rows require a
phase-specific repair; they must not become new INSERTs. Retain actionable Fedora
plans from XLSX and propose an exact approved repair when needed. `cleanup` produces
an exact actual-ID/path candidate plan with `execute: false`; review child/cascade/
restrict effects and obtain separate cleanup authorization. Keep all evidence after
cleanup and until an explicit retention decision.

## Bounded complete Fedora collection

Build a frozen JSON plan with a `resources` array of explicit `url` objects. Use
`capture --plan PLAN --directory RUN/BATCH/fedora-before --run-root RUN --limit 100`
and a separate `fedora-after` directory. Raise the explicit GET budget within the
authorized verification window when collecting a full load dataset. One session-only
password prompt covers a call; it is never saved. Collection resumes unchanged prior
responses, detects altered bytes and reports remaining resources. Preserve every
returned `index-*.json`. Resource body paths are relative to the run root, so the
whole retained folder can move to another opened workspace.

Use `verify-effects` with the independently authored history/resource expectation file,
both DB snapshots and both direct-response indexes. Put version-delta assertions on
the `/fcr:versions` resource itself; its memento IDs are parsed from retained content.
Use namespace-aware `xml_assertions` with exact owner paths/counts, not just text found
somewhere in XML. The reducer also supports explicit unchanged DB/resources checks.

## Isolating concealed errors

`split-negatives` prepares per-field probes; `split-branches` prepares per-branch
negative probes. Each preserves its parent pack and adds only row subsets from already
planned negative batches. Register/render that revision in the same run. Source,
operation, coverage and original-row checks reject scope expansion. New probe cards
are placed immediately after their parent, before fixture deletion. Execute only
checks concealed by an earlier error; retain all original results and never repeat
an already executed mutation. This fallback is separate from partial-commit recovery.


## Bind the load verdict to its retained session

`load-analyse` requires `--directory RUN_DIRECTORY` in addition to `--manifest`,
`--evidence` and `--output`. Select the final bound manifest registered in that run,
not an earlier template. Supply the exact run ID, suite, workload, namespace,
deployment, measured batch/task IDs, manifest SHA-256 (`json_bytes` representation),
input SHA-256 and timezone-aware acquisition time in the load evidence object.
The deployment must match the prepared source revision. Missing values block a
verified verdict; they are not inferred from ordinal assertion IDs.

Retain `input`, `report`, `db-before`, `db-after`, `fedora-before`, `fedora-after`,
`human-ux` and `load-results` in the measured task's checked terminal checkpoint.
`load-results.json` contains exactly the supplied load fields that are present:
`counts`, `assertions`, `group_transactions`, `phases`, `metrics` and
`human_responsiveness`. These are normalized analysis results; keep all underlying
original DB exports, completed direct-response indexes/bodies, XLSX and actual
human observations as well. Keep the returned reference objects as the evidence
object's `evidence` mapping; do not substitute source/download filenames.

Use `LOAD_RESULT_FIELDS` from `import_pack.reporting` and `json_bytes` from
`import_pack.common` when writing normalized results and calculating the manifest
hash. Complete mechanical comparisons first, retain these results and all required
originals through `checkpoint --phase terminal --state checked`, then call
`load-analyse` with that manifest and run directory. The reducer checks the latest
measured batch event, task identity, mode, selected input revision, retained hashes,
run-current acquisition times and direct-response body hashes. Changing/rebinding
inputs after that event requires fresh reconciliation/checkpoint evidence.
An older run, altered original or simulation cannot produce a verified load.
