# Design

## Context

See `proposal.md` for motivation and scope. Design is needed because the pack spans
relational dependencies, external persistence, partial commits, substantial workloads
and a human/agent execution boundary.

### Inspected implementation and sources

- Local revision: `202cd7f0056e72ba44a745709df608d20133bc5b` on `test`.
- `webclient/core/import_data_mappers.py`: 46 registered CSV classes, 13 with UPDATE
  prohibited. The registry, rather than the old attachment's spellings, determines
  executable filenames for a matched deployment.
- `webclient/cron/tasks.py`: read-only domain validation, approval, a transactional DB
  data phase, later history/metadata phases, and a binary phase. Distribution/paradata
  writes group by parent record. These observations locate tests; they do not prove
  deployed behaviour or establish the required outcomes.
- `webclient/core/admin_sites.py`, `core/views.py` and
  `templates/admin/import_data/`: upload/start/stop/cancel/reset/report UI and ownership.
  XLSX reports have `Import` and `Fedora` sheets. Local code retains terminal Redis
  job data for six hours; persisted XLSX/report index retrieval must be distinguished
  from transient job state and verified against the deployed build.
- `locale/cs/LC_MESSAGES/django.po` and its English counterpart are the wording sources.
- The operator states test data is a production copy approximately one month old.
  Reference identities can be reused after preflight; newly changed source records
  and numeric keys must not be assumed to match across environments.
- Bounded reads on 2026-11-08 established that Digiarchiv test search and authenticated
  Fedora test reads work. `q` filters search; `query` was ignored. Some range filters
  returned broad matches, so required nested structures must be checked explicitly.
  An empty OAI payload is not evidence that a feature is absent.
- Example source candidates confirmed in Fedora test: `C-LD-000010777` has a flight,
  shapes and a component; `C-TX-198901775` has a review reference; `C-202604577A` has
  eight documentation units and ADB references; `M-N0100189` has a component/object
  find. These are seed candidates, not records approved for mutation.
- Pre-session review (2026-11-14): the last TEST deployment (2026-11-06) shipped tag
  `v2.0.0-alpha.2` (`3d4a4dd15e83c769eaa78235c985b326ae838a24`). Compared by Git blob,
  the pinned sources differ from the inspected commit only in
  `webclient/core/repository_connector.py` (ARUP-CAS/aiscr-webamcr#4493, Fedora
  commit-failure rollback) and the PO catalogs. The catalog difference is a reflow
  plus one entry the pack does not use. TEST therefore lacks #4493, which affects
  the `session.fedora-commit-failure` expectation. `test` HEAD `32d9a23b3` adds only
  a `dokument/forms.py` layout change and dependency bumps after the inspected commit.
  The deployed revision remains a preflight fact to confirm at session start.

## Goals / Non-Goals

**Goals:**

- Make completeness inspectable by an agent and a human, including niche paths.
- Generate executable, reproducible fixtures and independent expected outcomes.
- Minimize human effort through batching, late binding and automated comparisons.
- Support separate behaviour and load windows and repeatable post-fix sessions.
- Give every manual checkpoint an unambiguous evidence and handoff procedure.

**Non-Goals:**

- Change the importer, its requirements, PO catalogs or database schema.
- Automate browser actions, simulate human observations, or submit imports through
  backend endpoints as a substitute for human operation.
- Perform live imports, cleanup, infrastructure fault injection or writes to Fedora
  with the provided read-only account during pack preparation.
- Edit delivered workflows, add a shared skill, write to a sibling/hub, or publish data.

## Decisions

### 1. Local pack with separate immutable inputs and run evidence

All implementation files are repository-owned under
`.agents/testing/imports-391-3527/`; none are supplied by hub sync. Proposed layout:

```text
START-HERE.md
operator/
  behaviour.md
  load.md
  evidence.md
  terminology.json
definitions/
  coverage.json
  scenarios.json
  datasets.json
  expectations.json
  batches.json
  schemas/
tools/
  pack.py
  import_pack/
tests/
generated/
  behaviour/<namespace>/
  load/<workload>/<namespace>/
runs/
  behaviour/<run-id>/
  load/<run-id>/
```

