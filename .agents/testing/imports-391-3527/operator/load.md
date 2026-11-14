# Independent load session

Use this runbook in its own authorized test-environment window. It does not require
execution of the behaviour suite and does not contribute a behaviour/UX pass merely
because large row counts completed. Read `START-HERE.md` and `evidence.md` first.

## Choose one workload

| Workload | Setup outside measurement | Measured input |
|---|---|---|
| Relational | Synthetic organisation/person and reusable spatial unit; verified vocabulary/geographical references | 10,000 projects + 10,000 Fieldwork events + 10,000 documentation units + 10,000 components + 10,000 finds = 50,000 rows. While the known defect is unfixed: two-import substitute (30,000 + 20,000 rows, see below) |
| Distribution/paradata | 5,000 synthetic parent documents and 10,000 files; generated key/path bindings and source volume staged | 20,000 distributions + 20,000 paradata = 40,000 operations, grouped across 5,000 parent records |

The agent builds and verifies full-size inputs offline and supplies the complete source
folder for transfer. `load-binaries` creates 40,000 source files for the second workload;
the binary manifest gives actual counts, bytes and checksums. This is a metadata/operation
load with deliberately small contents, not a claim about throughput for multi-GB binaries.

The generated `binary-sources.zip` lets an authorized agent/service owner transfer and
extract the flat source pool in one operation. Verify its SHA-256 and the complete
`binary-manifest.json`. `load-expected.json` separates setup sources from measured
payload bytes/writes, distribution history and parent transaction groups. Keep the
pool until recovery and every dependent check are finished.

## Before the window

The operator records the permitted window, service owner/contact and stop conditions.
The agent records deployment identity, a fresh independent namespace, expected row/parent/
file/binary counts, expanded ZIP size and available monitoring. Confirm current limits,
maintenance configuration and sufficient capacity through the authorized operator.
Missing service CPU/memory metrics are marked unmeasured. Agree the time/resource budget
for this instance; do not invent a universal duration threshold.

Build examples for the agent, from the repository root:

```powershell
.venv/Scripts/python.exe .agents/testing/imports-391-3527/tools/pack.py build --suite load --workload relational --namespace 960000 --references REFERENCES_JSON --output NEW_RELATIONAL_DIRECTORY
.venv/Scripts/python.exe .agents/testing/imports-391-3527/tools/pack.py build --suite load --workload distributions --namespace 980000 --references REFERENCES_JSON --bindings VERIFIED_BINDINGS_JSON --output NEW_DISTRIBUTION_DIRECTORY
.venv/Scripts/python.exe .agents/testing/imports-391-3527/tools/pack.py load-binaries --directory NEW_DISTRIBUTION_DIRECTORY
```

Resolve all uppercase arguments and input templates before presenting a human card.
Setup may allocate keys; the agent binds them from matching XLSX and DB evidence, then
generates the measured input in a new directory. Do not guess keys or reuse another suite.

## During the window

The human performs the prepared upload/start/download actions and observes labels,
progress, control state, responsiveness and reopening the page. The agent performs
safe non-browser reads and records timestamps, phase durations, progress samples and
available service metrics. Retain validation, approval/start and terminal times separately.
Do not stop the job just to test failure during a successful load measurement. Planned
interruption/recovery has its own clearly authorized run and distinct evidence.

## After the measured import

Retain the original XLSX, exact input hash, `timings.json`, progress/monitoring exports,
human observations, full expected/actual DB and Fedora counts, integrity assertions,
content hashes and transaction/group evidence. Check the complete generated dataset
mechanically; a few screenshots or matching totals alone are insufficient.

Report actual rows, distinct parents, files, binaries and bytes separately. Compute
throughput per measured phase and identify setup time separately. Show missing metrics
as unmeasured and missing evidence as unverified. Preserve all results for comparison
after fixes. Recovery and cleanup require reconciled actual state and their own scoped
authorization; neither runs automatically at the end of the load window.

Use `load-evidence.template.json` and `load-analyse --directory RUN_DIRECTORY`. A
manifest with several measured imports writes one `load-evidence.<batch>.template.json`
per import. Each evidence object names its `batch_id`, and `load-analyse` refuses an
ambiguous or non-measured batch. When the deployment is not the inspected commit,
start the run with `start-run --parity PARITY_JSON` from `deployment-parity` (see
`operator/agent-checks.md`).
Follow the retained-session protocol in `operator/agent-checks.md`: bind the final
manifest/input, batch/task, run/namespace and deployment identities; retain original
DB/Fedora/report/UX evidence and normalized `load-results` in a checked terminal
checkpoint. An unbound summary is descriptive only and cannot verify correctness. Every measured logical row/object
must have its own passing identity check. Also provide complete history/orphan checks,
semantic metadata and version checks for every expected parent, not just totals. For
the distribution workload retain normalized `group_transactions` entries with actual
`parent`, `transaction_uid`, `state: committed` and `operations: 8`, extracted by the
agent from the report or approved task-scoped logs. The expected 5,000 groups are not
proof of the actual 5,000 committed groups. Missing grouping evidence remains unverified.

Relational sequence while the `VazbaLookupImportField` defect is unfixed (see
`operator/known-source-risks.md`):

1. Preflight, then `L00-setup`, then verify the setup.
2. `L01a-relational-parents-30000`: validation/start → terminal report → complete
   verification.
3. `L01b-relational-components-20000`: validation/start → terminal report → complete
   verification.

Steps 2 and 3 are each a measured import with their own evidence object and expected
counts. Their metadata targets are projects plus Fieldwork events for `L01a`, and the
components' owning Fieldwork events for `L01b`. Report both as the **two-import
substitute**, never as the combined 50,000-row figure. `L01-relational-50000` stays
prepared but deferred: it has no card, cannot be checkpointed, and its expectation is
`blocked` in `load-expected.json`.

After the fix is deployed and recorded in `definitions/known-defects.json`, rebuild.
The sequence then returns to preflight → `L00-setup` → verify setup →
`L01-relational-50000` validation/start → terminal report → complete
DB/history/Fedora verification. The combined new-parent graph is intentional; a
validation failure is not a throughput run.

Distribution sequence: preflight/source-pool transfer → `L00-parents` → `L01-files`
→ bind all 10,000 allocated IDs/paths from XLSX plus DB → rebuild into a new directory
→ `L02-distributions-40000` validation/start → terminal report → complete object,
history, metadata, version and parent-group verification. Setup never enters measured
throughput. Present the exact card for each arrow; the human does no bulk comparison.
