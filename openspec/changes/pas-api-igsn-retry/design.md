## Context

`SamostatnyNalezEvidencniCisloPatchView.patch` and `SamostatnyNalezFotografieUploadView.post`
(`webclient/api/views.py`) currently run:

1. `transaction.atomic()`: database writes, history records, `save_metadata()` into an open Fedora transaction.
2. Database commit.
3. `_update_igsn_if_archived()` → `SamostatnyNalez.igsn_update(False, True)` (DataCite GET + PUT).
4. `FedoraRepositoryConnector.get_metadata()` and `FedoraTransaction.mark_transaction_as_closed()` (Fedora commit).

A `DoiWriteError` in step 3 is caught, the Fedora transaction is rolled back and HTTP 500 is returned, while the
database stays committed (#4523). Facts that shape the design:

- The IGSN payload (`pid/model_serializers.py`, `SamostatnyNalezSerializer`) is built from the database only;
  `update_record(reload_record=True)` calls `refresh_from_db()`. #4122 fixed the *order* (IGSN after the last database
  write), not the transaction placement. The payload carries the whole record: `evidencni_cislo` as an
  `alternateIdentifier`, files as `relatedIdentifier` URLs.
- `DigitalObjectIdentifierClient.update_record(check_status, …)` (`pid/client.py`) behaves as follows:

  | DataCite outcome | `check_status=False` (today) | `check_status=True` |
  |---|---|---|
  | GET network error | `DoiConnectionError` | `DoiConnectionError` |
  | GET 5xx | treated as "does not exist", nothing sent, no error | `DoiConnectionError` |
  | GET 404 | info log, nothing sent, no error | same |
  | PUT 4xx / 5xx | ignored | `DoiWriteError(status_code=…)` |
  | PUT network error | raw `requests.RequestException` | raw `requests.RequestException` |

- An IGSN update is a full-state PUT (`serialize_update()` = publish payload without `event`), so repeating it is safe.
- Fedora metadata is generated from the database, but an uploaded binary exists only in the request and the Fedora
  transaction.
- Celery already runs (`cron/tasks.py`, `@shared_task(bind=True, max_retries=...)` pattern in `load_news_feed`);
  `xml_generator.models.check_if_task_queued` detects scheduled tasks for a record.
- `ApiRequestLog` (`api/models.py`) has `status` (received/processing/success/failure) and `errors` (JSON) but no
  field for a secondary outcome.

## Goals / Non-Goals

**Goals:**

- Database and Fedora always end a PAS API request in the same state when only the IGSN update fails.
- DataCite never receives data that the database and Fedora do not hold.
- Every DataCite failure of the PAS API is detected and reported to Museion, without breaking clients that ignore the
  signal.
- Transient failures are repaired automatically; permanent failures are visible and can be re-run by an operator.

**Non-Goals:**