The helper package is named `import_pack` so the repository-wide `lib/` ignore rule
does not hide it. Source delivery checks use the actual Git candidate list, including
source-only execution; portable ZIP export alone is insufficient.

Definitions, templates and generator/verifier code are reviewable sources. Generated
ZIPs/binaries and evidence remain local under the pack, with a pack-local ignore file
and a documented portable export. The export includes instructions, manifests,
checksums and ready inputs; raw run evidence is an explicitly selected separate bundle.
Do not silently include credentials or large evidence in a source commit. No git
operation is authorized by creating this planning change.

The CLI separates `inventory`, `discover`, `build`, `bind`, `verify`, `report` and
`handoff`. Builds from frozen inputs work offline. Read-only network operations are
explicit and bounded; no CLI command submits imports or changes application state.
Prefer existing Python dependencies and standard-library data/ZIP tooling; do not add
a browser driver. Pin deterministic ZIP ordering, timestamps, encoding and line endings.

Alternative: hand-maintained ZIPs and a narrative checklist. Rejected because coverage
drifts, generated keys change and a replacement agent cannot safely reconstruct state.

### 2. Inventory plus independent expectations

Capture registry names, operation permissions, keys, fields, defaults/nullability,
lookup families, uniqueness/check constraints, ownership branches and side-effect
targets. Use static source inspection without starting Django against unknown settings.
Reconcile with a recorded deployed revision and read-only schema/reference preflight.
Keep issue attachments as requirements/provenance inputs, including their differences
from actual mapper names; do not silently treat old spreadsheets as executable schemas.

Each coverage item has a stable ID, class/operation, variant, source requirement,
fixture rows, batch, expected DB/history/Fedora effects, human observation and evidence
requirements. Expected targets are independently authored from requirements and domain
relationships, then compared with the code's observed targeting. Ambiguities are
recorded as acceptance questions rather than silently resolved in favour of the code.

Baseline CSV coverage, grouped for review:

| Family | Registry keys |
|---|---|
| Vocabulary | `heslar`, `heslar_datace`, `heslar_dokument_typ_material`, `heslar_hierarchie`, `heslar_odkazy` |
| Organisations/persons | `organizace`, `osoby` |
| Projects | `projekty`, `projekty_katastry`, `projekty_oznamovatele` |
| Individual finds | `samostatne_nalezy` |
| Fieldwork events, Sites and spatial documentation | `az_akce`, `az_lokality`, `az_akce_vedouci`, `az_katastry`, `az_pian`, `az_dokumentacni_jednotky`, `az_adb`, `az_adb_vyskove_body` |
| Documents | `dokumenty_lety`, `dokumenty`, `dokumenty_autori`, `dokumenty_jazyky`, `dokumenty_osoby`, `dokumenty_posudky`, `dokumenty_tvary`, `dokumenty_casti`, `dokumenty_neident_akce`, `dokumenty_neident_akce_vedouci` |
| Components/finds | `komponenty`, `komponenty_aktivity`, `komponenty_nalezy_objekty`, `komponenty_nalezy_predmety` |
| External sources | `externi_zdroje`, `externi_zdroje_autori`, `externi_zdroje_editori`, `externi_odkazy` |
| Users | `uzivatele`, `uzivatele_notifikace_projekty`, `uzivatele_spoluprace`, `uzivatele_opravneni`, `uzivatele_notifikace` |
| Binaries | `soubory`, `distribution`, `paradata` |
| History | `historie` |

At this revision the prohibited UPDATE list is `projekty_katastry`, `az_katastry`,
`dokumenty_autori`, `dokumenty_jazyky`, `dokumenty_osoby`, `dokumenty_posudky`,
`dokumenty_neident_akce_vedouci`, `komponenty_aktivity`, `externi_zdroje_autori`,
`externi_zdroje_editori`, `uzivatele_notifikace_projekty`, `uzivatele_opravneni` and
`uzivatele_notifikace`. This yields 125 permitted cells plus 13 required rejections.

