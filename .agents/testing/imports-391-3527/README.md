# Bulk-import verification pack

Repository-local pack for ARUP-CAS/aiscr-webamcr#391 and
ARUP-CAS/aiscr-webamcr#3527. Start with [START-HERE.md](START-HERE.md), then select
the behaviour or independent load runbook. The human operates the browser; the agent
prepares, binds, reads, compares and reports.

The prepared ledger contains **747 checks**: 138 class/operation cells across all
46 CSV classes, 210 named branches, 368 field probes, 10 archive/parser cases and
21 session cases. The main behaviour material has **84 CSV upload inputs and two
controlled management procedures**. **80 inputs are executable now. Four are deferred**
because a source-confirmed importer defect would abort them (see below). Sixteen CSV
inputs and both procedures need controlled setup or an acceptance decision. Twenty
further session scenarios are described separately; thumbnail backfill already has
its procedure card. Isolated follow-up inputs are used only when an earlier error
concealed a check.

| Independent suite | Prepared measured workload |
| --- | --- |
| Behaviour | All classes, allowed/prohibited operations, complex ownership, geometry, files, history, failure/recovery and human UX |
| Relational load | 50,000 rows: 10,000 each of projects, Fieldwork events, documentation units, components and finds. While the defect is unfixed: a two-import substitute of 30,000 + 20,000 rows |
| Distribution/paradata load | 20,000 distributions + 20,000 paradata, across 10,000 files and 5,000 parents; setup outside measurement |

**Known importer defect.** `VazbaLookupImportField._process_value` fails the whole
validation job for owners it cannot resolve. It is reported for the developer, not
fixed here. Its six checks are deferred in `N07x-deferred-known-defects` and
`V17`–`V19`. They stay in coverage as `blocked`, get no card, and every report lists
them in a source-confirmed `known_defects` section. The combined 50,000-row relational
import is deferred too, and measured meanwhile as `L01a` + `L01b`. Details and the
post-fix procedure are in `operator/known-source-risks.md` and
`definitions/known-defects.json`.

**Deployment identity.** The test instance runs release tags. `deployment-parity`
accepts a deployed commit whose pinned sources match by line-ending-normalised content.
A difference is accepted only with a review that names the coverage it withholds.
`v2.0.0-alpha.2` differs only in `repository_connector.py` (#4493). See
`operator/agent-checks.md`.

The distribution source pool contains 40,000 synthetic files, supplied as one
checksum-verified `binary-sources.zip`. Payloads are deliberately small; this measures
operation/metadata load rather than multi-GB transfer throughput.

Read [known source risks](operator/known-source-risks.md) before execution. Materials
and simulations do not establish deployed behaviour. Deployment revision, current
schema/reference exports, operator/access facts, import/report paths and each load
window must be verified before their dependent steps. `.template.zip` is never an
uploadable input. A source copy of production does not establish numeric-key parity.

The run namespace starts with 9; ordinary spatial-unit identifiers use the corresponding
8xxxxx sequence and actual ZM50 prefix, because 9xxxxx is reserved for cadastral precision.
Unused identifiers are verified on the test DB before setup. PO-backed field/error/status
translations are available offline in `definitions/import-messages.json`.

Source inventory does not import Django, read private settings or connect to a DB:

```powershell
.venv/Scripts/python.exe .agents/testing/imports-391-3527/tools/pack.py inventory
```

`definitions/` holds frozen, reviewed inputs. `generated/`, `runs/` and `exports/`
are local outputs excluded from source control. Keep run evidence until its explicit
retention decision; deleting synthetic application data does not delete evidence.

Coverage states: `prepared` means material exists, `passed` requires current execution
evidence, `failed` is an observed contradiction, `blocked` needs a missing prerequisite,
`unexecuted` has no execution yet, and `inapplicable` requires a recorded reason.
Simulation and historical evidence cannot produce a live pass.

The local delivery datasets are under `generated/delivery-2026-11-14-r4/`. The
superseded preparation iterations (r1–r3 and the earlier generated sets), the
2026-11-09 export bundles and the simulated offline rehearsal run were deleted on
2026-11-14 by operator decision. None of them was live session evidence.
`export-all` creates one portable bundle with `prepared/behaviour/`,
`prepared/load-relational/` and `prepared/load-distributions/`. It contains frozen
definitions, generator/source hashes, SQL, fixtures and instructions, with no run
evidence or credentials. Load source files are archived once rather than duplicated
as 40,000 loose entries in the outer bundle.

For source-checkout verification run:

```powershell
.venv/Scripts/python.exe -m unittest discover -s .agents/testing/imports-391-3527/tests -v
```

Offline checks include full-size generation, deterministic regeneration, actual XLSX
parsing/key binding, SQL/model key agreement, altered geometry/history/content,
source drift, immutable retained evidence, restart checkpoints, and a fresh portable
Python process with source access disabled. Live imports and human observations
remain separate evidence collected during the testing sessions.

Verification remediation (2026-11-09): helper sources live in `tools/import_pack/`
and are included by normal Git rules. Checkpoints retain each evidence kind by
content hash, preserving validation, final and later-task originals. Load analysis
requires `--directory` and a matching retained run/manifest/input/terminal task;
see `operator/agent-checks.md` for the complete provenance protocol. The earlier
prepared bundles were removed on 2026-11-14 (see above).

Pre-session remediation (2026-11-14): line-ending-normalised source identity,
deployment parity, known-defect deferral and the relational substitute. The pack now
lives at its designed path `.agents/testing/imports-391-3527/`. Use the bundle
`exports/imports-391-3527-2026-11-14-r4.zip` for a new session.
