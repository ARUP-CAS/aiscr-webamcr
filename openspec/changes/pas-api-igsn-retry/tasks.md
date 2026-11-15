## 1. Audit field

- [x] 1.1 Add `API_REQUEST_LOG_IGSN_STATUS_RETRY_PENDING`, `..._UPDATED`, `..._FAILED` and `IGSN_RETRY_MAX_RETRIES = 20`,
      `IGSN_RETRY_BASE_DELAY = 60`, `IGSN_RETRY_MAX_DELAY = 6 * 60 * 60` to `webclient/core/constants.py`
- [x] 1.2 Add the nullable `igsn_status` field with choices to `ApiRequestLog` in `webclient/api/models.py` and generate
      the migration with `manage.py makemigrations api`
- [x] 1.3 Show `igsn_status` in `ApiRequestLogAdmin` (`list_display`, `list_filter`, `readonly_fields`)
- [x] 1.4 Add Czech and English labels for the field and its choices to `locale/*/LC_MESSAGES/django.po`

## 2. IGSN update helper and retry task

- [x] 2.1 Add the outcome helper to `webclient/cron/tasks.py`: runs `igsn_update(True, True)` and classifies the result
      as success, retryable (`requests.RequestException`, `DoiConnectionError`, `DoiWriteError` 429/5xx) or
      non-retryable (other `DoiWriteError`, incl. 401/403), with a Czech Sphinx docstring
- [x] 2.2 Add `retry_samostatny_nalez_igsn_update` `@shared_task(bind=True, max_retries=IGSN_RETRY_MAX_RETRIES)`:
      reload record, SN4/IGSN guard, helper call, retry with countdown
      `min(IGSN_RETRY_BASE_DELAY * 2 ** (retries + 1), IGSN_RETRY_MAX_DELAY)` on retryable failures, error log with
      `ident_cely` on any end without success, `igsn_status` update of the record's `retry_pending` log entries to
      `updated`/`failed`, with a Czech Sphinx docstring
- [x] 2.3 Add tests for the helper: each row of the classification table (network error on GET and PUT, GET 5xx,
      PUT 429, PUT 503, PUT 422, PUT 401, PUT 403, success)
- [x] 2.4 Add tests for the task: success sets `updated`; retryable failures schedule retries with delays
      60/120/240/480 s and never above 6 h; 422 stops, logs an error and sets `failed`; exhausted retries log an error
      and set `failed`; record not SN4 / without IGSN / deleted sends nothing and sets `failed`

## 3. PAS API views

- [x] 3.1 Let `_success()` accept an optional `igsn_status` that is stored on the log entry in the same save and adds
      `X-IGSN-Status: retry-pending` or `X-IGSN-Status: failed`
- [x] 3.2 Add a `PasApiBaseView` method that, for an SN4 record, runs the helper, logs the failure, schedules the retry
      task for a retryable failure (skipping when `check_if_task_queued` finds one) and returns the `igsn_status` to
      record (or `None`)
- [x] 3.3 In `SamostatnyNalezEvidencniCisloPatchView.patch`, remove the IGSN call and the `except DoiWriteError` branch
      from the save block; call the new method after `mark_transaction_as_closed()` and pass its result to
      `_success()`
- [x] 3.4 Apply the same change to `SamostatnyNalezFotografieUploadView.post` (201 response)
- [x] 3.5 Replace `_update_igsn_if_archived` with the new method (removing the local `#4523` DoiWriteError simulation
      hook) and update the docstrings of both views and `_success()`

## 4. Management command

- [x] 4.1 Add `webclient/api/management/commands/retry_failed_igsn_updates.py` with `--ident` (repeatable) and
      `--dry-run`: reset the selected `failed` entries to `retry_pending` and schedule one retry task per record on
      commit; print a summary; Czech Sphinx docstrings
- [x] 4.2 Add tests: default run resets entries and schedules one task per record; `--ident` limits the run;
      `--dry-run` changes nothing and schedules nothing; no `failed` entries prints an empty summary

## 5. API tests

- [x] 5.1 Rewrite both `test_doi_write_error_on_archived_record_returns_500` tests in `webclient/api/tests/test_api.py`:
      a retryable failure returns 200/201 with `X-IGSN-Status: retry-pending`, `igsn_status = retry_pending`, saved
      database changes, committed Fedora transaction and a scheduled retry task; update the `doi_update_error`
      assertion
- [x] 5.2 Add tests: a non-retryable failure (422) returns success with `X-IGSN-Status: failed`, `igsn_status = failed`
      and no scheduled task; a successful SN4 update has no header and an empty `igsn_status`; IGSN is called with
      `check_status=True` after the Fedora commit; a Fedora commit failure sends no IGSN update and returns 500

## 6. Documentation and messages

- [x] 6.1 Describe the `X-IGSN-Status` header values, the retry schedule, the `ApiRequestLog.igsn_status` audit field,
      the `retry_failed_igsn_updates` command and the changed error contract in `docs/source/05_integrace/pas_api.rst`
- [x] 6.2 Regenerate module docs with `docs/generate_module_docs.py`
- [x] 6.3 Remove the unused `doi_update_error` message key from `locale/*/LC_MESSAGES/django.po`

## 7. Verification

- [x] 7.1 Run `compileall`, `pre-commit` on the changed files and `npm run openspec:validate`
- [x] 7.2 Run the database test classes `SamostatnyNalezEvidencniCisloPatchViewTests`,
      `SamostatnyNalezFotografieUploadViewTests`, the helper, task and command tests against PostGIS + Redis, and check
      `manage.py makemigrations --check`
- [x] 7.3 Update the local repro script to the new contract (retryable and non-retryable simulation) and confirm
      against the dev stack that both scenarios keep database and Fedora changes, return the header and mark the log
      entry
- [x] 7.4 Write the usage-log entry in `.agents/reports/usage/`
