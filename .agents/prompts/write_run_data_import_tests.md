# Writing `run_data_import` tests for a new mapper

Operational guide for agents adding integration-style tests for `cron.tasks.run_data_import` covering a specific `ImportModelMapper` subclass. The Heslar tests at `webclient/cron/tests/test_run_data_import_heslar.py` are the reference implementation — mirror their structure.

These tests exercise the full task end-to-end (data save, history, fedora, file phases) with Redis, Fedora HTTP, and signal-side fedora calls mocked. They are **not** mapper unit tests — for those, see `reference_mapper_unit_tests.md` in agent memory.

## File layout

- Path: `webclient/cron/tests/test_run_data_import_<model_lower>.py`.
- Inherit from `django.test.TestCase` (savepoint-based, fast; do **not** use `TransactionTestCase` unless you specifically need `on_commit` callbacks to fire).
- Constants at module level: `JOB_ID`, `LOCK_TOKEN`, the mapper's `__file_name` key, and the test record's primary-key value.

## setUpTestData

Create the minimal fixtures the mapper requires (heslář entries, organization, user that will be passed as `transaction_user`). Wrap the fixture creation in the same Fedora patches so the fixtures' `save_metadata` / pre-save signals don't make real HTTP calls:

```python
with patch(
    "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
    return_value=True,
), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
    # create_or_get fixtures here
```

## The `_run_import` helper

Centralises the patches needed for every test. Always patch all of these — missing any one of them produces confusing failures (real HTTP attempts, signal explosions, or atomic rollbacks that undo the operation under test):

| Patch target | Purpose |
|---|---|
| `core.connectors.RedisConnector.get_connection` | return your `FakeRedis` |
| `core.connectors.RedisConnector.refresh_import_lock` | default `return_value=True`; parameterise for lock-loss tests |
| `core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists` | `return_value=True` |
| `xml_generator.models.ModelWithMetadata.save_metadata` | `autospec=True, side_effect=…` (record calls or raise) |
| `cron.tasks.FedoraTransaction` | `return_value = MagicMock(uid="...")` |
| `cron.tasks.FedoraDeletionOnlyTransaction` | `return_value = MagicMock(updated_ident_cely=set())` — without this DELETE tests hit a real Fedora call inside `__create_transaction` and the inner exception handler calls `transaction.set_rollback(True)`, silently undoing the row delete |
| `<model_app>.signals.FedoraTransaction` | mock the **local** binding in the signals module where it's `from … import FedoraTransaction`-ed; patching `core.repository_connector.FedoraTransaction` does **not** rebind already-imported names |

Pattern (verbatim from Heslar):

```python
refresh_lock_kwargs = (
    {"side_effect": refresh_lock_side_effect}
    if refresh_lock_side_effect is not None
    else {"return_value": True}
)
with patch("core.connectors.RedisConnector.get_connection", return_value=fake_redis), \
     patch("core.connectors.RedisConnector.refresh_import_lock", **refresh_lock_kwargs), \
     patch("core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
           return_value=True), \
     patch("xml_generator.models.ModelWithMetadata.save_metadata",
           autospec=True, side_effect=side_effect), \
     patch("cron.tasks.FedoraTransaction") as fedora_transaction_mock, \
     patch("cron.tasks.FedoraDeletionOnlyTransaction") as fedora_deletion_mock, \
     patch("<model_app>.signals.FedoraTransaction") as signals_fedora_transaction_mock:
    fedora_transaction_mock.return_value = MagicMock(uid="test-fedora-uid")
    fedora_deletion_mock.return_value = MagicMock(uid="test-deletion-uid", updated_ident_cely=set())
    signals_fedora_transaction_mock.return_value = MagicMock(uid="test-signals-uid")
    cron_tasks.run_data_import(JOB_ID, self.user.id, LOCK_TOKEN)
```

To discover the `<model_app>.signals` target: grep for `pre_delete\|post_save\|pre_save` receivers on the model in question, then check which module they're declared in and what local name they use for `FedoraTransaction`.

## Building the FakeRedis fixture

Each test stages a serialized record per record_id at `import_data_{JOB_ID}_record_{i}` plus the count and performed-action keys.

```python
FakeRedis({
    f"import_data_count_{JOB_ID}": str(len(records)),
    f"import_performed_action_{JOB_ID}": performed_action,
    f"import_data_{JOB_ID}_record_0": json.dumps(serialized_record),
    # …
})
```

Critical column-structure rules — these come from `ImportModelMapper._check_column_structure`:

- **INSERT** — `value_dict.keys()` must equal `mapper.get_mapping().keys() | {primary_key}` exactly. Missing or extra keys raise `ImportDataIncorrectStructureError`.
- **UPDATE** — primary-key column required, no excess columns allowed.
- **DELETE** — **only** the primary-key column may appear. Sending any other column raises `ImportDataIncorrectStructureError`, which the inner except catches and calls `set_rollback(True)`, leaving the row in place. This was the most common subtle failure when authoring the Heslar tests — DELETE fixtures need their own minimal payload.

