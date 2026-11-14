# Evidence retrieval, retention and handoff

The agent handles reading, checksums, comparisons and report extraction. The human
handles browser actions and captures live observations. The agent can inspect supplied
screenshots; it must not claim to have observed unrecorded interactions or responsiveness.

## Before the human starts a batch

The agent states the exact full input path, operation, prerequisites and evidence root.
It captures the DB/Fedora baseline. Resolve the selected run folder to an absolute path
in an opened agent workspace; every generated card then names its full destinations.

Keep `input-manifest.json`/the selected manifest and the original ZIP. A filename alone
does not establish which bytes were uploaded: retain the SHA-256 as well.

## Validation and final reports

1. On the current import page, click **Stáhnout log importu** at the validation
   checkpoint. Move/copy the downloaded XLSX into the card's exact batch evidence
   directory as `validation-report.xlsx`. Keep the original bytes.
2. After the expected terminal outcome, use **Stáhnout log importu** again and save
   the separate download as `final-report.xlsx`. Do not replace the validation report.
   The agent retains each stage under its canonical `report` evidence kind at
   `<batch>/originals/report/<sha256>.xlsx`. Each checkpoint keeps its own reference;
   different snapshots and later task attempts also retain distinct hashed originals.
3. If the task page was lost or no longer shows the job, open
   https://amcr-test.aiscr.cz/admin/import-data-reports/ (**Reporty hromadného importu**).
   Find the matching **ID úlohy**, then use its **Stáhnout** link. Preserve the task ID
   and report identity when a partial and final report differ.
4. **Report uložen** displays a server/container path. Record that text for diagnosis;
   it is not the local download location and must not be handed over as though the
   agent could read it from the workstation. Use the download routes above.
5. Capture reports promptly. The inspected local code retains terminal Redis state
   for six hours; persisted report availability is a separate mechanism and must be
   checked on the deployed instance. Retained local copies do not depend on either.

If rejection occurs before a task/report exists, retain the actual form/error screenshot
and the agent's `report-unavailable.json` observation naming that fact and time. Do not
invent an XLSX or a task ID. The checkpoint identifies this as a form rejection.
Controlled management procedures retain their named command outputs instead of XLSX.

The agent reads the `Import` and `Fedora` XLSX sheets. Do not manually compare or copy
hundreds of rows. Keep a screenshot only for required UX transitions or unexpected
states; save it as `ui-validation.png` or `ui-final.png`. For timing/responsiveness,
the human records actual observations and times, rather than inferred screenshot timing.

## SQL fallback when the agent has no authorized DB connection

1. Confirm the connection is to the test DB. The agent provides the exact generated
   read-only script; it starts `BEGIN TRANSACTION READ ONLY` and performs SELECTs.
2. Run `sql/schema.sql` once for preflight and `sql/references.sql` for the reference
   selection. Save each query's single JSON value as UTF-8 `schema.json` and
   `references.json` in the exact preflight directory named by the agent.
3. For the card's `sql/snapshot.sql`, retain the single JSON value before the import as
   `db-before.json` and after as `db-after.json`. Copy the result **cell value**, not the
   SQL text or a screenshot. If exporting CSV is easier, retain that CSV unchanged and
   give it to the agent for decoding; do not hand-edit its quoting.
4. The agent compares values, relationships, history, controls and counts. Missing
   exports remain unverified. Do not run setup SQL or edit data as part of this fallback.

The agent uses `operator-query --ident U-xxxxxx --output ...` to generate an exact
read-only operator-key/role query without personal fields. Record the effective
application timezone as well; this pack's date/datetime expectations use Europe/Prague.
This is a non-secret setting, not a request for the application's configuration file.

After queries retain baseline numeric keys and link-table watermarks. This exposes
newly orphaned or shared history/file/component links after deletion or failure.
If unrelated concurrent allocations appear, correlate them with the task before
attributing a defect. Keep the original controlled-setup baseline to retain detached
file/link rows even when their ordinary parent scope no longer reaches them.

The scripts use PostgreSQL [read-only transactions](https://www.postgresql.org/docs/current/sql-set-transaction.html).
Their geographic reference selection uses a small [PostGIS envelope](https://postgis.net/docs/ST_MakeEnvelope.html)
containing the generated coordinate variants. Verify the deployed schema/functions via
the initial exports; source/model agreement alone is not a deployed SQL execution result.

## Give the agent access

On the shared machine, place the downloaded files in the exact run directory and send
its full absolute path. On another machine, copy the run folder into the opened agent
workspace or attach the card's named evidence files, preserving their filenames and
the run/batch/task identifiers. A browser download-folder name alone is insufficient.

Use this message:

> Suite [behaviour/load], run [run ID], batch [batch ID], task [ID úlohy]. The evidence
> directory is [full absolute path]. Check the retained files and tell me the next step.
> Observed state/messages and responsiveness: [what actually happened].

The agent verifies hashes, records the checkpoint and supplies a continuation message
for a fresh agent. Retain original reports even when parsing or verification fails.

## What remains after testing

Keep input manifests/checksums, sanitized source recipes, reference/schema exports,
actual key/path mappings, stage/final XLSX files, required screenshots/observations,
DB/Fedora baselines/results, verification reports, findings and recovery records.
Keep volume source files until their dependent tests/recovery are finished. Data
cleanup uses exact run-owned targets and separate authorization; it does not delete
the run evidence. Evidence retention ends only on an explicit later decision.
