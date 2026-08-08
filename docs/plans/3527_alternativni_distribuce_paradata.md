# Plan — Issue #3527: ATRIUM — rozšíření importu o alternativní distribuce a paradata

**Branch:** `feat/3527` · **Milestone:** v2.0.0 · **Parent feature:** hromadný import (#391)

## 1. Goal

Extend the bulk import (#391) with two new capabilities that operate on **existing** `Soubor`
records and their Fedora binary containers:

1. **Alternative distributions** — upload/replace/delete additional renditions of a file
   (e.g. `ocr/alto-xml`) stored as extra Fedora containers alongside `orig`. Recorded in file
   history and reflected in record metadata.
2. **Paradata** — upload/replace/delete paradata attached to a chosen distribution, stored as a
   Fedora sub-container. **Pure Fedora operation** — no DB row and no metadata XML change.

Plus supporting work: file-history change types, thumbnail-history integration + backfill script,
and a distribution picker in the file-table UI with permission-checked download.

## 2. Key facts about the current system (verified in code)

- **Import is two Celery tasks** in `webclient/cron/tasks.py`:
  `run_data_import_validation` (read-only validation, lines ~993–1132) and `run_data_import`
  (actual import). Input = a ZIP of CSVs uploaded in admin; **binary files come from a
  configured directory** `import_directory_settings.DIRECTORY_PATH` (read at tasks.py:1978).
- **CSV → mapper** registry: `@ImportModelMapper.register("<file_key>")` in
  `webclient/core/import_data_mappers.py`. `soubory.csv` → `SouborMapper` (line 4657). The
  validation loop discovers CSVs from the ZIP and dispatches by file key (tasks.py:998–1041).
- **Binary-file import loop** (tasks.py ~2012–2235): iterates `import_files_list` (list of
  `Soubor` produced during validation), reads the real file from `DIRECTORY_PATH`, detects mime,
  calls `conn.save_binary_file()` / `conn.update_binary_file()`, writes
  `Historie(typ_zmeny=IMPORT, …)`, then flushes record metadata via `obj.save_metadata()`.
- **Fedora connector** `webclient/core/repository_connector.py`:
  - `save_binary_file(file_name, content_type, file, save_thumbs)` creates
    `/record/{ident}/file/{uuid}` with content under **Slug `orig`**, then `save_thumbs()`
    writes Slug `thumb` and `thumb-large`.
  - URLs built centrally in `_get_request_url(FedoraRequestType, *, uuid, ident_cely)`
    (line 365); HTTP via `_send_request` (line 567).
  - `Overwrite-Tombstone: true` header already used in `record_deletion` when
    `self.override_tombstone` is set (line 1857). Same mechanism must be reused for
    distribution/paradata INSERTs.
- **`Soubor`** (`webclient/core/models.py:161`): `path` = Fedora URL, `repository_uuid` property
  parses uuid from path; `mimetype`, `sha_512`, `size_mb`, `rozsah`.
- **History** `webclient/historie/models.py:71` — `typ_zmeny` is `TextField(choices=CHOICES)`.
  New codes must be added to `CHOICES` (needs a schema-neutral `makemigrations` run) and to
  `webclient/core/constants.py` (existing file codes: `NAHRANI_SBR="SBR0"`, `PREJMENOVANI_SBR="SBR1"`).
- **UI**: `webclient/core/templates/core/filetable.html:54` renders the download link
  (`core:download_file`). Download served by `DownloadFile` view (`core/views.py:513`) via
  `soubor.content_file_response`. Permission gate = `check_soubor_vazba` + `LoginRequiredMixin`.
- `ADMIN_USER` available via `hesla_dynamicka.ADMIN_USER` (already used in tasks.py:530).

## 3. Work packages

### WP1 — History change-type constants
- Add to `webclient/core/constants.py`: `DISTRIBUCE_VLOZENI = "DIST01"`,
  `DISTRIBUCE_UPDATE = "DIST11"`, `DISTRIBUCE_SMAZANI = "DIST10"` (names TBD — match Czech naming
  convention of neighbouring constants).
- Add the three to `Historie.CHOICES` in `webclient/historie/models.py` with new translation keys.
- Run `makemigrations historie` → schema-neutral `AlterField` migration (allowed; choices change).

### WP2 — Fedora connector: generic distribution & paradata containers
Add methods to `FedoraRepositoryConnector` mirroring `save_binary_file`/`update_binary_file`/delete,
but parameterised by container path:
- `save_distribution(uuid, distribution, file_name, content_type, file)` → writes to
  `record/{ident}/file/{uuid}/{distribution}` (supports nested names like `ocr/alto-xml`).
- `save_paradata(uuid, distribution, file_name, content_type, file)` → writes to
  `record/{ident}/file/{uuid}/paradata/{distribution}`.
- Update + delete variants for each.
- **All INSERT writes send `Overwrite-Tombstone: true`** (reuse existing header logic — a tombstone
  may exist from a prior delete cycle; ref fcrepo PR #2044).
- New `FedoraRequestType` enum members + `_get_request_url` branches for these container URLs.
- **Reserved-name guard** (raise error): distribution == `orig`, `paradata`, `thumb/page`, or
  anything under `thumb/page/*`. (`thumb` and `thumb-large` themselves remain writable.)
  Put the guard in a shared validator used by both the mapper (validation phase) and the connector.

### WP3 — `distribution.csv` mapper (`DistribuceMapper`)
- Register `@ImportModelMapper.register("distribution")`. Columns: `id` (`soub-NNNN`), `nazev`,
  `mimetype`, `distribution`.
- Validation (`import_validation`):
  - parent `Soubor` (by `id`) must exist;
  - reserved-name guard (WP2);
  - existence check against file history: INSERT → error if the distribution **already exists**;
    UPDATE/DELETE → error if it **does not exist**. "Exists" = there is a `DIST01` for this
    `soubor` whose `poznamka == distribution` with **no younger `DIST10`** of the same `poznamka`
    (this rule also drives the UI in WP6 — implement once, reuse).
- Because the binary content lives in `DIRECTORY_PATH` (like `soubory`), the actual Fedora write
  happens in the import task, not the mapper (mappers are DB/IO-free — see class contract at
  import_data_mappers.py:1316). Mapper's job = validate + carry the row into a distribution
  work-list.
- On import (WP5): write/replace/delete the Fedora container (WP2), then write
  `Historie(typ_zmeny=DIST01/DIST11/DIST10, uzivatel=ADMIN_USER, datum_zmeny=now(),
  poznamka=distribution, vazba=soubor.historie)` and refresh record metadata (incl. Fedora).

### WP4 — `paradata.csv` handler (`ParadataMapper` / dedicated path)
- Columns: `path` (`soubor.path`), `nazev`, `mimetype`, `distribution`.
- **No DB row, no history, no metadata XML change** — pure Fedora. This does **not** fit the
  DB-model mapper contract, so it needs a light-touch integration (see Open Questions Q1).
  Recommended: a minimal mapper that only validates (locate `Soubor` by `path`; the referenced
  `distribution` must exist per WP3 existence rule) and enqueues a paradata work-item; the task
  performs the Fedora write to `…/file/{uuid}/paradata/{distribution}` with `Overwrite-Tombstone`.
- INSERT/UPDATE/DELETE semantics as in the issue.

### WP5 — Import-task integration (`webclient/cron/tasks.py`)
- Add distribution and paradata processing to the binary-file phase (after the existing `soubory`
  loop, reusing `DIRECTORY_PATH`, mime detection, antivirus, stop/lock cadence, Redis progress
  reporting, and per-item `FedoraTransaction` handling).
- Add validation-phase wiring so the new CSV keys are recognised (they already flow through the
  generic `allowed_file_names` / mapper dispatch once registered).
- Ensure rollback on failure mirrors the existing `soubory` error handling
  (`fedora_transaction.rollback_transaction()` + Redis failure markers).

### WP6 — File-table UI: distribution picker + download
- `webclient/core/templates/core/filetable.html`: before the download icon, render a dropdown of
  available distributions for the file (default `orig`), computed by the WP3 "exists" query
  (DIST01 without a younger DIST10 of the same poznamka). Add `thumb`/`thumb-large` handling per
  the file-API rules if in scope for display.
- Extend the download view (`DownloadFile` in `core/views.py`) / add a route to accept a
  `distribution` argument and stream that Fedora container. **Same permission gate as the normal
  download** (`check_soubor_vazba` + login).
- Add a `Soubor` helper (e.g. `available_distributions()`) so template and view share one source
  of truth.

### WP7 — Thumbnail history
- In `save_thumbs` (repository_connector.py:1265) add `DIST01` history insertion per generated
  thumb (`thumb`, `thumb-large`) following the WP3 procedure. Confirm poznamka value (Q3).
- **Backfill management command** (`webclient/<app>/management/commands/…`): iterate all `Soubor`;
  for each, query Fedora `fcr:versions` of `thumb` and `thumb-large` (same approach as #975); insert
  `DIST01` for the earliest version timestamp and `DIST11` for each later timestamp, per container.

### WP8 — Tests
- Mapper unit tests for `DistribuceMapper` (and `ParadataMapper`) per
  `.agents/prompts/` mapper-test procedure (see memory `[[reference-mapper-unit-tests]]`).
- `run_data_import` integration tests per `[[reference-run-data-import-tests]]` — 12-test matrix,
  Fedora/Redis/signal patches, INSERT/UPDATE/DELETE column-structure rules.
- Connector tests for reserved-name rejection and `Overwrite-Tombstone` header.
- UI/view test for permission-gated distribution download.
- **All tests run via Docker** (memory `[[feedback-docker-tests]]`), not local venv.
- Compile check + `pre-commit run --all-files`. Docstrings in Czech, comments in English,
  no f-strings around `_()`.

## 4. Suggested implementation order
WP1 → WP2 → WP3 → WP5(distribution) → WP4 → WP5(paradata) → WP7 → WP6 → WP8 (tests alongside each WP).

## 5. Open questions (need product/tech confirmation before/at coding time)

- **Q1 (RESOLVED):** Paradata is integrated via a minimal **validate-only mapper + dedicated task
  loop** (Option A) — keeps CSV discovery/dispatch/progress/error handling uniform with other imports.
- **Q2:** Do distribution/paradata binaries come from the same `DIRECTORY_PATH` as `soubory`?
  (Issue wording "skutečný celý název ve složce pro import" implies yes — assumed yes.)
- **Q3:** Exact `poznamka` values for thumbnail history entries — literal `thumb` / `thumb-large`?
- **Q4:** Nested distribution containers (`ocr/alto-xml`) — confirm the Fedora version in use
  auto-creates intermediate containers, or whether we must create them explicitly.
- **Q5:** Should UPDATE of a distribution create Fedora versions (like `orig` update) or overwrite?
  Issue history code `DIST11` implies versioned update.
