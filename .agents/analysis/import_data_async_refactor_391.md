# Hromadný import dat — asynchronous validation refactor (issue #391)

> **Bound to:** PR [ARUP-CAS/aiscr-webamcr#3895](https://github.com/ARUP-CAS/aiscr-webamcr/pull/3895)
> · Issue [ARUP-CAS/aiscr-webamcr#391](https://github.com/ARUP-CAS/aiscr-webamcr/issues/391)
>
> This is the design rationale for that PR. It exists so reviewers can see the
> justification behind individual implementation steps; section references
> (§3.2, §4.2, §5b.4, …) are cited from code comments and docstrings in the PR.

## 1. Goal

Today the bulk-import POST handler in `AmcrCustomAdminSite.import_data`
(`webclient/core/admin_sites.py`) does **all** the work synchronously inside the
HTTP request: unzip, antivirus check, parse every CSV row, instantiate a mapper
per row, run `mapper.map()` / `import_validation()` for every row, build the
validation-results table, store each valid record into Redis, and only *then*
render the page. For a large ZIP this blocks the request for minutes and will
time out.

The refactor moves validation out of the request and into a Celery task, exactly
like the existing data-import task `cron.tasks.run_data_import`. The POST
becomes a fast "accept and enqueue" operation, and the import page always
reflects the current state of the running job by reading Redis — no
import/validation data is rendered by Django from the POST context.

Requirements, restated:

1. **Validation runs as a task**, not in the POST request.
2. **Opening the import page while an import is running shows that import's
   progress** (validation phase or import phase), pulled from Redis.
3. **No data is rendered by Django from the POST.** All import/validation data
   lives in Redis and is delivered to the page through the progress endpoint.

## 2. Current behavior

Flow today:

1. User uploads a ZIP via `POST admin:import_data`.
2. `AmcrCustomAdminSite.import_data` synchronously: validates
   `ImportDataAdminForm`, reads the uploaded file into memory
   (`data_file.read()`), runs the antivirus check, opens the ZIP, orders files
   by mapper order, enforces `IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE`, then for every
   CSV row runs `mapper.map()`, `check_required_fields()`,
   `import_validation()`, `create_records()`, pushes the serialized record to
   `import_data_{job_id}_record_{record_id}`, builds
   `validation_results` / `invalid_records`, writes all status keys
   (`import_data_count_`, `import_data_valid_`,
   `import_data_validation_results_`, `import_data_progress_`, …), and renders
   `admin/import_data/import_data.html` with the validation table populated
   **from the context**.
3. The template renders the table from `validation_results` and shows the
   *Start import* button. Clicking it `POST`s `core:data-import-start`.
4. `DataImportStart` checks `import_data_valid_{job_id} == "1"`, generates a
   lock token, acquires `IMPORT_DATA_LOCK_KEY`, and calls
   `tasks.run_data_import.delay(job_id, user_id, lock_token)`.
5. The template's JS polls `core:data-import-progress` (`DataImportProgress`),
   which reads the per-job Redis keys and returns progress JSON. The JS fills in
   the DB primary key, status, history, and Fedora columns row by row.
6. `DataImportProgressReportView` exports the same Redis state to `.xlsx`.

Key facts the refactor builds on:

- There is **one global import lock**, `RedisConnector.IMPORT_DATA_LOCK_KEY`
  (`"import_data_lock"`), acquired with `SET … NX EX …` and refreshed/released
  with token-checked Lua scripts (`refresh_import_lock`,
  `release_import_lock`). It is currently acquired only in `DataImportStart` —
  only during the import phase, not during validation.
- `run_data_import` already **releases the lock in its `finally` block**
  (`webclient/cron/tasks.py:1678`) and expires every per-job key with
  `IMPORT_DATA_EXPIRATION_SECONDS`. The refactor reuses this cleanup.
- Per-job keys are all suffixed `_{job_id}`; the job_id is a 20-char random
  string generated in the POST handler.
- `import_data_validation_results_{job_id}` (list of
  `ImportDataValidationResult` dicts) is already stored in Redis and already
  consumed by `DataImportProgressReportView` — but it is written only at the very
  end of the synchronous POST, and `DataImportProgress` does not return it.
- Phase progress constants live in `cron/tasks.py`:
  `IMPORT_PROGRESS_PHASE_FAILED=0`, `_DATA_DONE=25`, `_HISTORY_DONE=50`,
  `_FEDORA_DONE=75`, `_FINISHED=100`. `IMPORT_DATA_RUNNING_TTL_SECONDS = 6h`.

## 2.5 User stories (the admin's experience)

This section describes the refactor from the admin's point of view: what they
do, what actions are available to them, and what information the page shows at
each moment. It is the user-facing counterpart to the technical architecture in
§3–§12; the phase names and buttons mentioned here are defined there.

### 2.5.1 Stories

- **US-1 — Start an import (the happy path).** *As an admin, I want to upload a
  ZIP and have it validated in the background, so that I am not staring at a
  spinning browser for minutes and can keep working.* The POST returns
  immediately and the page switches to a polling view of the `validating` phase
  (§4.1 step 11, §4.8).
- **US-2 — Watch validation progress.** *As an admin, I want to see validation
  fill in row by row, so that I know the job is alive and roughly how far along
  it is.* The page polls `DataImportProgress` and appends each row to the table
  incrementally; the validation progress bar reflects `progress_data` (computed
  from the validation numerator/denominator pair; §5b, §4.6, §4.8).
- **US-3 — Leave and come back.** *As an admin, I want to close the page (or be
  auto-signed-off) and later reopen it to find my in-flight job exactly where I
  left it, so that a session timeout does not lose my work.* Reopening the page
  binds to `import_data_current_job_{user_id}` and resumes the same view
  (requirement 2, §4.1 GET branch). The job is not tied to the browser session
  (§3.2 no-implicit-cancel).
- **US-4 — Review a validated job and start the import.** *As an admin, I want
  to review the validation table and then start the import, so that I confirm
  the file is correct before it touches the DB.* On the `awaiting_approval`
  phase the table is shown, *Start* is enabled, and clicking it dispatches
  `run_data_import` (§4.4, §4.8).
- **US-5 — See why my file was rejected and fix it.** *As an admin, I want a
  clear "N rows invalid — fix and re-upload" message with the offending rows
  highlighted, so that I am not left guessing whether my file is fixable or the
  job crashed.* A `failed` job with `failure_reason = validation_rejected` keeps
  the validation table and shows the distinct *validation_rejected* message;
  the admin edits the CSV and re-uploads (§4.2 step 7, §4.8).
- **US-6 — Tell a crash from a fixable file.** *As an admin, I want a distinct
  message when the job crashed (bad ZIP, virus, lock lost), so that I do not
  waste time re-uploading a file that was never the problem.* A `failed` job
  with `failure_reason = error` shows the crash status message alone (§4.2 step
  7, §4.8); `failed_lock_lost` specifically tells the admin their validated job
  is gone and they must re-upload (§4.8).
- **US-7 — Cancel a job I no longer want.** *As an admin, I want to release a
  validated-but-not-yet-imported job so that other admins are not blocked by my
  abandoned review.* *Cancel / Release lock* on `awaiting_approval` releases the
  lock and marks the job `canceled` (§4.5, §4.8).
- **US-8 — Stop a running import.** *As an admin, I want to stop an import that
  is already committing rows, so that I can halt a job I realize is wrong.*
  *Stop* sets the stop sentinel; the task finishes the current row and ends in
  `stopped` (§4.5, §4.8).
- **US-9 — Download the report.** *As an admin, I want to download an `.xlsx`
  of the validation/import results, so that I have an audit artifact.*
  *Download report* is enabled on terminal phases (`finished` / `stopped` /
  `canceled` / `failed`-with-table) and exports the Redis snapshot
  (§4.7, §4.8).
- **US-10 — See that someone else is importing.** *As an admin who has no
  in-flight job, I want to be told another admin's pipeline is running, so that
  I do not waste time uploading into a locked system.* The page shows the
  *import_is_running* banner when the global lock is held by another admin
  (§4.1 step 4 / GET branch, §4.8).
- **US-11 — Recover a stuck job (superuser).** *As a superuser, I want to
  release a forgotten `awaiting_approval` job that is blocking everyone, so that
  the import slot is freed even if the owner is gone.* Any superuser may
  force-cancel a stuck job (§4.5, §7).

### 2.5.2 Walkthrough (the happy path, end to end)

1. The admin opens the import page during maintenance mode. No job is running,
   so the page shows the upload form (§4.1 GET branch).
2. The admin picks a ZIP and submits. The POST stages the ZIP in Redis, sets
   `phase = validating`, enqueues `run_data_import_validation`, and returns the
   polling UI immediately — no validation table in the response (requirement 3,
   §4.1 step 11).
3. The page polls. The validation bar advances and validation rows append to
   the table one by one (§5b). *Start* is disabled, *Stop* and *Cancel* are
   available (§4.8).
4. Validation finishes with all rows valid → `phase = awaiting_approval`. The
   bar is pinned at 100 % (§5b.5), the table is complete, *Start* and *Download
   report* become available, *Cancel* remains available (§4.8). The admin can
   close the page here; the job waits with no TTL (§3.2).
5. The admin clicks *Start*. `DataImportStart` re-attaches the 6 h TTL to the
   lock, sets `phase = importing`, and dispatches `run_data_import` (§4.4). The
   page resets the bar to 0 (§5b.2/§5b.5) and switches to the import progress
   bar; the same table gains DB-key / history / Fedora columns as rows commit
   (§4.8).
6. The import completes → `phase = finished`, lock released (§4.3). The admin
   downloads the report (§4.7).

### 2.5.3 Actions available per phase

| Phase | Start | Stop | Cancel / Release lock | Download report | Re-upload |
|---|---|---|---|---|---|
| (no job) | — | — | — | — | upload form |
| `validating` | disabled | enabled | disabled | enabled (partial) | — |
| `awaiting_approval` | enabled | — | enabled | enabled | — |
| `importing` | disabled | enabled | rejected (use Stop) | enabled (partial) | — |
| `finished` | — | — | — | enabled | upload form |
| `stopped` | — | — | — | enabled | upload form |
| `canceled` | — | — | — | enabled | upload form |
| `failed` (`validation_rejected`) | — | — | — | enabled (table kept) | upload form |
| `failed` (`error` / `failed_lock_lost`) | — | — | — | enabled (table may be empty) | upload form |

> **Cancel is disabled during `validating` (UI).** *Stop* is the single control
> that halts a running validation. A Cancel during `validating` would only set
> the same stop sentinel as *Stop* (cancel ≡ stop), so exposing both was
> redundant and confusing — two active buttons that do the identical thing.
> *Cancel / Release lock* is therefore greyed out during `validating` and is only
> active in `awaiting_approval`, where no task is running and it performs the
> **direct** lock release. The backend `DataImportCancel` still accepts a
> `validating` job as a defensive no-op (≡ stop), but it is not reachable from the
> UI. This is enforced in `applyPhaseUi` in
> `webclient/templates/admin/import_data/import_data.html`.

### 2.5.4 Information available per phase

- **`validating`** — validation progress bar (`progress_data`, computed from
  the validation numerator/denominator pair; see §5b for the full bar
  mechanism), the validation table filling in row by row
  (`validation_results`), the status message (e.g. "Validating…"),
  `performed_action` + label. *Start* is disabled because validation has not
  finished.
- **`awaiting_approval`** — the complete validation table, `import_data_valid`
  result, row count, `performed_action` + label, the *waiting-for-approval*
  status message. The bar is pinned at 100 % (validation just finished; see
  §5b.5). No import columns yet.
- **`importing`** — the import progress bar (`progress_data`, reset to 0 on
  entry from `awaiting_approval`; see §5b.2/§5b.5), and the table extended with
  the DB primary key, history, and Fedora columns per row as they commit
  (`primary_keys`, `serialized_results`, `history_record_result`,
  `fedora_update_result`), plus the file table (`serialized_results_files`).
- **`finished` / `stopped` / `canceled`** — the final status message, the final
  row results, and the report available for download.
- **`failed`** — the `failure_reason` discriminator drives what is shown:
  `validation_rejected` → the validation table (which rows to fix) + the
  *validation_rejected* message; `error` → the crash status message alone;
  `failed_lock_lost` → the explicit "your validated job is gone, re-upload"
  state (§4.8).
- **Another admin's pipeline running (no own job)** — the *import_is_running*
  banner; no upload is accepted until that pipeline ends or is canceled
  (§4.1 step 4).

## 3. Proposed architecture

### 3.1 Job lifecycle (state machine)

Introduce an explicit per-job phase key so the page, the start view, and the
tasks all agree on what stage a job is in:

```
import_data_phase_{job_id}  ∈  validating | awaiting_approval | importing | finished | stopped | canceled | failed
```

Transitions (lock state shown in brackets):

```
                       upload POST   [acquire lock]
                           │
                           ▼
                       validating        ← run_data_import_validation task  [lock held]
                           │ (error → failed, release lock; stop → stopped, release lock)
                           ▼  (lock STAYS held)
                   awaiting_approval      ← validation OK, user reviews table  [lock held]
                           │ (cancel → canceled, release lock; approve → importing)
                           ▼  [lock already held; DataImportStart refreshes TTL]
                       importing          ← run_data_import task (unchanged phases)  [lock held]
                           │ (release lock in run_data_import finally)
                           ▼
              finished | stopped | canceled | failed   [lock free]
```

`failed` carries a **failure reason** (`import_data_failure_reason_{job_id}` ∈
{`validation_rejected`, `error`}, §4.2 step 7): `validation_rejected` = some
rows failed validation (fixable, file parsed OK); `error` = the job crashed
(bad ZIP, virus, oversized, lock-lost, unexpected exception). Both are terminal
with the lock released, but the reason drives a distinct status message and a
different `failed` UI (§4.8) so the admin can tell a fixable file from a crash.

The global import lock is acquired when validation starts and held
**continuously** across `validating` → `awaiting_approval` → `importing`. It is
released only on a terminal outcome: validation failure, explicit
**Cancel/Release** by the user, lock-loss, or `run_data_import`'s `finally` on
completion. The `awaiting_approval` review window therefore still holds the
lock — by design (see §3.2).

Add a **per-user** "current job" pointer so the import page knows which job to
bind to when the admin who started it simply reopens the page (no `job_id` in
the URL):

```
import_data_current_job_{user_id}  =  job_id   (set on upload, cleared on terminal state)
```

"Is something running?" is a single lock check (`IMPORT_DATA_LOCK_KEY`): the
lock is held for the entire pipeline, so a held lock means an import pipeline is
in progress and no other upload can start. The per-job
`import_data_phase_{job_id}` key distinguishes *which* phase (validating vs
awaiting_approval vs importing) for the UI.

### 3.2 Lock strategy

**No implicit canceling (primary motivation for the refactor).** The import
must **not** stop if the user closes the browser, signs off, or is auto-signed
off. It stops only on an **explicit** Cancel, or when a save crashes with an
error. There is therefore **no browser heartbeat** and **no TTL on the lock
during `awaiting_approval`** — the lock is `persist()`ed (no expiry) on
validation success and survives until the user explicitly Starts or Cancels (or
until Redis itself restarts). The owner's page polling is for UI display only;
it does not refresh the lock and has no bearing on whether the job is alive.

**Recommendation: acquire the global import lock when validation starts and hold
it continuously across validation, the `awaiting_approval` review window, and
the import — releasing it only on a terminal outcome or an explicit
Cancel/Release by the user.** One token is reused across the whole pipeline;
`DataImportStart` does **not** re-acquire, it refreshes the TTL and reuses the
stored token.

**Rationale (the key correctness reason — stated once here, referenced in
§4.2/§9/§12).** Holding the lock across the whole pipeline serializes
validation+import as one unit, preventing the **stale-validation conflict
between two imports**: if the lock were released during `awaiting_approval`,
admin A validates file A (OK, awaiting approval, lock released); admin B
validates file B containing an ID that will collide with a record A is about to
create — B's validation succeeds because A has not committed yet. A then runs
the import and commits the conflicting record. B's already-validated file is now
stale, but B can still click *Start*; B's import then crashes on the conflict
(duplicate ID / unique violation / missing prerequisite). Holding the lock
across the whole pipeline means no second file can validate against a DB state
another pending import is about to change. The lock is already the existing
"one import at a time" primitive; reusing it for the whole pipeline adds no new
concurrency mechanism.

**Priority: data integrity over operational convenience.** The whole point of
holding the lock is to prevent the conflict above; that correctness guarantee is
more important than the inconvenience of a held lock. The only mitigation is an
explicit **Cancel/Release** action (§4.5): the admin (or any superuser, for a
stuck job — see §7) is responsible for releasing a forgotten job. This does not
weaken the guarantee — it never expires the lock on its own. The concern that the
lock could be held indefinitely is accepted as the price of the no-implicit-
cancel model: a forgotten `awaiting_approval` job blocks other imports until
someone explicitly Cancels it. There is no automatic expiry and no UI action
that shortens this — by design.

**Guarantee scope — import-vs-import only, not a total guarantee.** The lock
serializes the import pipeline against *other import pipelines*. It does **not**
serialize against ordinary application writes: the lock is held by the import
flow alone, and normal app traffic (non-import record creation through the rest
of the app) is unaware of it and never blocks on it. During the
`awaiting_approval` window, regular app traffic can create a record whose ID
collides with one a pending validated import is about to commit — the
stale-validation conflict described above can therefore **reappear from a
non-import source**, and the import will still crash on it at `run_data_import`
time (duplicate ID / unique violation). The lock's guarantee is explicitly
scoped to import-vs-import; it is not a total guarantee that the validated state
will still hold at import time. Two mitigations keep this acceptable: (a) the
import is run only while maintenance mode is on, which sharply limits normal app
traffic during the review window; (b) `run_data_import` already catches
commit-time conflicts per row and records them in the per-row results, so a
collision surfaces as a per-row failure in the report rather than a silent
corruption. State this scope explicitly so the lock is not read as a total
guarantee.

**TTL strategy.** Two regimes, switched at the validation-success boundary:

- `IMPORT_DATA_RUNNING_TTL_SECONDS = 6 * 60 * 60` (6 h, `tasks.py:72`) — used
  for the lock while `validating` and `importing`, since those phases can run
  long. The validation task and `run_data_import` refresh the lock with this TTL
  once per row (mirroring the import task's per-record refresh at
  `tasks.py:783`; §4.2 step 6) so a long-running phase does not silently drop
  the lock.
- **No TTL during `awaiting_approval`.** On validation success the validation
  task **persists** the lock **and all per-job data keys** (removes any expiry),
  so a slow reviewer does not find the job gone when they finally click *Start*.
  The lock and data stay alive until explicit action or Redis restart.
  `DataImportStart` (§4.4) re-attaches the 6 h TTL via
  `refresh_import_lock(..., IMPORT_DATA_RUNNING_TTL_SECONDS)` before dispatching
  `run_data_import`.

**New lock primitive — `persist_import_lock` (token-guarded).** Today
`RedisConnector` exposes only `acquire_import_lock` / `refresh_import_lock` /
`release_import_lock` (`connectors.py:81-113`), each a token-checked Lua script;
there is **no** way to remove the lock's TTL while verifying ownership —
`refresh_import_lock` only *sets* a TTL. A bare `redis.persist(IMPORT_DATA_LOCK_KEY)`
on the raw client would work but is **not token-guarded** (it removes the TTL of
whatever holds the key, without checking this task still owns it), breaking the
symmetry every other lock mutation maintains. Add a matching classmethod:

```python
_PERSIST_LOCK_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('persist', KEYS[1])
else
    return 0
end
"""

@classmethod
def persist_import_lock(cls, connection: redis.Redis, token: str) -> bool:
    """Odstraní expiraci importního locku pouze tehdy, pokud ho stále vlastní zadaný token."""
    return bool(connection.eval(cls._PERSIST_LOCK_SCRIPT, 1, cls.IMPORT_DATA_LOCK_KEY, token))
```

The validation task calls `persist_import_lock(redis, lock_token)` on the success
path (§4.2 step 7/8). The **per-job data keys** (not the lock) have no token, so the
task persists them with the raw client — `redis.persist(key)` for each — batched in
a single Redis **pipeline** (the same pipeline style used for the chunk SETs, §3.3)
to avoid N round-trips.

Token lifecycle:

- Upload POST generates `lock_token` and `acquire_import_lock(...,
  IMPORT_DATA_RUNNING_TTL_SECONDS)`; the token is stored in
  `import_data_lock_token_{job_id}` and passed to
  `run_data_import_validation`, which refreshes it with the **6 h** TTL during
  validation.
- On validation **failure**/stop: the validation task releases the lock and
  expires the per-job data keys to 6 h (report retention — §4.2 finally).
- On validation **success**: the lock stays held (token unchanged); the task
  `persist_import_lock(redis, lock_token)`s the lock and (raw-client, pipelined)
  persists all per-job data keys (no TTL) and ends. Nothing
  refreshes the lock during `awaiting_approval` — it survives on its own.
- `DataImportStart` reads `import_data_lock_token_{job_id}`, calls
  `refresh_import_lock(..., IMPORT_DATA_RUNNING_TTL_SECONDS)` to re-attach the
  **6 h** TTL (the lock had no TTL during review), sets `phase = importing`,
  and dispatches `run_data_import(job_id, user_id, lock_token)`. It does **not**
  acquire a new lock. `refresh_import_lock` returns `False` only on an explicit
  release (force-cancel by a superuser) or Redis loss — **not** on TTL expiry,
  because there is no TTL to expire during review.
- `run_data_import` refreshes the token (6 h TTL) throughout and releases it in
  its existing `finally` (`tasks.py:1678`).
- **Cancel/Release** (`DataImportCancel`, §4.5): `release_import_lock(...)` with
  the stored token, set `phase = canceled`, **`expire()` the per-job data keys
  to `IMPORT_DATA_EXPIRATION_SECONDS` (6 h)** — the keys had no TTL during
  review, so re-attaching a 6 h TTL both prevents them from persisting
  indefinitely **and** keeps the report downloadable on a `canceled` job (§4.7,
  §2.5.3), matching the `stopped`/`failed` retention paths — clear the per-user
  pointer. "Once the lock is released, the import is canceled."

`awaiting_approval` abandonment: if the owner closes the page, signs off, or is
auto-signed off, **nothing happens to the job** — the lock has no TTL, so it
stays held and the job stays startable. The job blocks other imports until the
owner (or any superuser, §7) explicitly Cancels it. This is the deliberate
operational consequence of the no-implicit-cancel model: the import is not tied
to any browser session.

### 3.3 File staging

The Celery worker cannot see the in-memory `request.FILES` object, so the POST
must hand the uploaded ZIP to the validation task by reference, not by value.
Celery is configured with `CELERY_ACCEPT_CONTENT = ["json"]`
(`webclient/settings/base.py:646`), so the raw bytes cannot be a task argument
anyway — a reference (the `job_id`) is the correct shape.

**Recommendation: stage the uploaded (compressed) ZIP in Redis, chunked**
(stated once here, referenced in §8/§9). Concretely:

- In the POST, read `file_bytes = data_file.read()` (the compressed ZIP), split
  it into chunks of `IMPORT_DATA_REDIS_CHUNK_SIZE` (64 MiB; a constant in
  `webclient/core/admin_sites.py` next to `IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE`, see
  §11), and `SET` each chunk under `import_data_file_{job_id}_{i}`
  (i = 0..N-1) with `ex=IMPORT_DATA_RUNNING_TTL_SECONDS`, using a Redis pipeline
  for the SETs. Store the chunk count in `import_data_file_chunks_{job_id}`.
- The validation task reads `N = import_data_file_chunks_{job_id}`,
  pipeline-`GET`s `import_data_file_{job_id}_{0..N-1}`, concatenates them in
  order, and wraps the result as `io.BytesIO(blob)` for the antivirus check and
  `zipfile.ZipFile(...)`.
- The task deletes every `import_data_file_{job_id}_{i}` key plus the count key
  in its `finally` block — i.e. **at the end of the validation task, before the
  job enters `awaiting_approval`**. The chunks are **not** held through the
  review window or the import phase. The per-key `ex=` TTL is only the backstop
  for the case where the worker dies before reaching `finally`.

**Why this fits the existing app architecture (the deciding reason):**

- **Redis is already the web↔worker data bus**, and the import flow is the
  canonical example: `admin_sites.py:491` stores per-record JSON in Redis and
  passes only `job_id` to `tasks.run_data_import.delay(...)`. Staging the ZIP
  under `_{job_id}` keys and passing only `job_id` to the validation task is the
  same pattern, not a new one.
- **The app is disk-less for application data.** `Soubor` has no `FileField` —
  binaries live in Fedora; `MEDIA_ROOT` is defined but unused at runtime.
  Uploads stream through memory to Fedora (`core/views.py:824` → `BytesIO` →
  `FedoraRepositoryConnector.save_binary_file`). A tempfile-based staging
  directory would be the *new* mechanism — it would need a new
  `CustomAdminSettings` path, a writable shared volume between `web` and
  `celery_worker`, and a janitor for crashed-worker orphans. Redis staging
  reuses an already-shared, already-writable store with built-in TTL cleanup, so
  it adds no new setting and no new disk dependency.
- **Redis is already a shared service** on `prod-net`, reachable from both
  `web` and `celery_worker` (`docker-compose.yml`), so no new deployment
  topology is required.

**Why chunk the *compressed* bytes (not the uncompressed CSVs):**

- The import ZIP contains **only CSVs** (the binary Soubor files referenced by
  records live on `/vol/data-migrace`, not in the ZIP). CSV is text and
  compresses ~3-5x, so a ZIP at the existing
  `IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE = 1024 MB` cap is ~200-330 MB compressed.
  Chunking the compressed bytes therefore keeps total Redis RAM at ~250 MB for a
  maximum-size job — not the ~1 GB it would be if the *uncompressed* CSVs were
  chunked.
- Each chunk is small (64 MiB) → each `SET`/`GET` blocks the single-threaded
  Redis instance for only the chunk transfer time (tens of ms), not the whole
  blob, so other keys (sessions, caches, the import lock itself, Celery results)
  are not stalled behind one big transfer. Each value also stays far under the
  Redis 7+ `proto-max-bulk-len` default of 512 MiB with ample headroom, so
  chunking gives a safety margin if the uncompressed size limit is ever raised.
- Chunks are arbitrary byte ranges of the compressed ZIP → **no CSV row-boundary
  splitting problem** (a chunk of *uncompressed* CSV can split a row mid-field
  and would require carry-over logic). The worker simply reassembles the
  compressed blob in order and lets `zipfile` decompress.

**No new compressed-size cap is imposed.** A hard limit on the *compressed*
upload size is not a customer requirement and may be rejected; chunking makes
arbitrary compressed sizes work, bounded only by Redis RAM. The existing,
customer-accepted `IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE = 1024 MB` cap remains the
guardrail on total data volume, and via the ~3-5x compression ratio it
implicitly bounds the compressed bytes (and thus Redis RAM) to ~250 MB for a
maximum-size job — document this relationship (§8) so a future raise of the
uncompressed limit is reconsidered against Redis staging RAM.

**The ZIP is needed only during validation (stated once here, referenced in
§4.2 step 8).** Validation parses the CSVs into the per-record JSON keys
`import_data_{job_id}_record_{record_id}`, and the import task `run_data_import`
consumes *those* keys from Redis (`cron/tasks.py:802`) — it never reads the
uploaded ZIP. The binary Soubor files that records reference are read by the
import task from the operator-staged `/vol/data-migrace` volume
(`cron/tasks.py:1396`). So deleting all chunk keys at the end of validation is
safe and is the right moment to release the Redis memory.

**Caveat — persistence bloat.** If AOF/RDB is on, the chunks are written to the
persistence file and replayed on restart. Acceptable for an infrequent admin
upload; monitor RDB/AOF size. This is a new category of Redis value for the app
(today every Redis value is a small string/JSON/list/hash; nothing is a multi-MB
blob), but the chunks are bounded by `IMPORT_DATA_REDIS_CHUNK_SIZE` and are
short-lived (deleted at end of validation).

**Memory ceilings — three of them.** The ~250 MB figure above is only the
**Redis/reassembly** ceiling (the compressed blob in Redis RAM and the §4.2
step-2 reassembly peak). It is **not** the binding memory constraint. There are
two larger ceilings, analyzed in §8: the **web-worker upload peak** (~250-500 MB
transient, from `data_file.read()`), and — the real high-water mark — the
**validation worker peak** (several GB: object-dtype DataFrames + `to_dict`
copies + the accumulating `records` list). The present section sizes only the
compressed staging side; see §8 for the other two.

### 3.4 Two-task model (recommended over a single polling task)

Two tasks, mirroring the existing `run_data_import` style:

- **`run_data_import_validation(job_id, user_id, lock_token,
  performed_action)`** — new `@shared_task`. Owns the validation phase; refreshes
  the lock during validation. On success it leaves the lock held (for the
  `awaiting_approval` window); on failure/stop it releases the lock. The staged
  ZIP is reassembled from the `import_data_file_{job_id}_{i}` chunks (§3.3), so
  no file path or bytes are passed as task arguments — only the `job_id`
  reference, matching the existing `run_data_import(job_id, user_id, lock_token)`
  shape.
- **`run_data_import(job_id, user_id, lock_token)`** — existing task, essentially
  unchanged; still owns the import/history/Fedora/file phases and still releases
  the lock in its `finally` (`tasks.py:1678`).

`DataImportStart` **does not acquire a new lock** — it reuses the stored
`import_data_lock_token_{job_id}`, refreshes the TTL, and dispatches
`run_data_import`. The lock is thus held continuously from validation start
through import completion (or Cancel).

Rationale for two tasks over one task that polls an "approval" flag: a single
task blocked on a user-approval poll would occupy a Celery worker for the whole
review window (potentially hours). Two tasks free the worker between phases.

## 4. Component-by-component changes

### 4.1 `AmcrCustomAdminSite.import_data` (`webclient/core/admin_sites.py`)

The POST handler becomes a fast accept-and-enqueue. It preserves **both**
invariants of today's `admin_sites.py:369-370` gate (the POST branch is reached
only when maintenance is in progress **and** no import is running):

- **Invariant A — maintenance:** reject uploads outside maintenance mode.
- **Invariant B — no concurrent pipeline:** reject new uploads while *any*
  import pipeline is running (the own user's in-flight job, or another admin's
  lock-holding pipeline).

These are enforced in steps 2–4 below, before any work is accepted — with one
caveat: the *own-user* half of Invariant B (step 3) is advisory and not atomic,
while the *global* half (step 4 + the atomic lock acquire at step 7) is the
actual guarantee. See step 3 for the precise scope.

1. `if not request.user.is_superuser: raise PermissionDenied` (unchanged).
2. **Maintenance gate (Invariant A).** If `not is_maintenance_in_progress()`:
   render the page **without accepting the upload** — return early, do not fall
   through. The template's `{% if not maintenance %}` branch already shows the
   existing *not_maintenance* message, so this is a plain
   `TemplateResponse(...)` with the form and `maintenance=False` in context —
   exactly the current behavior. (Equivalently, return a 403 with the
   *not_maintenance* message as `DataImportStart` does; keep the page-render
   form to match today's UX.)
3. **Already-active-job gate (Invariant B, own job) — advisory, not atomic.**
   If the current user already has a non-terminal job
   (`import_data_current_job_{user_id}` points at a job whose
   `import_data_phase_{job_id}` is `validating`, `awaiting_approval`, or
   `importing`): render the page bound to **that** job **without accepting a new
   upload** — return early, do not fall through. The user returns to their
   in-flight job and can finish, start, or cancel it (requirement 2). This gate
   is per-user and does **not** block other admins.

   **This gate is a check-then-act and is NOT a hard invariant** — it is
   advisory UX, not a serialization guarantee. Reading
   `import_data_current_job_{user_id}` then its phase is two separate Redis
   calls with no atomicity between them, and the pointer is set only later in
   step 9; two near-simultaneous uploads from the same admin (e.g. two browser
   tabs) could both pass step 3 before either sets the pointer, so both would
   proceed to chunk-staging and dispatch. This is **benign by design**: the
   real serialization is the global lock acquire at step 7
   (`acquire_import_lock(..., NX)`), which is atomic — at most one of the two
   racing uploads wins the lock, the other falls back to the
   *import_is_running* page (step 7's TOCTOU branch). The loser's already-staged
   chunk keys are cleaned up by the dispatch-failure path (step 10) / the 6 h
   `ex=` TTL. Two further narrowing factors make the race window tiny in
   practice: (a) imports run only while maintenance mode is on (step 2), so the
   only actors are admins, not the general public; (b) the same admin double-
   submitting two tabs is the sole realistic trigger. Document this so future
   reviewers do not read step 3 as the guarantee — **step 7 is the guarantee**;
   step 3 only avoids surprises in the common single-tab case.
4. **Global-lock-busy gate (Invariant B, another admin's pipeline).** If
   `RedisConnector.get(IMPORT_DATA_LOCK_KEY)` is set (another admin's pipeline
   — validating, reviewing, or importing — is holding the lock): render the
   page with the existing *import_is_running* message **without accepting the
   upload** — return early, do not fall through to step 5. The lock cannot be
   acquired anyway; the user can retry once that pipeline finishes or is
   canceled.
5. Validate `ImportDataAdminForm`. On invalid, re-render the form page (no job).
6. Generate `job_id` (existing 20-char scheme) and `lock_token =
   secrets.token_hex(16)`.
7. `acquire_import_lock(redis, lock_token, IMPORT_DATA_RUNNING_TTL_SECONDS)`.
   If acquisition fails (TOCTOU race with another upload), fall back to rendering
   the *import_is_running* page.
 8. **Stage the ZIP in Redis, chunked (§3.3).** Read `file_bytes = data_file.read()`
    (the compressed ZIP), split into chunks of `IMPORT_DATA_REDIS_CHUNK_SIZE`
    (64 MiB, §11), and pipeline-`SET` each chunk to
    `import_data_file_{job_id}_{i}` with `ex=IMPORT_DATA_RUNNING_TTL_SECONDS`.
   Store the chunk count in `import_data_file_chunks_{job_id}`. No compressed-
   size precheck is imposed (chunking handles any size; the existing
   `IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE` cap remains the volume guardrail).
   **Note the web-worker memory peak:** `data_file.read()` pulls the whole
   compressed upload into the web process's RAM at once, and the chunk list
   holds a second reference during the SET loop — a transient ~250-500 MB
   spike per upload. This is analyzed in §8 (uWSGI `processes = 15`, no
   per-worker memory cap; the global lock serializes uploads so only one
   worker spikes). **Record this characteristic in the `import_data` view
   docstring** so a future maintainer does not bypass it unnoticed.
9. Set Redis keys with `ex=IMPORT_DATA_RUNNING_TTL_SECONDS`:
   - `import_data_current_job_{user_id}` = `job_id`
   - `import_data_phase_{job_id}` = `"validating"`
    - `import_data_status_message_{job_id}` =
      `_("cron.tasks.run_data_import.validating")` (new translation string, see
      §11)
   - `import_performed_action_{job_id}` = `performed_action`
   - `import_data_user_{job_id}` = `request.user.id` (for ownership checks, §7)
   - `import_data_lock_token_{job_id}` = `lock_token` (reused by
     `DataImportStart` and `DataImportCancel`; see §3.2)
   - `import_data_file_{job_id}_{i}` = compressed ZIP chunk *i* (set in step 8)
   - `import_data_file_chunks_{job_id}` = chunk count *N* (set in step 8)
   - `import_data_validation_total_{job_id}` = (unknown yet; set by task)
   - `import_data_validation_progress_{job_id}` = 0
   - `import_data_validation_results_{job_id}` = `[]`
   - `import_data_valid_{job_id}` = unset / `"0"`
   - `import_data_count_{job_id}` = unset
10. `tasks.run_data_import_validation.delay(job_id, request.user.id, lock_token,
   performed_action)`. On dispatch failure, release the lock and delete every
   `import_data_file_{job_id}_{i}` key plus `import_data_file_chunks_{job_id}`
   (read *N* first, or use a `SCAN`/`delete` loop), then re-render with an error.
11. Return `TemplateResponse` for the **polling UI** with only non-data context:
   `job_id`, `url` (`data-import-progress`), `url_stop`, `url_start`,
   `performed_action` + label, `import_directory_configured`. **No
   `validation_results`, no `records_count`, no `invalid_records` in context** —
   the JS pulls all of that from the progress endpoint.

The GET branch (no POST, or maintenance/running) reads
`import_data_current_job_{user_id}` for the requesting user and, if it points at
a non-terminal job, renders the polling UI bound to that `job_id` (so the admin
who started an import sees its progress on reopen, including the
`awaiting_approval` review state). If the user has no in-flight job but the
global lock is held, render the *import_is_running* page; otherwise render the
upload form.

### 4.2 New task `run_data_import_validation` (`webclient/cron/tasks.py`)

Move the body of the current POST `try:` block here, restructured:

1. `refresh_import_lock(...)`; on failure set phase `failed`, status
   `failed_lock_lost`, set `import_data_stop`, and return (mirror
   `run_data_import`'s `ImportLockLostError` pattern).
2. Reassemble the staged ZIP from Redis: read
   `N = int(redis.get(f"import_data_file_chunks_{job_id}"))`, pipeline-`GET`
   `import_data_file_{job_id}_{0..N-1}`, concatenate the chunks in order into
   `blob` (delete all chunk keys plus the count key in `finally`); wrap as
   `io.BytesIO(blob)`. Free each chunk from worker memory as soon as it is
   appended, to keep the **reassembly** peak at roughly one chunk + the
   reassembled blob. Note this is **not** the worker's high-water mark — the
   validation pass that follows is far larger; see the §8 validation worker
   peak-memory analysis.
3. Antivirus check (`Soubor.check_antivirus`). `VIRUS_FOUND` → phase `failed`,
   status `virus_found`, return.
4. Open the ZIP. `BadZipFile` / `ImportDataUnsupportedFilesError` /
   `ImportDataUnsupportedFileError` / `ImportDataEmptyError` /
   `ImportDataMissingFileError` / oversized → phase `failed`, status message
   from the existing translation strings, return. (These messages already
   exist; reuse them.)
5. Set `import_data_validation_total_{job_id}` to total row count (sum over
   files) once the sheets are read.
6. For each CSV row (the existing per-row `try/except`):

   - Call `LookupImportField.set_records(records)` once before the loop (as
     today) and `clear_records()`/`clear_cache()` in `finally`.
   - Run `mapper.map`, `check_required_fields`, `import_validation`,
     `create_records`, push `import_data_{job_id}_record_{record_id}` (all as
     today).
   - Build `ImportDataValidationResult` exactly as today.
   - Increment `import_data_validation_progress_{job_id}` per row.
   - `rpush` each row's `ImportDataValidationResult` to
     `import_data_validation_details_{job_id}` and its `item_order` to
     `import_data_validation_ids_{job_id}` (the live incremental path the UI
      reads — see §5). Every `VALIDATION_REDIS_UPDATE_INTERVAL` rows (a module-
      level constant in `webclient/cron/tasks.py`, mirroring the existing
      `HISTORY_REDIS_UPDATE_INTERVAL = 10` at `tasks.py:1083` which checkpoints
      the history JSON every 10 records) also dump the accumulated list to
      `import_data_validation_results_{job_id}` as a JSON checkpoint snapshot
      (this is the authoritative key `DataImportProgressReportView` reads; the
      final dump at end of validation, step 7, makes it complete). The lists are
      the UI path; the JSON key is the report snapshot.
    - Poll `import_data_stop_{job_id}`; if set, phase `stopped`, status
      `stopped_by_user`, return.
    - `refresh_import_lock(...)` **once per row**, at the top of the row loop —
      mirroring the import task, which calls `refresh_import_lock()` once per
      record at the top of its loop (`tasks.py:783`). This is the same cadence
      the import phase uses; no separate "every N rows" cadence is introduced.

7. On success: set `import_data_count_{job_id}`, `import_data_valid_{job_id}`
   (`"1"` if no invalid, else `"0"`), final
   `import_data_validation_results_{job_id}`, `import_data_primary_keys_{job_id}
   = {}`, `import_data_files_{job_id} = []`, `import_data_history_record_result_
   {job_id} = {}`, `import_fedora_result_{job_id} = {}`,
    `import_data_progress_{job_id} = 0`, and
    `import_data_phase_{job_id} = "awaiting_approval"` (or `"failed"` if
    `invalid_records`). Status message: a new translation string
    `cron.tasks.run_data_import.validation_done` (see §11). **Do not release
   the lock on success** — the lock stays held across the `awaiting_approval`
   review window so no other import can validate against a DB state this job is
   about to change (§3.2 rationale). The task ends here; nothing refreshes the
   lock during `awaiting_approval` — it survives on its own (no TTL, `persist()`ed
   in step 8) until `DataImportStart` re-attaches the 6 h TTL and dispatches
   `run_data_import`.

   **Distinguish validation-rejected from error-failed (do not collapse the
   two).** Routing `invalid_records` to a terminal `failed` phase (lock
   released) is a defensible simplification — it avoids holding the lock on an
   un-importable file — but `failed` is also the phase for genuine crashes
   (bad ZIP, virus, oversized, lock-lost, unexpected exception). Collapsing
   "your file has fixable invalid rows" and "the job crashed" into one
   undifferentiated `failed` state breaks the admin's mental model. Keep
   `failed` as the single terminal phase (no new state-machine state), but
   carry a **failure reason** and a **distinct status message** so the UI can
   tell them apart:
   - Set `import_data_failure_reason_{job_id}` ∈
     {`"validation_rejected"`, `"error"`}. `"validation_rejected"` = the file
     parsed and was checked but some rows failed validation (fixable: the admin
     edits the CSV and re-uploads). `"error"` = the job could not even produce
     a validation table (bad ZIP, virus found, oversized, lock-lost, unexpected
     exception).
    - Status message: `"validation_rejected"` → a new
      `cron.tasks.run_data_import.validation_rejected` (e.g. "Validation
      rejected — N rows invalid; fix the flagged rows and re-upload"), distinct
      from the `"error"` path which keeps the existing crash status messages
      (`virus_found`, `bad_zip_file`, `zip_too_large`, `failed_lock_lost`, …).
      The two must never share a message string.
      **Translation-interpolation warning:** the message embeds a count ("N
      rows invalid"), so it is tempting to write it as an f-string — do **not**.
      Per project convention (§11, and the existing
      `cron.tasks.run_data_import.*` strings), translations must be built with
      `%`/`.format()` applied to the `_()` result, never with an f-string
      wrapping `_()`. Concretely, define the template with a placeholder and
      interpolate after translation, e.g.:
      ```python
      validation_rejected = _("Validation rejected — %d rows invalid; "
                              "fix the flagged rows and re-upload") % invalid_count
      ```
      or equivalently `_("...{}...").format(invalid_count)`. An f-string of the
      form `f"...{invalid_count}..."` (with or without `_()` inside it) is
      **not** acceptable: it bypasses the catalog and breaks
      `makemessages`/`compilemessages`.
   - The validation table (live lists / JSON snapshot) is kept for the
     `validation_rejected` reason — it is the actionable information (which rows
     to fix) — and the UI renders it on the `failed` phase when the reason is
     `validation_rejected` (§4.8). For the `"error"` reason the table may be
     empty/absent and the UI shows the crash message alone.
   This preserves the admin's mental model (today the sync flow shows the
   invalid-rows table and disables *Start*; the async flow shows the same table
   under a `failed`/`validation_rejected` reason with a clear "fix and
   re-upload" message) without adding a state-machine state.

8. `finally`: `LookupImportField.clear_records()`/`clear_cache()`; delete the
   staged ZIP chunk keys `import_data_file_{job_id}_{i}` (for i in 0..N-1, where
   *N* is read from `import_data_file_chunks_{job_id}`) plus the count key itself
   — free the Redis memory as soon as validation is done with the bytes, do not
   wait for the TTL. The ZIP is needed only during validation (§3.3): the import
   task consumes the parsed per-record JSON keys, not the ZIP, so deleting the
   chunk keys at the end of validation is safe and is the right moment to
   release the Redis memory. **Release the lock only on the
   `failed`/`stopped`/lock-lost paths** (validation failed or was stopped → no
   import will follow). On the success path, leave the lock held for
   `awaiting_approval` and `persist()` it (remove its TTL) so it survives the
   review window without any refresher (§3.2). On `failed`/`stopped`,
   additionally clear `import_data_current_job_{user_id}` and set
   `import_data_phase_{job_id}` to the terminal value. The lock must not be
   left held on a *failed/stopped* exit, and must not be released on a
   *successful* exit.

   **Validation-results data keys are NOT deleted on failure — they are kept for
   6 h, then auto-expire.** On the `failed`/`stopped`/lock-lost paths
   `run_data_import` never runs, so its `finally` cleanup
   (`tasks.py:1660-1677`, which `expire(...)`s every per-job data key to
   `IMPORT_DATA_EXPIRATION_SECONDS` = 6 h) never executes. The validation task's
   own `finally` must therefore mirror that cleanup: call
   `redis_connector.expire(key, IMPORT_DATA_EXPIRATION_SECONDS)` on the
   validation data keys — `import_data_validation_results_{job_id}`,
   `import_data_validation_progress_{job_id}`,
   `import_data_validation_total_{job_id}`,
   `import_data_invalid_records_{job_id}`,
   `import_data_status_message_{job_id}`, `import_data_count_{job_id}`,
   `import_data_valid_{job_id}`, the live lists
   `import_data_validation_ids_{job_id}` / `import_data_validation_details_{job_id}`,
   and every `import_data_{job_id}_record_{record_id}`
   — so they persist for 6 h after the validation task ends. This is deliberate:
   the user must be able to see *why* validation failed on the page (the page
   polls and renders `phase = failed` + `validation_results`) and to download
   the report (`DataImportProgressReportView` reads
   `import_data_validation_results_{job_id}`), neither of which needs the ZIP.
   Do **not** `delete()` these keys on failure — only `expire()` them. On the
   **success** path, `persist()` the lock **and all per-job data keys** (remove
   the `ex=` TTL) so they survive `awaiting_approval` no matter how long the
   reviewer takes (§3.2, §6); `DataImportStart` re-attaches the 6 h TTL to the
   lock before dispatching the import, and `run_data_import`'s `finally`
   re-expires the data keys to 6 h after the import completes.

Note: `mapper.create_records` is called during validation in the current code
(see `admin_sites.py:460`). That builds in-memory record objects used only for
`records += …`; it does not persist. Keep that behavior. The validation task
must not write to the DB.

**Read-only contract for mappers during validation (documented, not guarded).**
`import_validation` and `create_records` perform DB *reads*/lookups (via
`LookupImportField`) but must not persist anything during the validation phase.
This contract is enforced by documentation, not by runtime guards, in **two
places**:

- **A comment at the `create_records` call site inside the new
  `run_data_import_validation` task** (in `webclient/cron/tasks.py`), explicitly
  stating that `create_records` is called for **serialization only** and must
  remain **read-only** — it must not call `save()`/`delete()` or otherwise
  mutate the DB. This anchors the contract where the call happens, so a future
  maintainer reading the task sees it immediately.
- **A note in the base `ImportModelMapper` class docstring**
  (`webclient/core/import_data_mappers.py`) stating that during validation the
  mapper methods (`map`, `check_required_fields`, `import_validation`,
  `create_records`) are used **read-only** — `create_records` builds in-memory
  objects for serialization only and must not call `save()`/`delete()` or
  otherwise mutate the DB.

No `transaction.atomic`/rollback wrapper, `save()`-monkey-patch, or row-count
assertion is added — the contract is documented in the task comment and the
base-class docstring only.

**Runtime guards — considered and rejected.** The contract is enforced in
**tests** (§10), not by production runtime guards:

- **`transaction.atomic()` + rollback around the validation loop** is rejected
  because `atomic()` does not *prevent* writes (it only rolls them back), would
  hold a DB transaction open for the whole validation loop (minutes — an
  anti-pattern: connection tied up, PostgreSQL snapshot/vacuum pressure, lock
  contention), and is **leaky**: it rolls back neither Fedora writes (HTTP) nor
  `save()`-signal side effects (Redis, notifications), so a buggy mapper could
  still cause irreversible side effects. It also changes read isolation.
- **Monkey-patching `create_records` (or `save`/`delete`) to assert no writes**
  is rejected as fragile: it requires intercepting writes on every model the
  mappers touch, breaks under refactoring, and couples the task to mapper
  internals.
- The test-time guard in §10 (capture queries, assert no
  `INSERT`/`UPDATE`/`DELETE` during validation) gives real regression protection
  with **zero production runtime cost** and is the chosen mechanism for the
  DB-write side of the contract. **It guards DB writes only.** It does *not*
  see Fedora HTTP writes or `save()`-signal side effects (Redis, notifications),
  because those are not SQL — the same blind spot used above to reject
  `atomic()`. For that class of side effect, the contract is enforced by
  documentation (the two places above) **plus a targeted mock-based assertion**
  that the Fedora external-write entry points are not called during validation
  (§10) — `assert_not_called` is cheap and closes the gap the SQL-capture test
  leaves open. No automated guard covers *arbitrary* signal side effects beyond
  the Fedora entry points; that residual is accepted, since today's synchronous
  POST already calls `create_records` without persisting, so this guards a
  future regression, not a present bug.

### 4.3 `run_data_import` (`webclient/cron/tasks.py`) — minimal changes

- The initial `refresh_import_lock` works with the **reused** token
  `DataImportStart` passes in (read from `import_data_lock_token_{job_id}`,
  §4.4) — no change to that logic; the lock has been held continuously since
  validation started.
- Remove (or keep idempotent) the `record_count <= 0` early-fail path's
  assumptions; it still applies.
- In the terminal `finally`, additionally: clear
  `import_data_current_job_{user_id}` (read `import_data_user_{job_id}` for the
  suffix), delete any leftover staged ZIP chunk keys
  `import_data_file_{job_id}_{i}` plus `import_data_file_chunks_{job_id}` if any
  still exist (defensive — the validation task should already have deleted them
  once it finished parsing), set `import_data_phase_{job_id}` to `finished` /
  `failed` / `stopped` (matching `status`), and release the lock (already done
  at `tasks.py:1678`).
- The `import_data_valid_{job_id}` gate is enforced by `DataImportStart`
  before this task is dispatched, so the in-task check is just defensive.

### 4.4 `DataImportStart` (`webclient/core/views.py`)

This section reflects the **chosen** lock strategy from §3.2 (continuous lock
across validation → review → import; one reused token). It is not conditional.

- Keep the `is_superuser` and `is_maintenance_in_progress` gates.
- Verify `import_data_phase_{job_id} == "awaiting_approval"` and
  `import_data_valid_{job_id} == "1"`; else return 422 with the existing
  `invalid_records` message.
- Verify `import_data_user_{job_id} == request.user.id` (§7).
- **Reuse the stored token**: read `lock_token =
  import_data_lock_token_{job_id}`. Do **not** call `acquire_import_lock` —
  the lock has been held continuously since upload and is still owned by this
  token. **Re-attach the 6 h TTL** with `refresh_import_lock(redis,
  lock_token, IMPORT_DATA_RUNNING_TTL_SECONDS)` (the lock had **no TTL** during
  `awaiting_approval` — the validation task `persist()`ed it on success — so
  this is the moment the TTL comes back, before the long-running import
  begins). If refresh returns `False` the lock was lost (explicit force-cancel
  by a superuser, or Redis restarted): set
  `import_data_phase_{job_id} = "failed"`, status `failed_lock_lost`, clear the
  per-user pointer, and return 409 — the job is no longer startable. (This
  cannot happen due to TTL expiry during review, because there is no TTL to
  expire.)
- Set `import_data_phase_{job_id} = "importing"`.
- `tasks.run_data_import.delay(job_id, request.user.id, lock_token)`. On
  dispatch failure, do **not** release the lock (the job is still resumable):
  set phase back to `awaiting_approval` and return 500.
- Return `{"result": "ok"}`.

### 4.5 `DataImportStop` and `DataImportCancel` (`webclient/core/views.py`)

- **`DataImportStop`** is unchanged in mechanism: it sets
  `import_data_stop_{job_id}`. Both the validation task (§4.2 step 6) and
  `run_data_import` already poll this sentinel, so stop works during
  `validating` and `importing`. Add the §7 ownership check.
- **`DataImportCancel`** (new, POST, `core:data-import-cancel`) — the user's
  explicit "release the lock" action. For an `awaiting_approval` job: read
  `import_data_lock_token_{job_id}`, call `release_import_lock(redis,
  lock_token)` (this is what makes the lock available to other admins),
  set `import_data_phase_{job_id} = "canceled"`, set
  `import_data_status_message_{job_id}` to a new
  `cron.tasks.run_data_import.cancelled`, **`expire()` the per-job data keys to
  `IMPORT_DATA_EXPIRATION_SECONDS` (6 h)**
  (`import_data_validation_details_{job_id}`, the JSON snapshot, `primary_keys`,
  etc. — see §6) — the lock had no TTL during review, so re-attaching a 6 h TTL
  prevents these keys from persisting indefinitely while keeping the report
  downloadable on the `canceled` job (§4.7, §2.5.3); do **not** `delete()` them.
  Clear `import_data_current_job_{user_id}`,
  and return `{"result": "ok"}`. "Once the lock is released, the import is
  canceled." For a `validating` job, cancel is equivalent to stop (set the stop
  sentinel; the validation task releases the lock and expires the data keys in
  its `finally`) — **but this branch is disabled in the UI** (§2.5.3): during
  `validating` only *Stop* is offered, since a Cancel here does nothing *Stop*
  does not. The `validating` branch is kept in `DataImportCancel` as a defensive
  no-op but is not reachable from the page. Reject cancel for `importing` (use *Stop* instead — the
  import task owns the lock and must release it in its own `finally`) and for
  terminal phases. Wire `core:data-import-cancel` in
  `webclient/core/urls.py` alongside the existing import routes.
- **Superuser force-cancel of a stuck `awaiting_approval` job.** A forgotten
  job holds the lock with no TTL and blocks all other imports (§3.2). Any
  superuser (not just the owner — §7) may call `DataImportCancel` on such a
  job to release the lock and `expire()` its data keys to 6 h. This is the only recovery
  path for an abandoned review-window job.

### 4.6 `DataImportProgress` (`webclient/core/views.py`)

Extend the JSON response so the page can render everything from Redis:

- `phase`: read `import_data_phase_{job_id}` (one of the states in §3.1; map
  missing → `"unknown"`).
- `validation_results`: the live validation rows, read by `lrange` of
  `import_data_validation_details_{job_id}` (decoded as the list of
  `ImportDataValidationResult` dicts) — this is the incremental UI path (§5).
  (The report view `DataImportProgressReportView` still reads the
  `import_data_validation_results_{job_id}` JSON snapshot, §4.7.)
- `progress_data`: the single 0–100 integer driving the bar. During
  `phase == "validating"` it is computed from the validation numerator/
  denominator pair `import_data_validation_progress_{job_id}` /
  `import_data_validation_total_{job_id}`; during `importing`/terminal phases
  it is computed by the existing import `if/elif` ladder (unchanged). The full
  bar mechanism — including the `awaiting_approval` pin at 100 % and the
  reset to 0 on `validating → importing` — is specified in §5b. **No separate
  `validation_progress` field is added**: reusing `progress_data` keeps the
  template's `maxProgressData` logic unchanged except for the §5b.5 phase
  switch. (The §2.5/§4.8 references to "validation progress bar" are satisfied
  by `progress_data` while `phase == "validating"`.)
- `invalid_records`: derive from `import_data_valid_{job_id} == "0"` (and/or a
  stored `import_data_invalid_records_{job_id}` list).
- `failure_reason`: read `import_data_failure_reason_{job_id}` when
  `phase == "failed"` (one of `"validation_rejected"` / `"error"`, §4.2 step 7)
  so the template can branch the `failed` UI accordingly (§4.8). Absent for
  non-`failed` phases.
- `performed_action` / `performed_action_label`: read from
  `import_performed_action_{job_id}`.
- Keep the existing fields (`record_count`, `progress_data`,
  `finished_record_count`, `serialized_results`, `primary_keys`,
  `history_record_result`, `fedora_update_result`, `status`,
  `serialized_results_files`, `status_message`).
- **Do not fold validation into the import `IMPORT_PROGRESS_PHASE_*` ladder.**
  The validation bar is driven by a separate `if phase == "validating"`
  branch placed *above* the existing import `if/elif` ladder, gated on `phase`
  (§5b.4). This avoids renumbering the existing
  `IMPORT_PROGRESS_PHASE_FAILED`/`_DATA_DONE`/`_HISTORY_DONE`/`_FEDORA_DONE`/
  `_FINISHED` constants and the many import tests that assert on them (§5b.3).
- `status`: extend to derive from `phase` (`finished` / `stopped` / `failed` /
  `canceled` / `in_progress`), keeping the current `phase_progress >= FINISHED`
  and `stopped` logic.
- **The lock is not touched here.** Per §3.2 there is no heartbeat and no TTL
  during `awaiting_approval`; polling is for UI display only. `DataImportProgress`
  never calls `refresh_import_lock` or `release_import_lock`. The lock stays
  alive on its own (no TTL) until the user explicitly Starts or Cancels.

### 4.7 `DataImportProgressReportView` (`webclient/core/views.py`)

Unchanged in logic (it already reads everything from Redis). It reads the
`import_data_validation_results_{job_id}` **JSON snapshot** (not the live lists)
— which the validation task dumps at end of validation (§4.2 step 6/7) — so it
works for both a finished import and a finished/failed validation. Add the §7
ownership check. **The report is downloadable at any phase**, including while
`phase == "validating"` or `phase == "importing"` — this matches the existing
import-phase behavior, where the report is already downloadable mid-import.
Two consequences of allowing mid-run downloads:
- The mid-run report is a **partial snapshot**, not authoritative: it lags the
  live list by up to `VALIDATION_REDIS_UPDATE_INTERVAL` rows while
  `phase == "validating"` (§5). Surface the phase in the report (e.g. a
  "VALIDATION IN PROGRESS — partial" banner) so a mid-run report is never
  mistaken for the final one. Do **not** refuse the download.
- At a terminal phase the final snapshot has been dumped (§4.2 step 7) and the
  report is authoritative.

### 4.8 Template `admin/import_data/import_data.html`

Remove every Django-rendered data table and every `{% if validation_results %}`
branch that reads from context. The page becomes a thin shell that either
shows the upload form (no active job) or the polling UI (active/terminal job),
with all data rendered by JS from `DataImportProgress`:

- Server-side context reduces to: `job_id` (or none), `url`, `url_start`,
  `url_stop`, `url_cancel`, `performed_action_label`,
  `import_directory_configured`, `maintenance`, and a `running_elsewhere` flag
  (global lock held by another admin). The `csrf` token is still needed for the
  start/cancel POSTs.
- The `<table id="result_list">` is rendered empty (header only); JS appends
  validation rows incrementally from `validation_results` by index —
  `start_index = table.rows.length - 1; for (i = start_index; i <
  data.validation_results.length; i++)` — the same pattern the file table uses
  for `serialized_results_files`. Each row shows order, file, import PK,
  validation result. Once the job moves to `importing`, the same JS continues
  to update columns 4/6/7/8 from `primary_keys`, `serialized_results`,
  `history_record_result`, `fedora_update_result` as it already does.
- The `<table id="result_list_files">` rows are still built by JS from
  `serialized_results_files` (as today).
- The progress bar reuses the single existing `progressBarData` element and
  switches its source on `phase` (full mechanism in §5b, including the
  `awaiting_approval` pin at 100 % and the reset to 0 on
  `validating → importing`):
  - `validating` → drive the bar from `progress_data` (computed from the
    validation numerator/denominator pair, §5b.4), disable *Start*, enable
    *Stop* (stop sentinel aborts validation; task releases lock), enable
    *Download report* (partial — §4.7).
  - `awaiting_approval` → show the validation table, pin the bar at 100 %
    (§5b.5), enable *Start* (this phase
    is reached only for all-valid jobs — `import_data_valid_{job_id} == "1"`;
    jobs with invalid records route to `failed` with the lock auto-released,
    §4.2 step 7 — so the empty-`invalid_records` check on *Start* is kept only
    defensively), enable *Cancel/Release lock* (see below), enable *Download
    report*. **Keep polling** while this phase is shown — for UI display only;
    the poll does not touch the lock (§4.6), and the lock stays alive on its own
    (no TTL) whether or not the page is open.
  - `importing` → reset the bar to 0 once (§5b.5), then show the import bar
    from `progress_data` (existing import `if/elif` ladder, unchanged),
    disable *Start*, enable *Stop*, enable *Download report* (partial — §4.7).
  - `finished` / `stopped` / `canceled` / `failed` → enable *Download report*,
    disable *Start*/*Stop*/*Cancel*. **Within `failed`, branch on
    `failure_reason`** (§4.2 step 7): if `failure_reason === "validation_rejected"`,
    keep rendering the validation table (the live `validation_results` rows are
    still in Redis and the JS already drew them during `validating`) and show
    the distinct *validation_rejected* status message ("Validation rejected — N
    rows invalid; fix the flagged rows and re-upload") — this is the admin's
    actionable view of which rows to fix, matching today's sync behavior of
    showing the invalid-rows table. If `failure_reason === "error"`, show the
    crash status message alone (the table may be empty/absent). The two reasons
    must never share a status string, so the admin is never left guessing
    whether their file is fixable or the job crashed.
- **`failed_lock_lost` UI is load-bearing — render it explicitly, not as a
  generic error.** Several paths route into `failed` with the
  `failed_lock_lost` status (§4.1 step 7's TOCTOU branch, §4.4's
  `refresh_import_lock` returning `False` on Start, §4.6/§3.2 lock-loss during
  review). Under the no-TTL model this means the lock was released by an
  explicit superuser force-cancel or lost to a Redis restart — **not** a TTL
  expiry — so the wording must match: a clear, specific state such as
  *"Your validated job is no longer startable — the import lock was released or
  Redis was restarted. Please re-upload the file."*, with the *Start* button
  hidden/disabled and the upload form re-shown (or a prominent *Re-upload*
  action). Do **not** render this as a bare generic error or a stale
  `awaiting_approval` table — the admin must understand their validated job is
  gone and that re-uploading is the only path forward. The `status_message`
  string for `failed_lock_lost` must be distinct from both the
  `validation_rejected` and the other `error`/crash strings (§11).
- **Cancel / Release lock button (`url_cancel` → `DataImportCancel` POST, see
  §4.5).** Visible for `validating` and `awaiting_approval`. Label it clearly as
  releasing the import lock (e.g. "Cancel and release lock"). For
  `awaiting_approval` it releases the lock and marks the job `canceled` — this
  is the user's explicit "I'm not running this import; free the slot" action,
  and it is the only way besides *Start* to release a held review-window lock.
  For `validating` it sets the stop sentinel (the task releases the lock in its
  `finally`).
- On page load, if `job_id` is present, start polling immediately (the existing
  `process()` loop). The existing 6 h / `MAX_TICKS` polling guard and
  `MAX_CONSECUTIVE_FAILURES` logic stay. Treat `phase` terminal as the poll
  stop condition (alongside the existing `status === "finished"|"stopped"`).

## 5. Validation results: incremental rendering

**Chosen strategy: append via Redis lists (scalable).** This mirrors the
existing import-phase pattern (`import_data_progress_ids`/`_details`, which
`run_data_import` `rpush`es to and `DataImportProgress` `lrange`s) and the file
table's incremental append (`serialized_results_files`).

- The validation task `rpush`es each row's validation result to
  `import_data_validation_details_{job_id}` (and its `item_order` to
  `import_data_validation_ids_{job_id}`) as it is produced — an O(1) append per
  row, instead of rewriting a growing JSON blob every row.
- `DataImportProgress` `lrange`s `import_data_validation_details_{job_id}` into
  the `validation_results` response array. The JS renders rows by index,
  appending only the ones it has not yet drawn (the same pattern the file table
  uses: `start_index = table.rows.length - 1; for (i = start_index; i <
  data.validation_results.length; i++)`). This keeps the rendering incremental
  and avoids re-drawing the whole table each poll.
- `import_data_validation_results_{job_id}` (the existing JSON-list key) is kept
  as the **authoritative snapshot for the report**: the validation task dumps
  the accumulated list to it at the end of validation (and optionally every
  `VALIDATION_REDIS_UPDATE_INTERVAL` rows as a checkpoint). It is *not* the live
  UI path — the lists are. This keeps `DataImportProgressReportView` unchanged
  (it already reads that exact key).
- **Two sources of truth — the mid-run report lags the UI.** Because the live
  list (`import_data_validation_details_{job_id}`) is `rpush`ed every row while
  the JSON snapshot (`import_data_validation_results_{job_id}`) is only
  checkpointed every `VALIDATION_REDIS_UPDATE_INTERVAL` rows, **a report
  downloaded mid-validation can lag the UI by up to
  `VALIDATION_REDIS_UPDATE_INTERVAL` rows** (the snapshot is stale between
  checkpoints). This is acceptable — reports are for terminal states
  (`finished` / `stopped` / `failed`), where the task has dumped the final
  complete snapshot in step 7 and the two sources agree. But state it explicitly
  so nobody treats a **mid-run** report as authoritative: the live list is the
  source of truth while `phase == "validating"`; the JSON snapshot is
  authoritative only at terminal states. `DataImportProgressReportView` (§4.7)
  surfaces the phase in the report (a partial-report banner while
  `phase == "validating"`) so a mid-run report is never mistaken for the final
  one — the download is **not** refused mid-run (§4.7).
- The per-poll payload is the list contents returned as an array; for very large
  imports it can be made cursor-based (the JS sends the last index it rendered
  and the view `lrange`s from there) to keep the payload constant per poll. This
  is an optimization; the index-based append above is the baseline.

Rejected alternative: **periodic full dump** — rewriting
`import_data_validation_results_{job_id}` as a JSON list every
`VALIDATION_REDIS_UPDATE_INTERVAL` rows and having
the JS replace the whole table each poll. Simpler, but rewrites a growing blob on
every flush and re-sends the full list every second; the list-based append is a
better fit for the existing import-phase pattern and for large imports.

## 5b. Validation progress bar (reusing the import progress bar)

> Scope of this section: the **progress bar** the admin sees during the
> `validating` phase (0 → 100 %). It is the user-visible counterpart to the
> `validation_progress` field already mentioned in §2.5, §4.6 and §4.8. The
> rows-table incremental rendering is a separate concern, covered in §5; this
> section is only about the single percentage bar.

### 5b.1 Current import progress bar (the model to mirror)

The import phase already drives a single percentage bar in the template from
Redis state, with no JavaScript-side interpolation of phase constants — the
server computes a 0–100 integer and the JS just sets the bar width. The
mechanism, end to end:

**Writer side — `run_data_import` (`webclient/cron/tasks.py`).** The import
progress is **not** one key but a layered set of phase + sub-phase keys, written
purely from the task:

1. A coarse **phase key**, `import_data_progress_{job_id}` ∈
   {`IMPORT_PROGRESS_PHASE_FAILED=0`, `_DATA_DONE=25`, `_HISTORY_DONE=50`,
   `_FEDORA_DONE=75`, `_FINISHED=100`} (`tasks.py:74-79`). The task `SET`s this
   key to the matching constant at the boundary of each phase
   (`tasks.py:728`, `:1066`, `:1150`, `:1240`, `:1647`/`:1653`), always with
   `ex=IMPORT_DATA_RUNNING_TTL_SECONDS`. This is the *only* key the import phase
   writes for "which phase are we in".
2. A pair of **sub-phase numerator/denominator keys** for each sub-phase that
   can run long, written while the phase key stays fixed at its phase boundary:
   - data phase: `import_data_progress_ids_{job_id}` /
     `import_data_progress_details_{job_id}` (the list the JS reads to fill the
     table is also the *count* the progress fraction is derived from — see
     §5b.3) plus `import_data_count_{job_id}` (the total record count, set once
     at upload in `admin_sites.py:533`).
   - history phase: `import_data_history_progress_{job_id}` /
     `import_data_history_total_{job_id}` (`tasks.py:1085-1086`, incremented at
     `:1138-1141`).
   - fedora phase: `import_data_fedora_progress_{job_id}` /
     `import_data_fedora_total_{job_id}` (`tasks.py:1160-1161`, incremented at
     `:1230-1233`).
   - file phase: `import_data_files_progress_{job_id}` /
     `import_data_files_total_{job_id}` (`tasks.py:1294-1298`, incremented at
     `:1490`).
   The numerator is incremented every row (or every `HISTORY_REDIS_UPDATE_
   INTERVAL` rows for the history JSON checkpoint — `tasks.py:1142-1145`),
   and the denominator is `SET` once at phase start. None of these sub-phase
   keys ever holds a 0–100 percentage directly; they hold raw counts.

**Reader side — `DataImportProgress` (`webclient/core/views.py:2747-2849`).**
The view reads the phase key and the relevant sub-phase pair and **computes the
0–100 integer server-side**, with one cascading `if/elif` ladder
(`views.py:2795-2819`):

```
if phase_progress >= FINISHED (100):       progress_data = 100
elif phase_progress >= FEDORA_DONE (75):   progress_data = 75 + floor(files_frac   * (100-75))
elif phase_progress >= HISTORY_DONE (50):  progress_data = 50 + floor(fedora_frac  * (75-50))
elif phase_progress >= DATA_DONE (25):     progress_data = 25 + floor(history_frac * (50-25))
elif record_count:                         progress_data = floor(serialized_results_len / record_count * 25)
else:                                      progress_data = 0
```

where `*_frac = min(numerator / denominator, 1.0)` via the local helper
`_phase_fraction(progress_key, total_key)` (`views.py:2788-2793`). Crucially,
the **data phase (0 → 25 %)** has *no* dedicated numerator/denominator pair of
its own — its fraction is derived from `len(serialized_results) /
record_count`, i.e. from the length of the same `import_data_progress_ids`
list the table is built from (`views.py:2816-2817`). That is the precedent the
validation bar reuses (§5b.3).

The view returns the computed integer as `progress_data` in the JSON
(`views.py:2828`), alongside `record_count`, `finished_record_count`,
`serialized_results`, etc.

**Template side — `admin/import_data/import_data.html`.** The bar is a plain
`<div class="progressBar">` whose width is set to `progress_data + "%"` by JS
(`import_data.html:72-76`, `:251-261`):

```javascript
maxProgressData = Math.max(maxProgressData, data.progress_data)
progressBarData.style.width = maxProgressData + "%"
progressPercentData.textContent = maxProgressData + "%"
```

`maxProgressData` is a monotonic high-water mark so the bar never goes
backwards between polls (it guards against a transient stale read showing a
lower value). The bar element id is `progressBarData` / `progressBarBoxData` /
`progressPercentData` (`import_data.html:72-76`). There is **no per-phase bar**;
the single bar is reused across every import sub-phase by feeding it
`progress_data` from whatever phase is active.

**Reset behavior.** The POST handler sets `import_data_progress_{job_id} = 0`
at upload (`admin_sites.py:537`), and `run_data_import` re-`SET`s it to the
phase boundary at each phase transition (including back to `0` on the
`record_count <= 0` early-fail at `tasks.py:726-730`). The JS `maxProgressData`
is a per-page-load variable (`import_data.html:220`), so reopening the page
starts the bar at whatever `progress_data` the server returns (no client-side
reset needed).

**Summary of the pattern.** The import progress bar is:

1. A coarse **phase key** (one `SET` per phase boundary).
2. A **numerator/denominator pair per long-running sub-phase** (raw counts,
   incremented as rows are processed), or a derived count from the live list
   for the data sub-phase.
3. **Server-side computation** of the 0–100 integer in the progress view, not
   in the template.
4. A **single template bar** reused across phases, fed by `progress_data`,
   with a monotonic client-side high-water mark.

### 5b.2 Requirement for the validation phase

The admin must see **one** progress bar during validation that goes from 0
(beginning of validation) to 100 (end of validation). The **same** template
bar is reused — no new bar element, no new CSS, no new JS percentage logic.
When validation finishes and the import phase starts, the bar must **reset to
0** and then climb again exactly as the import bar does today. Concretely:

- During `phase == "validating"` the bar shows `validation_progress` (0–100).
- On transition to `awaiting_approval` the bar is left at 100 % (validation
  done) — this is the natural "you can now review" visual cue. The JS keeps the
  monotonic high-water mark, so the bar stays pinned at 100 % while the user
  reviews; *Start* is enabled.
- On transition to `importing` the bar **resets to 0** and then climbs with
  the existing import `progress_data` logic. This reset is **explicit** and is
  the only place the monotonic `maxProgressData` high-water mark is bypassed:
  see §5b.5 for the exact mechanism (the template switches the source field
  from `validation_progress` to `progress_data` and resets
  `maxProgressData = 0` once on the `validating → importing` transition).

This matches the user stories in §2.5 (US-2 "watch validation progress", US-4
"review and start") and the per-phase information table in §2.5.4
(`validating` → validation progress bar; `importing` → import progress bar).

### 5b.3 Validation progress — recommended key layout (mirrors the import bar)

Validation is a **single sub-phase** (parse + map + `import_validation` +
`create_records` per row), so it needs only the data-phase pattern: a
numerator/denominator pair driven by the row loop, with the server computing
0–100 from it. No `IMPORT_PROGRESS_PHASE_*` constants are added and the
existing import `import_data_progress_{job_id}` key is **not** touched by the
validation task (avoiding any collision with the import phase's cascading
`if/elif` ladder in `DataImportProgress`).

**New keys (already listed in §6, restated with the bar semantics):**

- `import_data_validation_total_{job_id}` — denominator. `SET` once by the
  validation task at the start of the row loop, to the total row count across
  all CSVs in the ZIP (§4.2 step 5). The POST sets it to `0` (or leaves it
  unset) at upload so the bar reads 0 % before the task picks up
  (§4.1 step 9).
- `import_data_validation_progress_{job_id}` — numerator. Incremented by the
  validation task **once per processed row** (§4.2 step 6), after the row's
  `ImportDataValidationResult` is built and pushed to the live list. It counts
  *processed* rows (valid + invalid), not just valid ones — the bar tracks how
  far through the file the task has gotten, not how many passed. Both keys use
  `ex=IMPORT_DATA_RUNNING_TTL_SECONDS` while `validating`; on validation
  success they are `persist()`ed alongside the other per-job data keys (§3.2,
  §6); on `failed`/`stopped` they are `expire()`d to
  `IMPORT_DATA_EXPIRATION_SECONDS` in the validation task's `finally` (§4.2
  step 8).

**No second phase key for validation.** Validation has no sub-phases that need
a coarse phase boundary of their own (unlike import's data/history/fedora/file
phases). The single numerator/denominator pair is enough. If a future
extension splits validation into, say, "parse" + "validate" sub-phases, add a
phase key then — but do not pre-design for it; the import bar's layered shape
is a response to import's *actual* sub-phases, not a template validation must
copy.

**Why not reuse `import_data_progress_{job_id}` for validation.** That key is
the input to the import-phase `if/elif` ladder in `DataImportProgress`
(`views.py:2795-2819`) and to `IMPORT_PROGRESS_PHASE_*`. Writing validation
values into it would either (a) require adding a `VALIDATION_DONE` constant
and shifting every existing `IMPORT_PROGRESS_PHASE_*` number — touching the
import task, the view, and every existing import test that asserts on the
constants (see `cron/tests/_run_data_import_mapper_base.py:385` and the many
`test_run_data_import_*.py` assertions on `IMPORT_PROGRESS_PHASE_FAILED`/
`FINISHED`), or (b) overload the key's meaning so the view cannot tell
"validating" from "importing data phase". Keeping a separate
`import_data_validation_progress_{job_id}` /
`import_data_validation_total_{job_id}` pair, switched on by
`phase == "validating"` in the view, leaves the import constants and tests
untouched. This is the same recommendation §4.6 already makes ("keep
`progress_data` for the import phases only and let the template use `phase` +
`validation_progress` for the validation bar"); this section spells out the
key layout that implements it.

### 5b.4 Reader side — `DataImportProgress` (minimal extension)

Add the validation branch **above** the import `if/elif` ladder, gated on
`phase`, so it never collides with the import logic:

```python
phase = redis_connector.get(f"import_data_phase_{job_id}")
phase = phase.decode("utf-8") if phase else "unknown"

if phase == "validating":
    validation_total = int(redis_connector.get(f"import_data_validation_total_{job_id}") or 0)
    if validation_total:
        validation_done = int(redis_connector.get(f"import_data_validation_progress_{job_id}") or 0)
        progress_data = min(int(validation_done / validation_total * 100), 100)
    else:
        progress_data = 0
else:
    # existing import if/elif ladder (views.py:2795-2819) unchanged
    ...
```

Return `progress_data` as today (`views.py:2828`). The template will use
`phase` to decide whether the bar represents validation or import (§5b.5).
**Reuse `progress_data` — do not add a separate `validation_progress` field.**
`progress_data` itself is the bar value in both phases, so the template's
`maxProgressData` logic is unchanged; the only template change is the reset on
phase transition (§5b.5). (Earlier §4.6/§2.5 mentions of "validation_progress"
are satisfied by `progress_data` while `phase == "validating"` — they refer to
the *concept* of a validation bar value, not to a separate JSON field.)

**Edge cases:**

- `validation_total == 0` (task has not set it yet, or empty ZIP parsed to
  0 rows): bar reads 0 %, not a division error. The `else: progress_data = 0`
  branch handles this.
- `validation_done > validation_total` (defensive against a counting bug): the
  `min(..., 100)` clamp keeps the bar at 100 %, never above.
- Validation finished, `phase == "awaiting_approval"`: the import `if/elif`
  ladder runs, but the import keys are still at their initial values
  (`import_data_progress_{job_id} = 0` from the POST, `record_count = 0`), so
  the ladder falls through to `progress_data = 0`. The template **pins** the
  bar at 100 % in this phase (§5b.5) — it does not show 0 % during review. This
  is the one place the server-side `progress_data` value and the displayed bar
  intentionally diverge; the pin is in the template, not the view, so the view
  stays a pure reflector of Redis state.

### 5b.5 Template side — reuse `progressBarData`, switch on `phase`, reset on transition

The single existing bar (`progressBarData` / `progressBarBoxData` /
`progressPercentData`, `import_data.html:72-76`) is reused for both phases. The
JS gains a small phase-aware layer on top of the existing
`maxProgressData` logic:

```javascript
let currentPhase = null          // null | "validating" | "awaiting_approval" | "importing" | terminal

function applyProgress(data) {
    const phase = data.phase
    // Reset the bar to 0 exactly once when leaving the validation/review
    // phases and entering the import phase. This is the ONLY place
    // maxProgressData is reset downward; it is the explicit reset required
    // by §5b.2.
    if (phase === "importing" && currentPhase !== "importing") {
        maxProgressData = 0
    }
    currentPhase = phase

    if (phase === "awaiting_approval") {
        // Pin the bar at 100 % during review (validation just finished).
        // The server's progress_data reads 0 here (import keys are still
        // initial), so do not use it; show the completed-validation bar.
        maxProgressData = 100
    } else {
        maxProgressData = Math.max(maxProgressData, data.progress_data)
    }

    const progressBarData = document.getElementById("progressBarData")
    if (progressBarData) {
        progressBarData.style.width = maxProgressData + "%"
        const progressPercentData = document.getElementById("progressPercentData")
        progressPercentData.style.left =
            `${document.getElementById("progressBarBoxData").offsetWidth / 2}px`
        if (maxProgressData > 0) {
            progressPercentData.textContent = maxProgressData + "%"
        }
    }
}
```

`applyProgress(data)` replaces the inline block at `import_data.html:250-261`.
The rest of the existing `sendRequest` body (status message, table fill,
file-table append, terminal-state handling) is unchanged.

Behavior by phase, matching §2.5.4 and §4.8:

- `validating` — `progress_data` is the validation percentage (0–100, §5b.4).
  The bar climbs from 0 to 100 as rows are processed. `maxProgressData` is
  monotonic within this phase (no reset).
- `awaiting_approval` — bar pinned at 100 % (validation done, awaiting
  review). *Start* enabled, *Cancel/Release* enabled, *Download report*
  enabled (§4.8). Polling continues for UI display only; the bar does not
  move.
- `importing` — on the first poll where `phase == "importing"`,
  `maxProgressData` is reset to 0 once, then the bar climbs with the import
  `progress_data` (the existing `if/elif` ladder, unchanged). This is the
  reset required by §5b.2. From this point the existing monotonic behavior
  takes over and the bar behaves exactly as it does today.
- `finished` / `stopped` / `canceled` / `failed` — `progress_data` reflects
  the terminal value (100 for `finished`, 0 for `failed` with
  `IMPORT_PROGRESS_PHASE_FAILED`, etc.). `maxProgressData` is not reset on
  terminal transitions, so the bar shows the last-reached value (e.g. a
  `failed` import shows the point it failed at, not 0) — matching today's
  behavior.

**Why the reset is in the template, not the server.** The server cannot tell
"first poll of the importing phase" from "later poll of the importing phase"
without extra state — it just returns `progress_data`. The template *can*, via
the `currentPhase !== "importing"` guard, and it is the layer that already
owns the monotonic high-water mark. Keeping the reset there matches the
existing architecture: the view reflects Redis, the template renders.

### 5b.6 Status message alongside the bar

The bar's status line (`#processCurrentStatus`, `import_data.html:80`,
`:236-237`) already reads `data.status_message`. The validation task writes a
per-row status message of the form `"Validating row N/M"`
(`_("cron.tasks.run_data_import.validating")` + `N/M`, see §4.2 step 6 and the
existing pattern at `tasks.py:785-792` for the import "importing record N/M"
message). No new template element is needed; the status message and the bar
move together as they do during import.

### 5b.7 Tests

Add to the validation-task unit tests (§10):

- `import_data_validation_total_{job_id}` is set to the total row count once
  at the start of the row loop.
- `import_data_validation_progress_{job_id}` is incremented exactly once per
  processed row and equals `validation_total` at the end of a successful
  validation (so the bar reaches 100 %).
- On `failed` (validation_rejected) and `stopped` paths, both keys are
  `expire()`d to `IMPORT_DATA_EXPIRATION_SECONDS` (6 h), not `delete()`d.

Add to the view tests (§10):

- `DataImportProgress` with `phase == "validating"` returns
  `progress_data = floor(validation_done / validation_total * 100)`, clamped
  to [0, 100]; with `validation_total == 0` returns `progress_data = 0`; with
  `validation_done > validation_total` returns `100` (clamped).
- `DataImportProgress` with `phase == "importing"` still returns the existing
  import `progress_data` (regression guard that the validation branch did not
  disturb the import ladder).

No template-level test is required (the project has no JS test harness); the
reset-on-transition logic is small enough to be reviewed against this section.

## 6. New Redis keys (summary)

| Key | Set by | Purpose |
|---|---|---|
| `import_data_current_job_{user_id}` | upload POST | per-user in-flight job pointer for the page |
| `import_data_phase_{job_id}` | both tasks + start/cancel views | lifecycle state |
| `import_data_lock_token_{job_id}` | upload POST | lock token reused by `DataImportStart` (refresh) and `DataImportCancel` (release) |
| `import_data_file_{job_id}_{i}` | upload POST | staged compressed-ZIP chunk *i* (§3.3) |
| `import_data_file_chunks_{job_id}` | upload POST | chunk count *N* for reassembly |
| `import_data_user_{job_id}` | upload POST | owner (authz) |
| `import_data_validation_total_{job_id}` | validation task | validation progress denominator (§5b.3) |
| `import_data_validation_progress_{job_id}` | validation task | validation progress numerator, incremented per processed row (§5b.3) |
| `import_data_validation_results_{job_id}` | validation task | JSON snapshot for the report; dumped at end of validation (checkpointed every `VALIDATION_REDIS_UPDATE_INTERVAL` rows, §4.2 step 6) |
| `import_data_validation_ids_{job_id}` / `import_data_validation_details_{job_id}` | validation task | live incremental-rendering lists (`rpush` per row, `lrange`d by `DataImportProgress`; §5) |
| `import_data_invalid_records_{job_id}` (optional) | validation task | list of invalid row orders |
| `import_data_failure_reason_{job_id}` | validation task | `failed`-phase discriminator: `"validation_rejected"` (fixable invalid rows) vs `"error"` (crash) — drives the §4.8 `failed` UI branch and the distinct status message (§4.2 step 7) |

All keys use `ex=IMPORT_DATA_RUNNING_TTL_SECONDS` (6 h) while `validating`/
`importing`. On validation **success** the validation task `persist()`s the
lock and all per-job data keys (removes the TTL) so they survive
`awaiting_approval` no matter how long the reviewer takes (§3.2);
`DataImportStart` re-attaches the 6 h TTL to the lock before dispatching the
import. On a terminal outcome the tasks' `finally` blocks `expire()` the data
keys back to 6 h (report retention); `DataImportCancel` likewise `expire()`s the
per-job data keys back to 6 h (report retention on a `canceled` job; the keys
had no TTL during review, so this both bounds them and keeps the report
downloadable — §4.5, §4.7). This matches the
existing cleanup pattern in `run_data_import`'s `finally` (`tasks.py:1678`).

## 7. Authorization / ownership

Today the views only check `is_superuser`. With a persistent, page-resumable
job, add a cheap ownership check so one admin cannot mutate or exfiltrate
another's job: store `import_data_user_{job_id}` at upload and compare against
`request.user.id`. Enforce the check on the **mutating** actions
(`DataImportStart`, `DataImportStop`, `DataImportCancel`) and on
`DataImportProgressReportView` (the report contains validation data).
`DataImportProgress` may return its data payload to any superuser (so an admin
can see what is running) — it does not touch the lock at all (§4.6), so there
is no heartbeat for a non-owner to worry about. (Superusers are a small set, so
the mutating-action checks are defense-in-depth rather than a hard requirement
— call it out as recommended.) **Stuck-job recovery:** because an
`awaiting_approval` job holds the lock with no TTL (§3.2), a forgotten job
blocks all other imports until it is explicitly canceled. Relax ownership for
this case: **any superuser** (not just the owner) may call `DataImportCancel`
(§4.5) on a stuck `awaiting_approval` job to release the lock and `expire()` its
data keys to 6 h. The owner check still applies to `DataImportStart` and to cancel of
an active `validating`/`importing` job.

## 8. Deployment prerequisites

- **No shared filesystem between `web` and `celery_worker` is required.** The
  staged ZIP lives in Redis, which is already a shared service on `prod-net`
  reachable from both containers (`docker-compose.yml`). This removes the
  disk-staging prerequisite that a tempfile approach would impose — no new
  `CustomAdminSettings` path, no writable shared volume, no orphan-file
  janitor.
- **Chunk size — source-level constant, not runtime-configurable.**
  `IMPORT_DATA_REDIS_CHUNK_SIZE` (64 MiB) in `webclient/core/admin_sites.py`,
  next to `IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE` (§11). It is a source-level
  constant, not a `CustomAdminSettings`/import-settings value — there is no
  reason to tune it at runtime. It bounds each Redis `SET`/`GET` blocking window
  and keeps every value well under the Redis 7+ `proto-max-bulk-len` default
  of 512 MiB. The customer-facing upload limit is unchanged.
- **No new compressed-size cap.** Do not add a hard limit on the compressed
  upload size — it is not a customer requirement and may be rejected. Chunking
  makes arbitrary compressed sizes work, bounded only by Redis RAM.
- **Three memory ceilings — confirm the deployment tolerates each.** The
  refactor introduces three distinct memory peaks; all three must be sized for,
  and none is reducible to another:
  - **Redis RAM (~250 MB).** The existing, customer-accepted
    `IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE = 1024 MB` cap is the guardrail on total
    data volume. Because the import ZIP is CSV-only and compresses ~3-5x, a
    maximum-size job occupies ~200-330 MB of Redis RAM during validation
    (deleted at end of validation, §3.3). Document this relationship: if the
    uncompressed cap is ever raised, recompute the compressed/RAM footprint
    against Redis capacity before doing so. `redis/redis.conf` currently has no
    `maxmemory`/eviction policy, so a large staging cannot evict other keys —
    monitor Redis memory. If AOF/RDB is on, the short-lived chunks are written
    to the persistence file and replayed on restart; acceptable for an
    infrequent admin upload, but monitor RDB/AOF size growth.
  - **Web-worker upload peak (~250-500 MB transient).** The Redis RAM figure
    above is only the worker/bus side. The **web-process** side has a matching
    transient peak that the document must not omit: §4.1 step 8 reads
    `file_bytes = data_file.read()`, which pulls the **entire compressed upload
    (~200-330 MB for a maximum-size job) into the web worker's RAM in one shot**,
    and the chunk-splitting then holds that buffer plus the chunk list (a second
    reference to the same bytes) while pipeline-`SET`ting. A single upload can
    therefore spike a web worker to ~250-500 MB transiently. Django streams
    uploads larger than `FILE_UPLOAD_MAX_MEMORY_SIZE` (default 2.5 MB) to a temp
    file, but `.read()` re-materializes the whole file in RAM regardless of that
    threshold — so the "disk-less for application data" property does **not**
    protect the web worker here; the temp file Django wrote is bypassed by the
    explicit `.read()`. The production web server is **uWSGI**
    (`scripts/uwsgi_site.ini`: `processes = 15`, `enable-threads = false`, no
    `limit-as`/per-worker memory cap), not gunicorn; a worker that spikes is not
    killed by any configured memory limit. Two factors keep this contained: (a)
    the global import lock serializes uploads, so **only one of the 15 workers
    spikes at a time** — no concurrent multi-hundred-MB spike across workers; (b)
    the spike is **transient** — `file_bytes` and the chunk list are freed when
    the request returns, well before the minutes-long validation. For an
    infrequent admin action this is acceptable, but the deployment must confirm
    the uWSGI worker RSS headroom tolerates a ~500 MB transient spike (and that
    no container memory limit `<500 MB` would OOM-kill the worker mid-upload).
    Record this characteristic in the `import_data` view docstring (§4.1) so it
    is not rediscovered as a production outage. If the uncompressed cap is ever
    raised, recompute this web-worker peak alongside the Redis RAM figure.
  - **Validation worker peak (several GB — the binding constraint).** The §3.3
    ~250 MB figure is the *compressed* staging blob and the §4.2 step-2 "one
    chunk + reassembled blob" line is the *reassembly* peak — neither is the
    Celery worker's actual high-water mark. Validation is what dominates worker
    RAM, and the document must say so. From the current code
    (`admin_sites.py:420-499`, moved unchanged into the task): for each CSV,
    `sheet = pd.read_csv(file, dtype=str)` builds an **object-dtype DataFrame**
    — one Python `str` object per cell, so the DataFrame is larger than the raw
    CSV text (per-cell `PyObject` overhead, ~50 bytes/cell, on top of the string
    data); `mapper_class.validate_batch_ordering(sheet.to_dict("records"))`
    then builds a **second full copy** of that file as a list of dicts; and the
    `records` list (`records += mapper.create_records(...)` / `records.append
    (record)`) **accumulates every valid record across every file for the whole
    pass** (it backs `LookupImportField.set_records(records)` for cross-reference
    lookups). The per-file DataFrame and `to_dict` copy are transient (the
    previous `sheet` is dropped each iteration), but `records` is a persistent
    accumulator that grows to the full valid dataset as Python dicts. For a
    maximum-size 1 GB-uncompressed job this is **several GB of worker RAM** —
    the decompressed text + object-dtype DataFrames + the `to_dict` copy + the
    `records` accumulator — which dwarfs the ~250 MB compressed blob. The
    reassembled compressed blob itself is freed once the ZIP is open, so it does
    not stack on top. Two properties keep this bounded today: (a) the existing
    `IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE = 1024 MB` cap bounds the input, hence the
    DataFrame/`records` size; (b) the global import lock serializes the whole
    pipeline, so only one validation runs at a time — no concurrent multi-GB
    spikes across workers. **Operational consequence:** the Celery worker must
    be sized for this multi-GB transient, not for the ~250 MB compressed figure;
    confirm the `celery_worker` container memory limit and the worker's RSS
    headroom tolerate a several-GB validation peak (and that no
    `--max-memory-per-child`/OOM limit kills the worker mid-validation). If the
    uncompressed cap is ever raised, recompute this validation peak first — it
    scales linearly with the uncompressed size and is the binding constraint,
    not Redis RAM. Record this in the `run_data_import_validation` task docstring
    alongside the read-only contract (§4.2).

## 9. Alternatives and tradeoffs

- **Hold one continuous lock across validation + review + import (chosen).**
  Acquire the lock when validation starts and keep it until
  `run_data_import`'s `finally` releases it (or explicit Cancel), reusing one
  token. This serializes the whole pipeline and prevents the stale-validation
  conflict described in §3.2 (two imports validating against the same pre-import
  DB state and then crashing at import time). The review-window concern (lock
  held during review with no TTL) is mitigated, not by releasing the lock or by
  a heartbeat, but by an explicit *Cancel/Release* action (§4.5) — available to
  any superuser for a stuck job (§7). This is the approach adopted in §3.2/§4.4.
- **Release the lock at end of validation; re-acquire in `DataImportStart`
  (rejected).** Frees the lock during `awaiting_approval` so other admins can
  upload/validate/start concurrently. **Rejected because it reintroduces the
  stale-validation conflict** (§3.2): a second file can validate against a DB
  state the first pending import is about to change, and both imports then
  proceed (validation already passed) until the second crashes at import time.
  The whole point of holding the lock across review is to make
  validation+import one indivisible, serialized unit.
- **Single task with an approval gate.** One task validates, then polls an
  `import_data_approved_{job_id}` flag set by `DataImportStart`, then imports.
  Pro: one lock, one token, naturally continuous, and the worker holds the lock
  during review (no separate refresh needed). Con: occupies a Celery worker for
  the entire review window. Rejected in favor of two tasks for worker
  utilization; the no-TTL `persist()` of the lock on validation success (§3.2)
  replaces the worker-driven hold.
- **Stage the compressed ZIP in Redis, chunked (chosen, §3.3).** The POST splits
  the compressed upload into `IMPORT_DATA_REDIS_CHUNK_SIZE` (64 MiB, §11) chunks
  stored under `import_data_file_{job_id}_{i}` plus a count key; the validation
  task reassembles them. The full rationale (fits the existing Redis-as-bus /
  disk-less / shared-service architecture; chunk the *compressed* bytes to keep
  Redis RAM at ~250 MB, bound each `SET`/`GET` to a tens-of-ms blocking window,
  stay under `proto-max-bulk-len`, and avoid the CSV row-boundary problem; no
  new compressed-size cap; ZIP deleted at end of validation) is in §3.3 and is
  not repeated here.
- **Single compressed value in Redis (rejected).** One `SET`/`GET` of the whole
  ~200-330 MB compressed ZIP is mechanically simpler (one key, no reassembly),
  and within the existing 1 GB-uncompressed cap it stays under `proto-max-bulk-
  len` — so the cap is not the issue. Rejected because a single ~250 MB
  `SET`/`GET` blocks the single-threaded Redis instance for ~2-3 s, stalling
  every other key; chunking bounds each blocking event to tens of ms and adds
  headroom if the uncompressed limit is ever raised.
- **Chunk the uncompressed CSVs (rejected).** Storing 100 MB chunks of the
  *uncompressed* CSVs would keep each value small, but it costs ~3-5x more Redis
  RAM (~1 GB vs ~250 MB) and ~3-5x more total Redis transfer (worsening, not
  easing, the single-threaded blocking), introduces CSV row-boundary splitting
  (a chunk can split a row mid-field, needing carry-over logic), and shifts
  decompression+chunking memory pressure into the POST/web process. Chunking the
  compressed bytes gets the per-value smallness without these costs.
- **Disk tempfile staging (rejected).** Writing `data_file` to a `tempfile`
  path and passing the path to the task would require a new
  `CustomAdminSettings` staging path, a writable shared volume between `web`
  and `celery_worker`, and a janitor for orphaned files from crashed workers.
  It contradicts the app's disk-less-for-application-data architecture (no
  `FileField`, `MEDIA_ROOT` unused, uploads stream to Fedora) and re-introduces
  the shared-filesystem prerequisite that Redis staging removes (§3.3/§8).
- **Object store (S3/MinIO) fallback (not required).** Only worth introducing if
  a deployment genuinely cannot fit the staging in Redis RAM (e.g. if the
  uncompressed cap were raised well above 1 GB). Not needed under the current
  cap and the chunked-compressed approach; listed here only as a future escape
  hatch, with a hard size cap and a `proto-max-bulk-len`-equivalent precheck.
- **Production runtime guard on the read-only contract (rejected).** Wrapping
  the validation loop in `transaction.atomic()` + rollback, or monkey-patching
  `create_records`/`save` to raise on writes, would enforce the mapper
  read-only contract at runtime. Rejected: `atomic()` is leaky (rolls back
  neither Fedora writes nor `save()`-signal side effects) and holds a
  minutes-long DB transaction (anti-pattern); monkey-patching is fragile and
  couples the task to mapper internals. The contract is instead enforced at
  **test time** (§10): a query-capture assertion guards DB writes, and a
  targeted `assert_not_called` on the `FedoraRepositoryConnector` external-write
  entry points guards the Fedora/HTTP side. Together they cover the two
  concrete write vectors; no production runtime cost. See §4.2.

## 10. Testing approach

Follow the existing test conventions for this codebase (Docker-based test run;
no f-strings inside `_()`/`gettext`/`gettext_lazy`):

- **Validation task unit tests** — new. Cover: lock lost at start, virus found,
  bad ZIP, unsupported files, empty ZIP, oversized ZIP, all-valid → phase
  `awaiting_approval` + `valid=1` + **lock still held** (not released),
  some-invalid → `valid=0` + `failure_reason="validation_rejected"` + lock
  released + the **distinct** `validation_rejected` status message (not the
  crash message), each crash path (virus/bad ZIP/oversized/lock-lost) →
  `failure_reason="error"` + its own crash status message, stop sentinel
  mid-validation → phase `stopped` + lock released, and all
  `import_data_file_{job_id}_{i}` chunk keys plus `import_data_file_chunks_{job_id}`
  deleted in `finally`. Assert the two failure reasons never share a status
  string. Add a chunking test: a ZIP larger than
  `IMPORT_DATA_REDIS_CHUNK_SIZE` is split into N chunks at upload, reassembled
  byte-for-byte equal to the original by the task, and parsed correctly. Add a
  failure-cleanup test: on the `failed`/`stopped` path the validation-results
  data keys (`import_data_validation_results_{job_id}`, the per-record keys, …)
  are `expire()`d to `IMPORT_DATA_EXPIRATION_SECONDS` (6 h) — **not**
  `delete()`d — so the report stays downloadable, while the ZIP chunk keys are
  `delete()`d. Add a **read-only-contract test** with two complementary
  assertions:
  - **DB writes (SQL):** run a full validation under
    `django.test.utils.CaptureQueriesContext` (or inspect
    `connection.queries_log`) and assert that **no `INSERT`/`UPDATE`/`DELETE`
    query is issued** against the DB during the whole validation pass — this is
    stronger than a row-count comparison (which misses `UPDATE`s on existing
    rows). Selects are expected (mapper lookups via `LookupImportField`); only
    write statements must be absent. This guards the DB-write side of the §4.2
    contract.
  - **External writes (Fedora/HTTP):** the SQL-capture assertion above is blind
    to non-SQL side effects — and a stray `.save()` during validation would
    fire `post_save` signals that call `save_metadata()` → Fedora HTTP writes
    (e.g. `core/signals.py:25` on `Soubor`; equivalent signals on `Osoba`,
    `Organizace`, `User`). Mock the `FedoraRepositoryConnector` external-write
    entry points (`save_binary_file`, `save_metadata`/the metadata-update
    methods, and the delete counterparts — or, equivalently, assert that no
    `FedoraTransaction` is committed during validation) and `assert_not_called`
    on each across the whole validation pass. `save_metadata` is the more
    likely regression vector than `save_binary_file` (it is the signal-driven
    path), so cover the group, not just one method. This closes the gap the
    SQL-capture test leaves open; the contract for any *other* signal side
    effect (Redis, notifications) beyond these entry points remains
    documentation-only, by design (§4.2).
  Mock `Soubor.check_antivirus`, the Redis connector, and the mapper dict as
  needed.
- **`run_data_import` tests** — extend the existing suite (see the project
  memory on `run_data_import` end-to-end tests): assert the lock is released
  and `import_data_current_job_{user_id}` is cleared in the terminal `finally`,
  and that `import_data_phase_{job_id}` is set to the terminal state.
- **View tests** — `DataImportStart` **reuses** `import_data_lock_token_{job_id}`
  and calls `refresh_import_lock` (does **not** call `acquire_import_lock`);
  returns 409 with phase `failed` if the refresh shows the lock was lost; and
  rejects when phase is not `awaiting_approval` or `valid != "1"`;
  `DataImportCancel` calls `release_import_lock`, transitions
  `awaiting_approval` → `canceled`, **`expire()`s the per-job data keys to 6 h**
  (not `delete()` — the report stays downloadable, §4.5/§4.7), and
  clears the per-user pointer; any superuser may cancel a stuck
  `awaiting_approval` job (§7); `DataImportProgress` returns
  `validation_results`, `progress_data` (driven by the validation
  numerator/denominator pair while `phase == "validating"`, §5b), and `phase`,
  and **never touches the lock** (no heartbeat); `DataImportStop` works during
  validation.
- **Conflict-regression test (the §3.2 rationale).** With job A in
  `awaiting_approval` (lock held), a second upload's `acquire_import_lock`
  must fail — assert no second job can enter `validating` while A's lock is
  held. This is the guard against the stale-validation conflict.
- **Lock scope is import-vs-import only — not a total guarantee (§3.2).** The
  global import lock serializes the import pipeline against *other import
  pipelines*, not against ordinary application writes. During the
  `awaiting_approval` window, normal (non-import) app traffic can create a
  record whose ID collides with one a pending validated import is about to
  commit, so the stale-validation conflict can reappear from a non-import
  source and the import still crashes on it at `run_data_import` time. The
  mitigation is narrow: imports run only during maintenance mode (little app
  traffic), and `run_data_import` already records per-row commit conflicts in
  the report. The lock must not be read as a total guarantee that the validated
  state still holds at import time. See §3.2.
- **Page GET test** — with `import_data_current_job_{user_id}` set, the page
  renders the polling UI bound to that `job_id` and contains **no**
  `validation_results` in the rendered HTML (regression guard for requirement 3).

## 11. Rollout

- Pure refactor of an admin-only flow; no DB migration, no schema change.
  `*/migrations/*.py` is untouched.
- No new translation namespaces strictly required — reuse existing
  `core.admin.import_data.*` and `cron.tasks.run_data_import.*` strings where
  possible; add a small number of new strings (`validating`,
  `validation_done`, `awaiting_approval`, `cancelled`, `failed_lock_lost`,
  `validation_rejected` status messages) with the standard `_()` (non-f-string)
  form. The `validation_rejected` and `error`/crash messages must be **distinct
  strings** (§4.2 step 7) so the `failed` UI can distinguish a fixable file
  from a crash.
- Add two new constants:
  - `IMPORT_DATA_REDIS_CHUNK_SIZE = 64 * 1024 * 1024` (64 MiB) in
    `webclient/core/admin_sites.py`, next to the existing
    `IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE` class attribute (`admin_sites.py:333`) —
    the compressed-ZIP chunk size for Redis staging (§3.3). A pure operational
    knob, not customer-facing; placed beside the related import-size constant
    so the two volume guardrails live together.
  - `VALIDATION_REDIS_UPDATE_INTERVAL = 50` (rows) in
    `webclient/cron/tasks.py`, next to the existing
    `HISTORY_REDIS_UPDATE_INTERVAL = 10` (`tasks.py:1083`) — governs how often the
    validation task checkpoints the `import_data_validation_results_{job_id}`
    JSON snapshot for the report (the live `import_data_validation_details` list
    is `rpush`ed every row; the final snapshot is dumped at end of validation
    regardless — §4.2 step 6, §5). A required constant, not optional: without it
    the mid-run report lags the UI by the whole validation run, which §4.7/§5
    warn against. It mirrors the existing `HISTORY_REDIS_UPDATE_INTERVAL`
    pattern (a module-level constant in `tasks.py`, checkpointing the report
    JSON every N records).
  `IMPORT_DATA_RUNNING_TTL_SECONDS` (6 h) is unchanged and still governs the
  `validating`/`importing` phases and the staging-key TTLs. **No review-window
  TTL constant is added** — the lock has no TTL during `awaiting_approval`
  (§3.2); it is `persist()`ed on validation success and re-attaches the 6 h TTL
  only when `DataImportStart` dispatches the import.
- Keep the existing URL names (`core:data-import-progress`, `-stop`, `-start`,
  `-progress-report`) and the existing template path. Add one new URL,
  `core:data-import-cancel`, wired in `webclient/core/urls.py` (see §4.5). Only
  the template's body and the views' bodies otherwise change.
- Add the read-only contract in two places (see §4.2): a comment at the
  `create_records` call site inside the new `run_data_import_validation` task
  (`webclient/cron/tasks.py`) stating it is serialization-only and must remain
  read-only, **and** a note in the base `ImportModelMapper` class docstring
  (`webclient/core/import_data_mappers.py`). Documentation only, no runtime
  guard. In the same task docstring, also record the validation worker
  peak-memory characteristic (§8): the ~250 MB compressed blob is not the
  worker high-water mark — the DataFrames + `to_dict` copies + accumulating
  `records` list reach several GB for a max-size job, and the worker must be
  sized for that.
- **Deploy-window behavior (what happens to an in-flight job on deploy).** A
  deploy restarts the `web` and `celery_worker` containers (`docker-compose.yml`);
  Redis is a separate container and is normally **not** restarted by an app
  deploy, so the per-job Redis keys survive. The outcome depends on the phase
  the in-flight job is in:
  - **`awaiting_approval` — survives, no re-upload needed.** The lock and all
    per-job data keys have **no TTL** (`persist()`ed, §3.2/§4.2 step 8), and no
    task is running (nothing to kill). After the deploy, the admin reopens the
    page, the per-user pointer still resolves to the `job_id`, the phase still
    reads `awaiting_approval`, and *Start* dispatches `run_data_import` as if
    nothing happened. This is a deliberate strength of the no-TTL review model:
    the review window is deploy-survivable. (Caveat: if Redis itself is
    restarted without AOF/RDB, the no-TTL lock is lost in memory → the job is
    unstartable → the admin re-uploads; with AOF/RDB on, the no-TTL key is
    replayed and the job survives.)
  - **`validating` / `importing` — the running task is killed; the lock lingers
    up to 6 h.** These phases hold the lock with the 6 h `IMPORT_DATA_RUNNING_
    TTL_SECONDS` TTL, refreshed only by the (now-dead) task. After the deploy,
    no refresher runs, so the lock and the `validating`/`importing` phase key
    remain for up to 6 h — blocking other imports. The normal *Cancel* does not
    help here (it sets the stop sentinel, which the dead task never reads), so
    recovery is: a superuser **force-cancels** the stuck job (§7: `release_import_
    lock` + delete per-job keys, immediate) or the deploy waits out the 6 h TTL.
    For `importing` specifically there is an additional hazard: `run_data_import`'s
    `finally` never runs, so a partially-committed import may be left in the DB
    (some rows committed, some not) with no terminal phase recorded — this is
    the messy case and requires manual inspection/cleanup of the
    partially-imported records. Operational guidance: **prefer to deploy when
    no job is `validating`/`importing`** (the lock check tells you); if a deploy
    must happen mid-pipeline, force-cancel the stuck job afterward and, for an
    `importing` job, audit the DB for partial commits before re-uploading.
  For an admin-only, one-at-a-time flow the blast radius is tiny (one job, one
  admin), but state this phase-aware behavior explicitly so a deploy during
  `importing` is not assumed clean.

## 12. Risks

Each risk states the hazard and the accepted mitigation; the full rationale lives
in the referenced section and is not repeated here.

- **Abandoned `awaiting_approval` jobs hold the lock until explicit cancel
  (§3.2).** The lock has no TTL during review, so a forgotten job blocks all
  other imports until the owner (or any superuser, §7) explicitly Cancels it.
  This unbounded block is the deliberate price of the no-implicit-cancel model
  and of preventing the stale-validation conflict. *Cancel/Release* (§4.5) is the
  only recovery path; there is no TTL backstop.
- **Lock-loss during review (§3.2/§4.4/§4.8).** With no TTL, the lock can only be
  lost via a superuser force-cancel (§7) or a Redis restart. The owner's next
  *Start* then sees `refresh_import_lock` return `False` → `failed`
  (`failed_lock_lost`), not startable. The UI must surface this as an explicit
  "re-upload" state, not a generic error (§4.8).
- **Deploy during `validating`/`importing` leaves a stuck lock, and `importing`
  may partially commit (§11).** The killed task can no longer refresh the 6 h
  TTL or run its `finally`; the normal *Cancel* cannot help (the dead task never
  reads the stop sentinel). Recovery is a superuser force-cancel (§7) or waiting
  out the TTL; for an `importing` job, also audit the DB for partial commits.
  `awaiting_approval` is unaffected (no TTL, no running task). Mitigation: deploy
  when no job is `validating`/`importing`.
- **Orphaned chunk keys from crashed workers (§3.3/§8).** Chunks linger until
  their 6 h `ex=` TTL; the TTL is the backstop (no disk janitor — staging is in
  Redis), and `run_data_import`'s `finally` also defensively deletes leftovers.
  Bounded by the 6 h worst case and the ~250 MB Redis RAM ceiling; monitor Redis
  memory if large imports are frequent.
- **Validation worker peak memory is several GB, not ~250 MB (§8).** The
  compressed blob is the Redis/reassembly figure, not the worker high-water
  mark; the binding constraint is the validation pass (DataFrames + `to_dict`
  copies + the accumulating `records` list). Sized for via the
  `IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE` cap and the global lock's serialization;
  confirm the `celery_worker` memory limit tolerates a several-GB peak. Full
  analysis in §8.
- **Incremental validation payload size (§5).** Choose the append-via-lists
  strategy if very large imports are expected.
- **Concurrent page opens by different admins.** The
  `import_data_current_job_{user_id}` pointer is per-user; an admin with no
  in-flight job sees the *import_is_running* banner when another admin holds the
  lock and cannot upload until that pipeline ends or is canceled — the intended
  serialization.
- **`RedisConnector` is not connection-fault-tolerant (pre-existing,
  cross-cutting).** It caches one client with no `health_check_interval` /
  `socket_keepalive` / `Retry` policy (`connectors.py:58-78`); redis-py's pool
  self-heals dropped connections, so the real failure mode is a Redis *outage*
  (infrastructure). This refactor reuses the cached connector consistent with
  the existing `DataImportStart` — `SET NX EX` atomicity is server-side. If
  hardening is desired, make `RedisConnector` fault-tolerant globally as a
  separate task; do **not** special-case this view with a one-off
  `redis.Redis(...)` connection.

## 13. Stop-scenario analysis — what happens when the user stops an import

> Added 2026-07-26. This section enumerates **every situation that can occur when
> an admin stops an import**, phase by phase, including the data left behind, the
> latency, the terminal state, and the recovery path. It reflects the code on
> branch `feat/391`, **including the uncommitted change that makes a stop during
> the data phase roll back** (see §13.4 S-I1). Line numbers are `webclient/cron/tasks.py`
> unless stated otherwise.
>
> **Consistency note vs. the rest of this document:** §2.5.1 US-8 and §3.1 still
> describe the *old* "finish the current row, keep what committed" semantics.
> §13 supersedes them for the **data phase**, which now **rolls back** on stop.
> The post-data phases (history, Fedora, files) are unchanged and still keep what
> they committed. US-8/§3.1 should be reconciled with §13 in a follow-up edit.

### 13.1 The stop mechanism (recap)

"Stop" is **cooperative**, not preemptive. It never touches the worker directly:

1. `DataImportStop.get` (`views.py:2944`) — superuser + `_check_import_ownership`
   (owner only) — sets the sentinel `import_data_stop_{job_id} = 1` (no expiry)
   and returns `{"result": "ok"}`. It does **nothing else**: no lock release, no
   phase change.
2. `DataImportCancel.post` (`views.py:2974`) for a **`validating`** job treats
   *cancel ≡ stop* — it also just sets the sentinel (`views.py:3015`). **This
   branch is disabled in the UI** (§2.5.3): during `validating` only *Stop* is
   offered, since Cancel would be an identical second stop button; the branch
   remains as a defensive no-op but is not reachable from the page. For an
   **`importing`** job, Cancel is **rejected with 409** (`views.py:2993`) — the
   only way to halt a running import is Stop.
3. The running task must **poll** the sentinel at a checkpoint, react, and then
   unwind through its `finally` (the block at `tasks.py:1672`) which sets the
   terminal phase, releases the lock, clears `import_data_current_job_{user_id}`,
   and expires every per-job key to 6 h.

Two consequences follow from this design and drive everything below:

- **The sentinel is only honored where it is polled.** If the code path the
  worker is currently executing does not read `import_data_stop`, the stop is
  deferred until the next path that does — or ignored entirely if no such path is
  reached before the job finishes.
- **If the worker dies, nothing reacts.** A dead worker never polls the sentinel
  and never runs its `finally`, so the lock and pointer are stranded (§13.6).

### 13.2 Where the sentinel is actually polled

| Task / phase | Polls `import_data_stop`? | Location |
|---|---|---|
| `run_data_import_validation` — per row | **yes** | `tasks.py:2136` |
| `run_data_import` — data-record loop, per record | **yes** | `tasks.py:1007` |
| `run_data_import` — history loop | **no** (only reacts to `stopped` already set) | `tasks.py:1108` (guard added) |
| `run_data_import` — Fedora loop | **no** (only reacts to `stopped` already set) | `tasks.py:1179` (guard added) |
| `run_data_import` — `pending_soubor_fedora_deletes` (DELETE) | **no** (guarded by `not stopped`) | `tasks.py:1021` |
| `run_data_import` — directory file-import loop, per file | **yes** | `tasks.py:1324`, `:1329` |
| `run_data_import` — `pending_related_metadata` sub-loop | **no** | `tasks.py:1519` (guarded by `not stopped`) |

The critical gap is the middle rows: **the history and Fedora phases never
re-read the sentinel.** They only observe `stopped == True` if it was already set
during the *data* loop. A stop that first arrives while the worker is in history
or Fedora is invisible to those phases (§13.4 S-I2/S-I3).

### 13.3 Stop during `validating` and `awaiting_approval`

- **S-V1 — Stop during `validating`.** (*Stop* is the only control offered here;
  Cancel is disabled in the UI — §2.5.3.) The per-row poll (`tasks.py:2136`)
  fires on the next row: `_set_failure("error", stopped_by_user, phase="stopped")`,
  a final results snapshot, `release_import_lock`, `_clear_current_job_pointer`,
  `_expire_data_keys_on_terminal`, `return`. Validation is **read-only by
  contract** (§4.2), so there is **nothing to roll back**. Latency ≈ one row.
  Outcome: `phase = stopped`, lock free, pointer cleared → the admin can start a
  new import immediately; the report is retained 6 h. **Clean.**
- **S-A1 — `awaiting_approval`.** There is **no Stop** here (US-8/§2.5.3); the
  Stop button is disabled and only Cancel is offered. Cancel (`views.py:3018`)
  releases the lock, sets `phase = canceled`, expires keys, clears the pointer.
  No task is running and the import never touched the DB, so nothing is
  committed. Immediate and clean.

### 13.4 Stop during `importing` — by sub-phase

The import task runs four sub-phases in order: **data records** (one
`transaction.atomic()` block) → **history** → **Fedora metadata** → **directory
files**. When the stop is honored depends entirely on which sub-phase is active.

- **S-I1 — Stop during the data-record loop (the fast, clean path).** The poll
  at `tasks.py:1007` fires after the current record. Because of the uncommitted
  change, the user-stop branch calls `transaction.set_rollback(True)`
  (`tasks.py:~1011`), so when the `atomic()` block exits **every data record
  committed so far is rolled back**. The history and Fedora phases are then
  skipped (`if failed or stopped: break` / `if not failed and not stopped:`), the
  file phase is skipped (already guarded `not stopped`), and the per-record
  "success" markers are relabeled `rolled_back` (`tasks.py:~1090`). `finally`
  sets `phase = stopped`, releases the lock, clears the pointer. **Latency: the
  current record only. Result: nothing persisted — a true abort.**
  - **DELETE imports (resolved, review r3703505209):** in the DELETE path a record is
    removed with a `FedoraDeletionOnlyTransaction`, but that transaction is no longer
    committed inside the `atomic()` block. Every deletion transaction is queued and
    committed from a single `transaction.on_commit` callback
    (`commit_pending_fedora_delete_commits`), which Django does not run when the
    transaction rolls back. A stopped or failed delete-import — including a failure of
    the database commit itself — therefore leaves Fedora untouched, and the queued
    transactions are explicitly rolled back. The abort is now clean in **both** stores.
- **S-I2 — Stop during the history phase (deferred or ignored).** The data loop
  has already **committed** (the `atomic()` block exited normally). The history
  loop does not poll the sentinel and `stopped` is still `False`, so **history
  runs to completion**, then Fedora runs to completion. The stop is first seen at
  the **file phase** (`tasks.py:1329`) *if the import has directory files* — the
  job then ends `stopped` with data+history+Fedora **committed** and files
  partially imported (S-I4). **If the import has no files, the sentinel is never
  re-read and the job finishes normally as `phase = finished` — the stop is
  silently ignored.** The committed data cannot be rolled back at this point.
- **S-I3 — Stop during the Fedora-metadata phase.** Identical to S-I2: not
  polled, runs to completion, deferred to the file phase or ignored. Data,
  history, and the Fedora updates done so far are committed.
- **S-I4 — Stop during the directory file-import phase.** Polled per file at
  `tasks.py:1324`/`:1329`; the next iteration sets `stopped`, writes
  `stopped_by_user`, and `break`s. Files already imported are **committed and not
  rolled back** — each file is written to Fedora and saved in its own
  `FedoraTransaction` closed with `mark_transaction_as_closed()` (`tasks.py:1495`),
  so a binary already in Fedora stays there. Remaining files are skipped; the
  `pending_related_metadata` sub-loop is skipped. Data/history/Fedora from the
  earlier phases are committed. Outcome: `phase = stopped`, **partial file import
  persisted**. This is inherent — Fedora binary writes are not transactional — and
  is accepted.
- **S-I5 — Stop during the `pending_related_metadata` sub-loop
  (`tasks.py:1521`).** Entered only for a file that already saved; the sub-loop
  itself does not poll, so it completes for the current file, and the sentinel is
  observed at the top of the next file (`tasks.py:1324`). Equivalent to S-I4.

### 13.5 Latency summary

| Stop clicked during | First honored at | Typical latency | Data left behind |
|---|---|---|---|
| `validating` | next row (`:2136`) | ~1 row | none (read-only) |
| data-record loop | next record (`:1007`) | ~1 record | **none — rolled back** |
| history phase | file phase or **never** | rest of history+Fedora, or whole job | data+history+Fedora **committed** |
| Fedora phase | file phase or **never** | rest of Fedora, or whole job | data+history+Fedora **committed** |
| file phase | next file (`:1329`) | ~1 file | data+history+Fedora + files-so-far **committed** |

The observed "~30 s before I could start a new import" corresponds to a stop
clicked while history/Fedora were running (S-I2/S-I3): the task had to grind
through the remaining history and Fedora work before the sentinel was seen at the
file phase (or the job simply ran to `finished`).

### 13.6 Worker-death scenarios (orthogonal to phase)

If the Celery worker is **killed** (SIGKILL, OOM, container restart, deploy)
after a job is running, the `finally` never executes:

- **S-D1 — killed during `importing`.** `phase` stays `importing`, the lock stays
  held (6 h TTL), the pointer stays set. The admin page keeps re-rendering the
  old job (`admin_sites.py:377`) and **no new import can start**. Recovery is
  **not available through the UI**: Stop only sets a sentinel a dead task will
  never read, and Cancel **rejects `importing` with 409**. The only remedies are
  a manual Redis cleanup (delete `import_data_lock`, `import_data_current_job_*`,
  `import_data_phase_*`) or waiting out the 6 h TTL. Any DB rows the data phase
  committed before the kill remain. **This is the incident reproduced earlier in
  this work and matches backlog `[REV-391] CELERY-05`.**
- **S-D2 — killed during `validating`.** `phase` stays `validating`, lock held.
  The only UI control is *Stop*, which just sets a sentinel a dead task will
  never read (Cancel is disabled in this phase — §2.5.3 — and would only set the
  same sentinel anyway), so the UI **cannot** free a job whose task is already
  dead. Same manual/TTL recovery. No DB writes were made (read-only), so nothing
  is committed.

### 13.7 Lock-loss, idempotency, and authorization edge cases

- **S-L1 — lock lost mid-import.** `refresh_import_lock` failing raises
  `ImportLockLostError` (`tasks.py:723`); it is caught at `tasks.py:1059`, sets
  the stop sentinel and `failed = True`. The exception unwinding the `atomic()`
  block **rolls back the data phase automatically**. `finally` sets `phase = failed`
  and releases the lock (a no-op token check if another holder took it). No orphan
  data from the data phase; files/history already committed in earlier phases (if
  any) remain.
- **S-X1 — repeated Stop clicks.** Setting the sentinel is idempotent (`= 1`).
- **S-X2 — Stop then Cancel while `importing`.** Cancel returns 409; the earlier
  Stop stands. Harmless.
- **S-X3 — ownership.** Both Stop (`views.py:2958`) and Cancel-as-stop
  (`views.py:3012`) require the requester to be the **owner** (superuser +
  `_check_import_ownership`). A non-owner superuser may only *force-cancel a stuck
  `awaiting_approval` job* (§7), **not** stop another admin's running import.

### 13.8 Consistency matrix (what remains after a stop)

| Stop during | Data records | History rows | Fedora metadata | Binary files | Net effect |
|---|---|---|---|---|---|
| `validating` | — | — | — | — | nothing written |
| data loop (S-I1) | **rolled back** | skipped | skipped | skipped | **clean abort**, Fedora deletions included |
| history (S-I2) | committed | committed | committed | deferred/none | **partial, unabortable** |
| Fedora (S-I3) | committed | committed | partial→full | deferred/none | **partial, unabortable** |
| file loop (S-I4) | committed | committed | committed | **partial** | **partial, unabortable** |
| worker kill (S-D1) | maybe committed | maybe | maybe | maybe | **wedged + partial** |

### 13.9 Known gaps and recommendations

1. **History/Fedora phases do not honor Stop (S-I2/S-I3).** A stop arriving in
   these phases is deferred to the file phase or **silently ignored** for
   file-less imports (the job ends `finished`). *Recommendation:* re-read the
   sentinel at the top of the history loop (`tasks.py:1108`) and the Fedora loop
   (`tasks.py:1192`) and `break` on it. Note this only stops *further* work — the
   data is already committed — so the resulting job is a legitimate
   `stopped`-with-partial state, which must be documented (or, if a true abort is
   required post-commit, the data+history phases would need to share one
   transaction, which files/Fedora cannot join).
2. **No UI recovery for a killed `importing`/`validating` job (S-D1/S-D2,
   CELERY-05).** *Recommendation:* implement a Celery `task_revoked`/SIGTERM
   handler that releases the lock and sets a terminal phase, **and/or** allow a
   superuser force-cancel to act on `importing`/`validating` (currently 409/no-op)
   by clearing the lock, pointer, and phase directly rather than relying on the
   dead task.
3. **DELETE-import Fedora rollback gap (S-I1 caveat) — implemented.** Fedora
   deletions are deferred to the post-commit phase via `transaction.on_commit`, so
   the database is the single commit point and a stopped or failed delete-import —
   including a failure of the database commit itself — leaves Fedora untouched.
   *Residual, accepted:* the opposite direction remains. Once the database has
   committed, an individual Fedora commit can still fail, leaving an object in Fedora
   that was meant to be deleted but no longer has a row in the database. It is not
   lost data (`FedoraRepositoryConnector.delete_binary_file` is a soft delete — a
   `dcterms:type 'deleted'` marker triple; the bytes stay) and it is recoverable. The
   commit loop does not abandon the remaining deletions on such a failure; each
   failure is logged (`cron.tasks.run_data_import.fedora_delete_commit.error`, with
   `ident_cely` / `repository_uuid` / `path`) and reported per record in
   `import_fedora_result_tr`, so an operator can finish the deletion. A durable outbox
   with an automatic retry task was judged disproportionate for this change.
4. **Reconcile the design narrative.** Update US-8 (§2.5.1) and the `importing`
   transition note (§3.1) to reflect the rollback-on-stop semantics now in effect
   for the data phase (§13.4 S-I1).