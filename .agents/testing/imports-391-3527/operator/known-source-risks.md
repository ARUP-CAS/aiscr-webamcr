# Source observations to carry into preflight

The frozen inventory pins commit `32d9a23b356259ea2c289d5b084f308f8505cb5e` (`test`,
2026-11-14). Its pinned sources have the same content as the originally inspected
commit `202cd7f0056e72ba44a745709df608d20133bc5b`. Source hashes use line-ending-
normalised content (`sha256-lf-text-v1`), so CRLF and LF checkouts agree.
The actual test-instance revision remains a mandatory preflight fact. Historical
testing reports supply failure hypotheses, never current pass/fail evidence.

## Deployed revision on the test instance

The last recorded TEST deployment (2026-11-06) shipped tag `v2.0.0-alpha.2`
(`3d4a4dd15e83c769eaa78235c985b326ae838a24`). Running `pack.py deployment-parity`
against it reports:

- `webclient/core/repository_connector.py` differs: the tag lacks
  [ARUP-CAS/aiscr-webamcr#4493](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4493)
  (Fedora commit failure goes through rollback and releases the record lock). This
  affects the expectation for `session.fedora-commit-failure`.
- Both PO catalogs differ only outside the entries this pack uses
  (`catalog_entries_equal`), so labels and diagnostics are unaffected.

Until TEST is redeployed, start a run against that tag only with a reviewed parity
record that withholds the affected coverage, for example
`{"webclient/core/repository_connector.py": {"withheld_coverage": ["session.fedora-commit-failure"], "reason": "#4493 not deployed", "reviewer": "<operator>"}}`.
Re-check the deployed revision at session start; a newer deployment needs a new
parity record.

## Known defect: `VazbaLookupImportField` fallback (checks deferred)

This is a source-confirmed defect in `VazbaLookupImportField._process_value`
(`webclient/core/import_data_mappers.py`, lines 1381–1421). It is reported for the
developer and is not fixed by this pack. The frozen record is
`definitions/known-defects.json`. The isolated probe is `definitions/source-probes.json`.

1. When `get_record_from_ident` does not return a usable owner, the fallback iterates
   `self.records` (line 1417). The field exposes only `get_records()`, so this raises
   `AttributeError`.
2. Even after (1) is corrected, the fallback assigns `filtered_records[0].historie`
   (line 1421) regardless of `read_field_name`. Component (`komponenty`) and file
   (`soubory`) owners would receive the wrong object.

The `komponenty`, `soubory` and `historie` mappers reach the fallback when the
owner value:

- **`owner-not-persisted`**: is created in the same import, or by a batch that is
  not guaranteed to run earlier;
- **`no-identifier-pattern`**: has no `get_record_from_ident` pattern, as with
  cooperation and file owners referenced by numeric ID, or a nonexistent reference
  (the intended `ImportDataMissingReferencedValueError` is never raised);
- **`owner-lacks-read-attribute`**: resolves to a model without the read attribute
  (`User` exposes `history_vazba`, not `historie`);
- **`document-part-missing`**: names a document part whose document exists but the
  part does not. `DokumentCast.objects.get` then raises an uncaught `DoesNotExist`.

Empty owner values become `None` and take the required-field path instead.

`run_data_import` catches only `ImportData*` errors per row
(`webclient/cron/tasks.py:1470`). The exception reaches the outer `except Exception`
(`webclient/cron/tasks.py:1519`), and the whole validation job fails with
`core.admin.import_data.error.unexpected_error`. One triggering row therefore hides
every other check in its ZIP.

The build classifies every row against the state its batch's prerequisites guarantee,
and defers any batch containing a triggering row, together with that batch's
dependents. Deferred batches keep their prepared inputs. They get no instruction
card, cannot be checkpointed, and their coverage is reported `blocked` with the fix
as the prerequisite. Behaviour now defers:

| Batch | Coverage |
| --- | --- |
| `N07x-deferred-known-defects` (split out of N07, which keeps its other 362 checks) | `historie.field.vazba.missing-lookup`, `komponenty.field.vazba.missing-lookup`, `soubory.field.vazba.missing-lookup` |
| `V17-branches-update` | `historie.branch.user-owner` |
| `V18-branches-update` | `historie.branch.cooperation-owner` |
| `V19-branches-update` | `historie.branch.file-owner` |

Relational load defers `L01-relational-50000`: its 10,000 components point at
documentation units created in the same import. The same rows are measured as a
two-import substitute: `L01a-relational-parents-30000`, then
`L01b-relational-components-20000`. Reports label the substitute figures as such.
They are not the combined-import figure. The distribution workload is unaffected.

After the developer fix is deployed, record
`resolved_in: {"commit": ..., "source_sha256": ...}` in
`definitions/known-defects.json` and rebuild. The deferred checks then return to their
ordinary batches and the combined relational import replaces the substitute. If the
mapper source changes without such a record, the build refuses instead of guessing.

Sources at the pinned commit:
[ownership lookup](https://github.com/ARUP-CAS/aiscr-webamcr/blob/32d9a23b356259ea2c289d5b084f308f8505cb5e/webclient/core/import_data_mappers.py#L1381-L1421),
[identifier resolver](https://github.com/ARUP-CAS/aiscr-webamcr/blob/32d9a23b356259ea2c289d5b084f308f8505cb5e/webclient/core/ident_cely.py#L479),
[validation error handling](https://github.com/ARUP-CAS/aiscr-webamcr/blob/32d9a23b356259ea2c289d5b084f308f8505cb5e/webclient/cron/tasks.py#L1460-L1522),
[query attachment from ARUP-CAS/aiscr-webamcr#391](https://github.com/user-attachments/files/20712616/import_export_dotazy.zip).

## Thumbnail-history backfill scope

`backfill_thumb_history` accepts `--dry-run` and `--limit`, with no file-ID filter.
`--limit` selects the first numeric PKs and cannot restrict execution to this run's
new files. Backfill cards therefore require an isolated fixture environment or separate
explicit approval covering the whole scanned scope. They are management procedures,
not CSV-upload cards. Do not substitute the provided read-only Fedora access for the
application/DB authority required by that command.

The fixture replacement first establishes multiple thumbnail versions. Retain the
complete selected history and version lists before preparing a legacy missing-history
state. Check exact oldest/later version timestamps and `ADMIN_USER`, then repeat the
command to prove idempotence. Missing-history-link setup has its own restoration proof.

Source: [backfill command at the pinned commit](https://github.com/ARUP-CAS/aiscr-webamcr/blob/32d9a23b356259ea2c289d5b084f308f8505cb5e/webclient/core/management/commands/backfill_thumb_history.py).