`__file_name` is popped by the task before the mapper sees the dict, so it doesn't count toward column-structure validation but must match the mapper's `@ImportModelMapper.register(...)` name.

## Assert helpers

- `_assert_import_failed(fake_redis)` — checks `import_data_progress_{JOB_ID}` equals `IMPORT_PROGRESS_PHASE_FAILED` (0) and the stop flag is set. Reuse for every failure-mode test.
- `_create_existing_<model>()` — factored creation of a pre-existing row for UPDATE/DELETE/duplicate-INSERT tests.

## Standard test matrix

For each new mapper, add these tests in this order. They share the helper above so total LOC is small.

1. **Happy-path INSERT** — record saved to DB, `save_metadata` called, `import_data_primary_keys_{JOB_ID}` populated.
2. **Happy-path UPDATE** — pre-create row, run UPDATE, verify fields updated and `save_metadata` called again.
3. **Happy-path DELETE** — pre-create row, run DELETE (minimal-payload fixture), verify row no longer in DB.
4. **DB save failure** — `patch.object(<Model>, "save", side_effect=RuntimeError(...))`. Asserts `_assert_import_failed`. Exercises the inner data-phase except + `set_rollback`.
5. **History save failure** — `patch.object(Historie, "save", side_effect=…)`. If the mapper's `get_record_history` returns `None` by default (most mappers do), also `patch.object(<Mapper>, "get_record_history", staticmethod(lambda record: record))` so the history loop actually runs. Asserts `_assert_import_failed`.
6. **Fedora save failure** — `save_metadata` side_effect raises. Asserts `_assert_import_failed`.
7. **Multi-record rollback** — 3 INSERTs where the 2nd has a unique-constraint conflict with the 1st. Verify none of the three persists (atomic rollback) and `_assert_import_failed`.
8. **User stop mid-import** — pre-set `import_data_stop_{JOB_ID}` in FakeRedis; verify status message contains `stopped_by_user`. (Status messages are gettext keys when no `.po` is compiled; `assertIn("stopped_by_user", …)` works.)
9. **UPDATE on nonexistent row** — no fixture, UPDATE payload. Exercises `DoesNotExist` from `create_records`. `_assert_import_failed`.
10. **INSERT duplicate primary key** — pre-create row, INSERT same `ident_cely`. Exercises `IntegrityError`. `_assert_import_failed` + verify original row unchanged.
11. **Lock lost mid-import** — `refresh_lock_side_effect=[True, False, False, …]` (first True so the initial acquisition at line 562 of `tasks.py` passes, then False for the per-record refresh). Verify status contains `failed_lock_lost` (the special branch in the outer except preserves this status; the inner except does not). `_assert_import_failed`.
12. **Success marker in progress details** — happy-path INSERT, verify the `import_data_progress_details_{JOB_ID}` list contains `cron.tasks.run_data_import.success` after success.

## Pitfalls encountered

- **`HeslarMapper.get_record_history` returned `None`** — default behaviour for most mappers. Without patching it the history loop is empty and the history-failure test can never trigger. Same caveat applies to any mapper whose `get_record_history` returns `None`.
- **Signal-time `FedoraTransaction`** — model-specific pre/post-save/delete signals often instantiate `FedoraTransaction()` themselves. Patch the binding in the signal module, not just `cron.tasks.FedoraTransaction`.
- **`get_record_from_ident(ident)` in the fedora-update phase** — when a DELETE just removed the row, this raises `Http404`. The fedora loop catches it inside its `try`, marks `failed=True`, but the data-phase DELETE itself is already committed (separate atomic block). The test should still verify the row is gone, not that the import succeeded overall.
- **`transaction.set_rollback(True)` is called by the inner data-phase except** — any uncaught exception within the per-record `try` rolls back the whole atomic block, including operations from prior loop iterations. Use this for the multi-record-rollback test; avoid it surprising you in DELETE tests by paring the DELETE payload down to the primary key.
- **`Django TestCase` swallows `on_commit` callbacks** — `instance.record_deletion(...)` scheduled by signal handlers never fires under `TestCase`. This is desirable for these tests (we don't want real Fedora deletion side-effects), but means you can't assert anything about post-commit work from these tests.

## Pre-flight before running

```bash
docker compose -f docker-compose-dev-local-db-all-containers.yml exec web \
  python manage.py test cron.tests.test_run_data_import_<model> -v 2
```

Tests must run inside the `web` container (per `feedback_docker_tests.md` in agent memory — never via local venv). If you change `cron/tasks.py` while iterating, **restart the celery worker** before manual end-to-end re-tests; unit tests pick up changes automatically.