Each family adds cases for its own FK targets, constraints and special branches:

- Multi-model Fieldwork event/Site/document imports; wrong subtypes and missing
  companion rows; optional document extra data; partial versus full updates.
- Project-linked and independent Fieldwork events; mutually exclusive document-part
  relationships; unidentified fieldwork and its managers; both component owners.
- Spatial units and geometry-bearing imports in 4326/5514, supported geometry types,
  source/derived consistency, empty/omitted columns, malformed geometry and elevation.
- Cadastral documentation units with existing/missing automatic spatial units;
  correct reuse and no orphan or duplicate derived objects after rejection/failure.
- Hierarchies, cycles, forward references, wrong vocabulary families and duplicate
  relations; prefixed numeric keys, natural keys, composite keys and FK-as-key imports.
- All three RUIAN owner types; users, cooperation peers, permissions, notifications;
  protected current-user deletion; history ownership for every supported owner.
- Child changes and FK reassignment with assertions for both former/new parents,
  sibling controls, deduplicated `IMP` history and metadata freshness.
- CSV quoting, newlines, Unicode, BOM/encoding, duplicate headers/rows/keys, empty input,
  unknown files, malformed archive, field overflow and supported/invalid bool/date forms.
- Files for document/project/Individual find: insertion, replacement, deletion,
  filename/path, detected metadata, checksums, thumbnails and synthetic EXIF GPS removal.
- Distribution/paradata lifecycle, MIME/name preservation, reserved/unsafe names,
  prefix collisions, missing sources, existence checks, nested paths, tombstones,
  same-record grouping, multiple files, `DIST*` history, UI downloads/permissions,
  thumbnail history/backfill and idempotent backfill verification.
- Validation purity, ownership/maintenance gates, concurrent admin attempts, approval
  cancellation, phase-specific stop/failure/recovery and report consistency.

Actual branch coverage is explicit per class/relationship, not a claim that all possible
input combinations can be exhausted. Shared field boundary cases can share fixtures
only when their mapper-specific persistence/constraint outcomes remain checked.

### 3. Structural discovery followed by synthetic graph construction

Use Digiarchiv test first to find feature-rich records; production OAI supplies
additional structures when needed. Follow OAI resumption tokens within a bounded
selection, ignore inaccessible payloads as seeds, and fetch selected Fedora XML to
confirm relationships. Retain identifiers, source/version hashes and sanitized structure
recipes, not a wholesale production harvest or copied personal details.

Freeze reference identifiers and validate them against test. Generate synthetic people,
organisations, notifier/user details and known-content binaries. Keep existing reference
tables unchanged. Vocabulary mutation tests use synthetic entries under verified
vocabulary types; broad shared vocabulary edits are not setup. Check unused valid IDs
before execution and never assume a production numeric PK equals the test PK.

Construct parallel graphs for explicit child deletion, parent cascades, FK movement,
failure and unaffected controls. The build emits logical-key-to-CSV-key mappings.
After numeric IDs/file paths are allocated, `bind` consumes reports/query exports to
produce later packs; source identity, report keys and DB results must agree.

Provide synthetic missing-state recipes where a branch cannot be prepared through
ordinary imports. A recipe requiring controlled fixture setup, history removal or
infrastructure changes is clearly separate and remains blocked until authorized.

### 4. Batch by operation and dependency, not one upload per assertion

Each ZIP carries a single selected operation. Foundation, domain graph, file and
distribution/paradata stages are sequenced as needed for references and generated keys.
Full UPDATE and partial UPDATE cannot share a table header when omitted-column
semantics are under test, so they use separate packs. Explicit child deletions are
partitioned by dependency depth; root cascades operate on a parallel graph.

Combine independent row-level validation errors that the validator can enumerate.
Keep archive/parser, unsupported-file and batch-order errors separate when they prevent
later rows being visited. The ledger records which error caused the outcome so that
one error cannot pass multiple unrelated checks. Planned coverage cannot substitute for
observed execution. The generated batch manifest shows the number of uploads and which
assertions each upload covers, allowing review of operator effort before execution.

