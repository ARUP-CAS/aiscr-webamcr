# Proposal

## Why

The rewritten bulk importer needs repeatable verification of every supported import
class and its complex relationships, with evidence from the deployed test application,
database and Fedora. An operator currently has to assemble data and reconcile results
manually; large imports also need a separately scheduled performance session.

## What Changes

- Create a repository-local test pack for ARUP-CAS/aiscr-webamcr#391 and
  ARUP-CAS/aiscr-webamcr#3527 under `.agents/testing/imports-391-3527/`.
- Account mechanically for all registered CSV classes, permitted and prohibited
  operations, field/relationship variants, constraints, side effects and recovery cases.
  The inspected local revision has 46 classes, 33 UPDATE-capable classes and 13
  prohibited UPDATEs; deployed-version reconciliation remains a preflight requirement.
- Generate deterministic connected synthetic datasets, using test-instance references,
  Digiarchiv search and OAI/Fedora metadata as structural evidence. Missing or inaccessible
  source structures are synthesized rather than omitted from coverage.
- Minimize manual uploads through compatible batches and dependency-aware sequencing,
  while preventing an early failure or cascade from concealing another check.
- Produce independent behaviour and load suites with separate entrypoints, identifiers,
  prerequisites, time windows, evidence and reports. Prepare a 50,000-row relational
  workload and a 40,000-operation distribution/paradata workload.
- Assign browser interaction and visual UX observations exclusively to the human.
  Agents prepare datasets, perform authorized safe non-browser checks, reconcile
  evidence and guide the operator through one clearly specified step at a time.
- Supply exact UI labels from the Czech and English PO catalogs, copy-ready SQL,
  authenticated Fedora verification links, and explicit evidence retention/retrieval
  instructions suitable for a fresh agent session and reruns after fixes.
- Keep execution statuses distinct from prepared coverage. Earlier test reports supply
  hypotheses, not evidence about the rewritten importer or the current deployment.
- Pre-session remediation (2026-11-14): pin source identity by line-ending-normalised
  content so hashes are portable across checkouts, and accept a deployed revision
  as equivalent only when every pinned source file has identical normalised content.
  The test instance runs a release tag, never the pack's inspection commit.
- Defer checks that a source-confirmed, uncaught importer defect would fail, instead of
  letting the defect abort and mask whole batches. The `VazbaLookupImportField`
  fallback defect (see design decision 10) makes the affected rows `blocked`, with its
  fix as the named prerequisite. Those rows move to separate deferred batches, and the
  defect is recorded in the test report for the developer.
- Measure relational load now with a two-import substitute (30,000 parent rows, then
  20,000 component/find rows). The original single 50,000-row import stays blocked
  until the defect fix is deployed.

## Capabilities

### New Capabilities

- `testing/bulk-import-verification`: Repeatable generation, human-operated execution,
  non-browser verification and evidence accounting for comprehensive bulk-import tests,
  including separately scheduled load workloads.

### Modified Capabilities

None. No existing durable capability specs were present in the inspected repository.

## Impact

- Adds local testing tooling, data definitions, operator documents and evidence schemas;
  does not change Django application behaviour, import contracts, translations or
  shared governance. The new capability describes test-pack behaviour only.
- Reads `webclient/core/import_data_mappers.py`, related models/tests, `cron/tasks.py`,
  import views/templates and `locale/{cs,en}/LC_MESSAGES/django.po` as source inputs.
- Uses the currently deployed test application, test PostgreSQL and
  `fedora-test.aiscr.cz` during later authorized testing. Preparation performs only
  bounded read requests against external systems; supplying read-only Fedora access
  does not authorize import execution or infrastructure changes.
- Agent surfaces are delivered from aiscr-management through its manifest/registry
  baseline; this change neither edits those delivered surfaces nor requests sibling
  delivery or hub writes. Pack-owned files must remain outside delivered ownership.
- The `VazbaLookupImportField` defect in `webclient/core/import_data_mappers.py` is
  reported, not fixed. Its correction is separate developer work; this change only
  defers the dependent checks and keeps them ready for a rerun after the fix.
- This planning phase creates OpenSpec artifacts and a rolling usage record only.
  Pack implementation, git operations and live test execution are later boundaries.
