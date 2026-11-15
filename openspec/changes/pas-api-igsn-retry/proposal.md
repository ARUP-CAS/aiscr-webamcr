## Why

PAS API endpoints that change an archived (SN4) samostatný nález commit the database first and only then update
IGSN metadata in DataCite. When the IGSN update raises `DoiWriteError`, the endpoint rolls back the Fedora transaction
and returns HTTP 500, but the database changes stay committed
([ARUP-CAS/aiscr-webamcr#4523](https://github.com/ARUP-CAS/aiscr-webamcr/issues/4523)). The result is the worst of
all outcomes, reproduced locally on 2026-11-15:

- PATCH `evidencni-cislo`: the new value and the `SN-UPD`/`SN34` history rows stay in the database, while Fedora keeps
  the old metadata.
- POST `upload-foto`: a `Soubor` row stays in the database, but its binary was rolled back in Fedora and cannot be
  recovered (the file exists only in the request).
- The client (Museion) receives 500 for a change that was saved; a retried upload creates a duplicate file.

Moving the IGSN call back inside the database transaction is not the chosen fix: a DataCite write cannot be undone, so
it would only trade this inconsistency for "DataCite has data AMČR rolled back", and a DataCite outage would keep
blocking every edit of archived records. The order fixed by
[ARUP-CAS/aiscr-webamcr#4122](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4122) (IGSN after `save_metadata()`)
must also be preserved.

## What Changes

- **BREAKING (API contract)**: when the IGSN update fails, the PATCH `evidencni-cislo` and POST `upload-foto`
  endpoints no longer return HTTP 500. They keep the database and Fedora changes, return their normal success response
  (200 resp. 201 with XML metadata) and add the response header `X-IGSN-Status` with value `retry-pending` (DataCite
  unreachable, 429 or 5xx) or `failed` (any other DataCite rejection, including 401/403).
- The IGSN update runs after the Fedora transaction is committed, so DataCite only receives data that both the database
  and Fedora hold.
- The IGSN update checks DataCite response statuses (`check_status=True`); today a DataCite 5xx or a rejected update
  passes silently as success.
- A new Celery task retries retryable IGSN failures of a samostatný nález with exponentially growing delays
  (20 retries, delay doubling from 60 s and capped at 6 h, all as named constants) until it succeeds, the record no
  longer needs it, a non-retryable failure occurs, or the retries are exhausted (logged as an error with `ident_cely`).
- `ApiRequestLog` gets a new field `igsn_status` that records the IGSN outcome for audit (`retry_pending`, `failed`)
  and is updated by the retry task (`updated` or `failed`). It is shown and filterable in the Django admin.
- A new management command `retry_failed_igsn_updates` lets an operator re-run IGSN updates of records with `failed`
  entries (e.g. after fixing DataCite credentials), with `--ident` and `--dry-run`.
- The PAS API documentation describes the header, the retry behaviour, the audit field and the command.
- The message key `api.views.SamostatnyNalezEvidencniCisloPatchView.patch.doi_update_error` is no longer returned by
  the API.

This change affects application behaviour only; it does not touch governance, agent configuration, or any
`aiscr-management` hub baseline or sync path.

## Capabilities

### New Capabilities

- `pas-api`: Behaviour of the PAS API endpoints for samostatný nález records — here the consistency guarantees,
  client signalling, retry and audit when the IGSN (DataCite) update of an archived record fails.

### Modified Capabilities

None. No durable specs exist in `openspec/specs/` yet.

## Impact

- Code: `webclient/api/views.py` (`PasApiBaseView._update_igsn_if_archived`,
  `SamostatnyNalezEvidencniCisloPatchView.patch`, `SamostatnyNalezFotografieUploadView.post`), `webclient/cron/tasks.py`
  (IGSN outcome helper and retry task), `webclient/api/management/commands/retry_failed_igsn_updates.py` (new
  command), `webclient/core/constants.py` (retry and `igsn_status` constants), `webclient/api/models.py` and
  `webclient/api/admin.py` (`ApiRequestLog.igsn_status`).
- Database: one new migration in `webclient/api/migrations/` adding a nullable column to `ApiRequestLog`.
- Translations: labels for the new field and its choices in `locale/*/LC_MESSAGES/django.po`.
- Tests: `webclient/api/tests/test_api.py` — both `test_doi_write_error_on_archived_record_returns_500` tests and the
  `doi_update_error` assertion change to the new contract; new tests for the outcome helper, the retry task and the
  management command.
- Docs: `docs/source/05_integrace/pas_api.rst`; regenerated module docs under
  `docs/source/04_django_aplikace/04_02_moduly/`.
- API clients: Museion must read `X-IGSN-Status` to learn about a pending or failed IGSN update; clients that ignore
  the header keep working and see a normal success.
- Operations: requires the Celery worker (already deployed) and the new migration; retry budget is defined by code
  constants, not settings.