Alternative: one giant successful/invalid ZIP or hundreds of independent manual cases.
Rejected because the first conceals dependencies/failures and the second shifts
mechanical work onto the operator.

### 5. Behaviour and load are independent sessions

`operator/behaviour.md` covers exhaustive class/branch semantics, deliberately bounded
inputs, negative outcomes, UX, recovery and integrity. It never invokes load batches.

`operator/load.md` covers separately approved windows, baseline capacity, test-data
namespace, monitoring availability, phase durations, throughput, polling/report sizes,
human-observed responsiveness and outcome reconciliation. It offers two independent
workloads with their own setup:

- Relational: 10,000 projects, 10,000 linked Fieldwork events, 10,000 documentation
  units, 10,000 components and 10,000 finds: 50,000 rows. Use verified reusable spatial
  and vocabulary references so setup is deterministic. Distinct parent count and
  expected metadata targets are part of the workload manifest.
- Distributions/paradata: prepare 10,000 synthetic files under 5,000 parent records,
  each file receiving two distributions and two paradata objects: 20,000 distribution
  rows plus 20,000 paradata rows. Setup and measured inputs are separate; record files,
  bytes, parent groups, expected writes and transaction/version evidence.

Both are real import workloads; neither is replaced by repeatedly calling validation.
Preflight reports expanded ZIP size against the local 1 GiB guard and confirms deployed
limits. Correctness uses complete machine comparisons, not sampled count-only checks.
Human checks focus on workflow responsiveness and observability. Resource metrics
require separately available access; missing metrics stay unmeasured. No universal
duration threshold is invented before the operator's window/budget is recorded.

Alternative: embed a large run at the end of behaviour testing. Rejected because the
operator's time window, state, monitoring needs and recovery budget differ.

### 6. Terminology comes from PO entries

`operator/terminology.json` records CSV/domain identifier, message key, exact Czech and
English translation and catalog hash. Examples already checked:

| Identifier/context | Czech | English | PO message key |
|---|---|---|---|
| `az_akce` UI | Akce | Fieldwork events | `arch_z.views.AkceListView.toolbar_name.text` |
| `az_lokality` UI | Lokality | Sites | `templates.baseLogedIn.sidebar.lokality` |
| `az_pian` | PIAN | Spatial unit | `mapa.pian` |
| `az_adb` | Archeologický dokumentační bod | Archaeological documentation point | `vypis.adb.adb.section_name` |
| Elevation | Výškové body | Elevation points | `vypis.adb.vb.label` |
| Unidentified | Neidentifikovaná akce | Unidentified fieldwork | `dokument.filters.dokumentFilter.existNeidentAkce.label` |
| Start | Zahájit import | Start importing | `core.templates.admin.import_data.start_import` |
| Stop | Zastavit úlohu | Stop task | `core.templates.admin.import_data.stop_request` |
| Cancel | Zrušit import | Cancel import | `core.templates.admin.import_data.cancel_release_lock` |
| Download | Stáhnout log importu | Download import log | `core.templates.admin.import_data.download_report` |
| Report list | Reporty hromadného importu | Bulk import reports | `core.templates.admin.import_reports.heading` |

Use context-specific labels rather than inventing a single translation when the PO
catalog has several. Operator instruction cards quote the Czech UI and give a technical
CSV identifier where relevant. No translations are changed as part of this pack.

### 7. Responsibility split and instruction cards

| Work | Owner |
|---|---|
| Discover seeds, synthesize data, validate manifests, build/bind ZIPs | Agent |
| Generate links/SQL, fetch authorized metadata, compare evidence, produce reports | Agent |
| Upload ZIP, select operation, start/stop/cancel/reset through the UI | Human |
| Capture live labels/progress/errors/download controls, permissions and responsiveness | Human |
| Inspect supplied screenshots and reports; extract visible results | Agent |
| Run read-only SQL where agent lacks access; save required export | Human fallback |
| Place binary inputs on the configured import volume | Authorized agent transfer when available; otherwise exact human instructions |
| Change maintenance/infrastructure or execute cleanup | Explicitly authorized operation, assigned in that session |