- Closing the pre-existing gap where the Fedora commit fails after the database commit (#4437, #4473).
- Changing IGSN/DOI handling in the UI views (`pas/views.py`, `projekt/views.py`, …), other record types, or
  `pid/client.py` itself.
- A record that exists in AMČR with an IGSN but not in DataCite (GET 404): it stays an info log and is treated as "no
  update needed", as today.
- Durable retry state that survives loss of the Celery broker (outbox table).

## Decisions

### D1. Run the IGSN update after the Fedora commit

New order: database transaction → `get_metadata()` + `mark_transaction_as_closed()` → IGSN update.
The IGSN payload is still built after `save_metadata()` and the last `save()`, so the #4122 ordering is kept.

- *Alternative: keep IGSN between database commit and Fedora commit.* Rejected: a Fedora commit failure would leave
  DataCite ahead of both AMČR stores.
- *Alternative: IGSN inside the database transaction (fix A).* Rejected by decision on #4523: the DataCite write is
  irreversible and a DataCite outage would block edits of archived records.

`get_metadata()` reads metadata inside the still-open Fedora transaction, so the response body is unchanged.

### D2. Check DataCite statuses and classify failures

The PAS API and the retry task call `igsn_update(True, True)`. A shared helper in `webclient/cron/tasks.py`, used by
the views and the task, runs the update and returns an outcome:

| Outcome | Raised by | Classification |
|---|---|---|
| `requests.RequestException` | PUT network error | retryable |
| `DoiConnectionError` | GET network error, GET 5xx | retryable |
| `DoiWriteError` with `status_code` 429 or ≥ 500 | PUT | retryable |
| any other `DoiWriteError` (4xx incl. 401/403) | PUT | non-retryable |

401/403 are non-retryable because wrong credentials do not heal by waiting; the operator fixes the configuration and
re-runs (D6). The raw `requests.RequestException` is handled in the helper rather than wrapped in `pid/client.py`, so
other DOI/IGSN callers are unaffected.

- *Alternative: keep `check_status=False`.* Rejected: GET 5xx and every PUT error would pass as success, so neither
  the client nor the retry could know an update is missing.

### D3. Signal the outcome with a response header

The views return the normal `_success()` response and add `X-IGSN-Status: retry-pending` (retryable) or
`X-IGSN-Status: failed` (non-retryable). No header when the update succeeded or the record is not SN4. Each failure is
logged (`warning` for retryable, `error` for non-retryable) with `ident_cely` and the error.

- *Alternative: HTTP 202.* Rejected: clients must then treat a new status as success.
- *Alternative: JSON body with a warning.* Rejected: breaks the XML success format.
- *Alternative: reject the change on a non-retryable failure.* Rejected: the payload is the whole record, so a 4xx is
  usually caused by other data or configuration, not by the request; rejecting would need the DataCite call inside the
  transaction (fix A) or a hand-written undo (fix B), and DataCite offers no validate-only call.

### D4. Retry with a Celery task

New task in `webclient/cron/tasks.py`:

```python
@shared_task(bind=True, max_retries=IGSN_RETRY_MAX_RETRIES)
def retry_samostatny_nalez_igsn_update(self, class_name: str, samostatny_nalez_pk: int) -> None: ...
```

- Arguments follow the `(class_name, pk)` convention of `update_single_redis_snapshot`, which
  `check_if_task_queued` matches on; retries are re-published with the same arguments, so a waiting retry chain is
  detected too.
- Loads `SamostatnyNalez` by pk; stops if it does not exist, `stav != SN_ARCHIVOVANY` or `igsn` is empty.
- Runs the D2 helper. On a retryable failure it calls `self.retry(countdown=...)` with an exponentially growing delay
  `countdown = min(IGSN_RETRY_BASE_DELAY * 2 ** (self.request.retries + 1), IGSN_RETRY_MAX_DELAY)`. The first attempt
  is scheduled with `IGSN_RETRY_BASE_DELAY`, so the delay before attempt n is `min(60 s × 2^(n−1), 6 h)`.
- Constants in `webclient/core/constants.py` (`Final`, like other module constants):
  `IGSN_RETRY_MAX_RETRIES = 20`, `IGSN_RETRY_BASE_DELAY = 60`, `IGSN_RETRY_MAX_DELAY = 6 * 60 * 60`.
  Resulting schedule: 60 s, 2 min, 4 min, … 4 h 16 min (attempt 9), then 6 h for attempts 10–21; 21 attempts spread
  over about 80.5 h (≈ 3.4 days). The 6 h cap prevents the 20th doubling from reaching months.
- No jitter: tasks are per record and few, so synchronised retries are not a load concern.
- A non-retryable failure, `MaxRetriesExceededError`, or a stop condition ends with `logger.error(...)` including
  `ident_cely` and the reason.
- On success the task sets `igsn_status = updated`, on any other end `igsn_status = failed`, for all `ApiRequestLog`
  rows of the record that are still `retry_pending` (D5).
- The views schedule it with `apply_async(["SamostatnyNalez", pk], countdown=IGSN_RETRY_BASE_DELAY)` only for a retryable failure and
  unless `check_if_task_queued("SamostatnyNalez", pk, "retry_samostatny_nalez_igsn_update")` reports one already
  scheduled. Duplicates are harmless (full-state PUT), so the check is best-effort.

- *Alternative: outbox table + periodic task.* Rejected for now: survives broker loss but needs another model; can be
  added later without changing the API contract.

### D5. Audit field `ApiRequestLog.igsn_status`

New nullable `CharField(max_length=20, choices=...)` on `ApiRequestLog` with values from `core/constants.py`:
`API_REQUEST_LOG_IGSN_STATUS_RETRY_PENDING = "retry_pending"`, `..._UPDATED = "updated"`, `..._FAILED = "failed"`.

- The view stores `retry_pending` or `failed` on its log entry together with the success update (`_success()` gains an
  optional `igsn_status` argument that also adds the response header, so the entry is saved once).
- The task updates rows by record (`ApiRequestLog.objects.filter(samostatny_nalez_id=pk, igsn_status=retry_pending)`),
  not by log id. Several requests for one record that share a single scheduled task are therefore all resolved by it.
- Shown in `ApiRequestLogAdmin` (`list_display`, `list_filter`, `readonly_fields`).

- *Alternative: write a note into the existing `errors` JSON field.* No migration, but `errors` means failure and
  cannot hold the later outcome cleanly; rejected.
- *Alternative: new `status` value such as `success_igsn_pending`.* Mixes two dimensions into one field and breaks
  existing status filters; rejected.

### D6. Management command `retry_failed_igsn_updates`

New command in `webclient/api/management/commands/retry_failed_igsn_updates.py` (the `api` app owns
`ApiRequestLog`):

- Selects distinct `samostatny_nalez_id` of `ApiRequestLog` rows with `igsn_status = failed`, optionally limited by
  repeated `--ident <ident_cely>`.
- Without `--dry-run`: in one transaction sets those rows to `retry_pending`, then (on commit) schedules
  `retry_samostatny_nalez_igsn_update.apply_async(["SamostatnyNalez", pk], countdown=0)` per record. The task's normal outcome handling
  then sets `updated` or `failed` again.
- With `--dry-run`: prints the affected `ident_cely` values and the number of entries, changes nothing.
- Prints a summary (records scheduled, entries reset).

- *Alternative: run the IGSN update synchronously in the command.* Rejected: duplicates the task's classification and
  retry logic; scheduling reuses it, and transient failures during the re-run get the normal retries.

## Risks / Trade-offs

- [DataCite lags behind AMČR until a retry succeeds] → retries with backoff; `igsn_status` and error logs make it
  visible; D6 re-runs failed records.
- [A non-retryable failure leaves DataCite outdated until someone acts] → error log and `failed` in admin; operator
  fixes the cause and runs D6 or the manual IGSN update in `pid/views.py`.
- [Retry lost if the Celery broker drops the task] → the entry stays `retry_pending`; accepted for now. Outbox pattern
  is the follow-up if this proves insufficient.
- [Museion ignores the header] → behaviour is still correct (data saved); documentation states the header.
- [Contract change: tests and clients expecting 500] → tests rewritten in this change; Museion informed via the PAS API
  documentation and the PR.
- [GET 404 still looks like success] → recorded non-goal; it is a missing IGSN registration, not a failed update.
- [`check_if_task_queued` only inspects `worker1@amcr` scheduled tasks] → duplicates possible but idempotent.
- [Long retry window (≈ 3.4 days)] → `igsn_status` and error logs make stuck records visible in admin.

## Migration Plan

One schema migration adds the nullable `igsn_status` column to `ApiRequestLog` (no data migration, safe on a live
table). Deploy web and Celery worker together (the worker must know the new task before the web container schedules
it). Rollback: revert the code and the migration; already scheduled tasks for an unknown task name are discarded by
Celery with an error log, with no data impact.

## Open Questions

None.