An instruction card is rendered only after paths/namespace/batch are resolved. It gives:
the purpose; prerequisites; exact full input path and checksum; selected operation;
quoted control labels; expected states; what to observe visually; wait/stop conditions;
files to retain and exact destinations; the next message to give the agent. Present one
action/checkpoint at a time. Human browser actions cannot be replaced with HTTP POSTs,
GUI automation or browser tooling. Authenticated direct reads are allowed for the
verification routes already authorized, not for obtaining missing human observations.

### 8. Evidence lives in the run directory and stays accessible

Bind each run to an absolute workspace directory, for example:
`D:\David\Git\aiscr-webamcr\.agents\testing\imports-391-3527\runs\behaviour\<run-id>\`.
Record root relocation in the session manifest. Each batch retains:

```text
<batch-id>/
  instruction.md
  input-manifest.json
  baseline/                 # agent captures before the human acts
  validation-report.xlsx    # human download, agent hashes and reads
  final-report.xlsx         # human download after a terminal state
  ui-validation.png         # only where visual observation is required
  ui-final.png
  operator-observations.json
  db-after.json
  fedora-after/              # direct metadata, statuses and hashes
  verification.json
```

Do not require screenshots for every row; collect them at representative UX transitions
and every unexpected error. Record exact messages/states and observation times where
timing matters. Load runs additionally retain `timings.json`, monitoring exports if
available, and complete count/integrity results. Raw report downloads stay intact;
normalization produces separate files. Immutable ingestion uses
`<batch>/originals/<kind>/<sha256><suffix>`, so validation, terminal and later task
reports keep distinct checkpoint references without overwriting originals. Before providing real-data excerpts to an agent,
local tooling extracts required synthetic-record fields and redacts unrelated details.

The human download procedure names both routes: current task's `Stáhnout log importu`,
or the matching task ID in `Reporty hromadného importu`. Keep each stage's download as a
separate named file. `Report uložen` shows a server/container path; record it for
diagnosis, but do not imply it is a workstation file or a clickable download. Capture
the final XLSX promptly rather than relying on transient Redis state.

If SQL is unavailable to the agent, give the human one ready-to-run read-only script,
the exact export format/encoding and full destination. On the shared workstation the
human places downloads in the run directory and supplies that directory path; an agent
then reads them locally. On another machine the human attaches the listed evidence
bundle or copies it into an agent-readable opened workspace. A browser download-folder
path or remote server path alone is not sufficient handoff evidence.

At each checkpoint the agent hashes inputs/evidence, updates append-only event history
and the current session state, and renders a ready-to-paste continuation message naming
suite, run ID, batch ID, task ID and evidence root. A fresh agent reads `START-HERE.md`
and that run's manifest/checkpoint before doing anything. Existing mutation steps are
not repeated because a chat session was lost.

Retain generator revision, sanitized source recipes, input hashes, reports, observations,
baseline/result snapshots, mappings, failures and recovery records through final review
and all related reruns. Keep synthetic volume inputs until their dependent runs/recovery
are finished. Dataset cleanup does not delete evidence; evidence deletion is a separate
explicit retention decision. No default arbitrary expiry is imposed on retained evidence.

### 9. Read-only verification, recovery and reporting

SQL preflight/export scripts use read-only transactions and scoped SELECTs. Prefer
direct authorized agent execution; otherwise consume operator exports. Check expected
values, omitted-field preservation, FK resolution, uniqueness, geometry/SRIDs, owner
links, orphans, history multiplicity/actor/notes and unaffected controls, not just totals.
No schema changes, temporary setup tables or persistent helper functions are required.

Generate Fedora links from actual stored `soubor.path`, including cases without a
leading slash. Import key `soub-<numeric id>` is not a repository UUID. Produce search,
metadata, binary, distribution/paradata and version URLs without credentials. Page through
search results and compare direct resource status/content; index lag is not persistence
failure. Separate expected metadata XML changes from repository resource versions.

Failures are classified by validation, DB data transaction, history, metadata, binary
and record-group boundaries. Stop tests record whether data rolled back or earlier work
committed. Do not promise global atomicity across PostgreSQL/Fedora. Include failure
around commit boundaries in the scenario ledger. Infrastructure-dependent injections
remain blocked without an approved method; local simulations are reported separately.

Recovery uses reconciled DB/Fedora/report results to build remaining operations; never
blindly replay the original INSERT input. Cleanup identifies exact run-owned IDs, paths
and dependencies and requires separate authorization. Do not delete copied production
records or reset shared vocabularies. New runs normally use fresh namespaces; preserved
Fedora history/tombstones mean cleanup is not a byte-identical baseline restoration.

Reports show class/operation/branch coverage, expected versus actual effects, human UX
observations, evidence links and prepared/passed/failed/blocked/unexecuted/inapplicable
states. Inapplicability needs an explicit reason and cannot hide mandatory branches.
Behaviour and load verdicts remain separate; no completeness claim with missing
mandatory evidence or unverified deployment identity. Load reduction requires the
retained run directory, matching suite/workload/namespace/deployment identities, the
selected manifest/input hashes and a checked terminal checkpoint for the measured
task. Its required original evidence and normalized load-results must be retained
with matching hashes and current acquisition provenance; an unbound or stale summary
cannot yield a verified verdict.

### 10. Known source defects defer checks instead of masking batches

Source review of the inspected commit, which matches `v2.0.0-alpha.2` for this file,
confirms two defects in `VazbaLookupImportField._process_value` in
`webclient/core/import_data_mappers.py`. This is the owner-reference field used by the
Komponenta (`komponenty`), Soubor (`soubory`) and Historie (`historie`) mappers.

1. The fallback for an owner that `get_record_from_ident` does not return iterates
   `self.records`. The field exposes only the class method `get_records()`, so this
   raises `AttributeError`.
2. Even after (1) is corrected, the fallback assigns `filtered_records[0].historie`
   regardless of `read_field_name`, so component and file owners would receive the
   wrong object.

The fallback is reached when the owner value:

- names a parent created in the same import (not yet persisted);
- has no identifier pattern in `get_record_from_ident` (cooperation and file owners
  referenced by numeric ID);
- resolves to a model without the read attribute (`User` exposes `history_vazba`,
  not `historie`);
- does not exist at all. The intended `ImportDataMissingReferencedValueError` is
  never raised.

Empty owner values become `None` and take the required-field path instead.

`run_data_import` catches only `ImportData*` errors per row. The `AttributeError`
reaches the outer `except Exception` and fails the whole validation job with
`core.admin.import_data.error.unexpected_error`, so one triggering row conceals every
other check in its ZIP.

Affected prepared inputs (delivery r3):

| Input | Triggering rows | Deferred coverage |
| --- | --- | --- |
| `N07-field-boundaries` | three `MISSING-REFERENCE-*` owner rows | `historie.field.vazba.missing-lookup`, `komponenty.field.vazba.missing-lookup`, `soubory.field.vazba.missing-lookup` |
| `V17-branches-update` | user owner | `historie.branch.user-owner` |
| `V18-branches-update` | cooperation owner | `historie.branch.cooperation-owner` |
| `V19-branches-update` | file owner | `historie.branch.file-owner` |
| `L01-relational-50000` | 10,000 components owned by same-import units | combined relational load verdict |

Batches whose owners are persisted beforehand and resolve with the read attribute are
unaffected: B02b, B03, B05, B06, V00b, V01, V05, V06, F01, Q15/Q16, R14 and the
distribution load (`L01-files` references documents created by `L00-parents`).

Handling, without fixing the application:

- A frozen known-defects definition records each defect: source path and lines,
  source hash, trigger conditions, affected coverage IDs and batches, and its
  prerequisite (`fix deployed`). Affected items use the existing `blocked` state with
  that prerequisite. No new execution state is introduced.
- The three N07 rows move to a separate deferred negative batch. N07 stays executable
  for its remaining checks. V17–V19 become deferred batches. Card rendering skips a
  deferred batch until a run records its prerequisite as met against a deployment
  containing the fix.
- Relational load uses a two-import substitute: `L01a` (10,000 projects, 10,000
  Fieldwork events, 10,000 documentation units: 30,000 rows) then `L01b` (10,000
  components, 10,000 finds: 20,000 rows). Both are measured and reported as a
  substitute. Find-to-component references use the working `get_records()` lookup.
  `L01-relational-50000` stays prepared and blocked, and is never reported as measured.
- Reports carry a known-defects section labelled source-confirmed. Source analysis
  and the isolated probe in `definitions/source-probes.json` are not live failures.
  A live observation, if one occurs, is recorded separately as usual.

Alternatives considered: fixing the importer was rejected because the developer will
correct it separately. Leaving the rows in place was rejected because it would abort
N07 and hide about 362 unrelated negative checks. Dropping the coverage was rejected
because the checks must remain ready for a rerun after the fix.

### 11. Portable source identity and deployment parity

Pinned `source_hashes` were computed from working-tree bytes. With
`core.autocrlf=true` these are CRLF files, so a Git blob, a Linux checkout or deployed
source reported every pinned file as drifted. Source and generator identity uses
content with line endings normalised to LF, so the same Git content yields the same
hash on every checkout. Binary fixtures keep raw-byte hashes.

Deployment identity is no longer exact commit equality, which a tag-based deployment
can never satisfy. Preflight records the verified deployed commit and compares each
pinned file's normalised content at that commit (from `git show` or an exported
listing). Every file equal means `source-equivalent`, recording both commits. Any
difference withholds the dependent coverage and requires a refreshed inventory, as
before. Report and `load-analyse` accept a `source-equivalent` deployment recorded in
the run. An unknown deployment still blocks.

## Risks / Trade-offs

- Source and deployment drift -> pin identities and rerun preflight; preserve unresolved
  deployment identity instead of treating a local checkout as hosted proof.
- Known importer defect hides unrelated checks -> isolate triggering rows into deferred
  batches, keep their items blocked with a named prerequisite, and report the defect
  as source-confirmed. The substitute load figure is not the combined-import figure.
- Exhaustive classes with a small upload budget -> combine compatible cases, publish
  the actual batch count, and preserve independent execution evidence for every check.
- Rare state needs privileged setup -> generate an exact setup recipe and mark the
  affected case blocked until authorized; do not silently omit it.
- Large imports occupy a shared test service -> separate windows, namespaces, capacity
  checks and recovery budgets; preparation does not submit either workload.
- Copied personal data or transient credentials -> synthesize details, minimize source
  retention, extract/redact before agent context and keep secrets out of disk artifacts.
- Operator loses chat/browser state -> checkpoint files, durable downloaded reports and
  explicit local evidence paths support a fresh agent without replaying mutations.

## Migration Plan

1. Review these planning artifacts; obtain implementation approval separately.
2. Implement local pack sources and validate generation/verifiers offline with meaningful
   positive/negative controls. Review the emitted full coverage and batch manifests.
3. Preflight the deployed test build and produce portable, ready inputs plus exact
   run instructions; unknown instance-specific settings are late-bound, not guessed.
4. Conduct behaviour and load sessions only in their individually authorized windows,
   preserving evidence and human browser ownership. Findings can produce separately
   authorized application fixes; this change does not perform them.
5. No hub sync is needed. If delivery is proposed later, first obtain its own scope and
   approval, inspect a sync dry run, then obtain the required sync-apply approval.

Instance-specific deployment commit, import-volume path, agent DB read access, operator
accounts and load windows are preflight inputs. Their values can be supplied later
without changing the contract or architecture; absent values block only dependent work.
