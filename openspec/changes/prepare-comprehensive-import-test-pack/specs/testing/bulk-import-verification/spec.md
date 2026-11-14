# Spec Delta

## Purpose

Provide repeatable and comprehensive verification of bulk imports through prepared
datasets, human-operated application steps, non-browser agent checks and retained
evidence, with behaviour and load testing scheduled and reported independently.

## ADDED Requirements

### Requirement: Complete version-bound coverage inventory

The pack SHALL bind coverage to recorded source and deployment identities and account
for every registered CSV class and operation, including prohibited operations. Missing
coverage or unresolved deployment drift MUST prevent a completeness claim.

#### Scenario: Baseline class coverage
- **GIVEN** the inspected revision registers 46 classes with 33 permitted UPDATEs
- **WHEN** the coverage inventory is generated
- **THEN** it includes 125 permitted class-operation cells and 13 prohibited UPDATE cells
- **AND** each cell identifies inputs, assertions and required evidence

#### Scenario: Importer changes after pack preparation
- **GIVEN** a pack bound to an earlier importer inventory
- **WHEN** a class, field, supported operation or relevant constraint changes
- **THEN** preflight reports the difference and withholds the affected coverage claims
- **AND** an unknown deployed revision is recorded as unresolved rather than assumed equal

#### Scenario: Deployed release tag differs from the inspected commit
- **GIVEN** a pack pinned to an inspected commit and a test instance deployed from a different, verified revision
- **WHEN** preflight compares the pinned source files at both revisions using line-ending-normalised content hashes
- **THEN** the deployment is recorded as source-equivalent only if every pinned file is identical, and both revisions are retained
- **AND** any differing pinned file withholds the coverage it affects, and checkout line endings MUST NOT by themselves produce drift

### Requirement: Explicit complex branch coverage

The pack SHALL separately account for relationship-owner variants, constraints,
cross-record effects and failure/recovery boundaries in each class. Sharing a mapper
or validation primitive MUST NOT erase distinct persistence or metadata paths.

#### Scenario: Multiple owners and polymorphic references
- **GIVEN** components, files, history or geographical references support multiple owners
- **WHEN** behaviour datasets are prepared
- **THEN** each supported ownership/reference variant has explicit checks
- **AND** wrong-type references, omitted values and reassignment between parents are covered

#### Scenario: Required cases have no accessible source example
- **GIVEN** a required complex branch has no suitable accessible source record
- **WHEN** datasets are generated
- **THEN** a synthetic case exercises that branch
- **AND** the branch is not silently removed or labelled passed

### Requirement: Independently defined expected outcomes

Every executable scenario SHALL declare expected DB, history, Fedora and UX outcomes
from the issue requirements, schemas and domain relationships. Importer code and
historical test reports SHALL be discovery inputs, not sufficient proof of correctness.
Conflicting or missing acceptance rules MUST remain explicit.

#### Scenario: Current implementation conflicts with expected metadata effects
- **GIVEN** a child operation is expected to affect two related records
- **WHEN** the current implementation or report names only one target
- **THEN** the verification retains assertions for both expected targets
- **AND** the discrepancy is reported without rewriting expectations to match the result

### Requirement: Reproducible connected datasets

The pack SHALL produce deterministic connected datasets with a run namespace, key
mappings, dependency order, checksums and known binary contents. It SHALL reuse verified
reference data and synthesize missing structures and personal details. Reruns MUST
identify whether a fresh namespace or a verified baseline is required.

#### Scenario: Repeat preparation with identical inputs
- **GIVEN** the same pack revision, frozen inputs, seed and namespace
- **WHEN** datasets are regenerated
- **THEN** CSVs, binaries, operation counts and import ZIP contents are reproducible
- **AND** volatile generation timestamps do not change their checksums

#### Scenario: Generated database keys are needed by a later batch
- **GIVEN** earlier imports allocate numeric keys or Fedora file paths
- **WHEN** the corresponding report and read-only query results are supplied
- **THEN** the agent binds later inputs to verified actual values
- **AND** guessed key offsets or production-to-test key equivalence are not used

### Requirement: Bounded source discovery and transient credentials

Source discovery SHALL use bounded read requests, validate candidate structures and
preserve source provenance. Credentials MUST be held transiently, confined to their
intended service and excluded from files, links, evidence and reports. Inaccessible
or empty metadata MUST be distinguished from absent domain data.

#### Scenario: A source filter is ineffective
- **GIVEN** a search parameter is ignored or a query returns overly broad results
- **WHEN** a candidate is selected for a niche case
- **THEN** the selector verifies the required nested feature before accepting it
- **AND** a search hit count alone does not satisfy coverage

#### Scenario: The agent starts a later session without credentials
- **GIVEN** the earlier read-only credentials were not persisted
- **WHEN** another agent starts the retained test pack
- **THEN** the handoff explains how to supply session-only access again
- **AND** no secret must be recovered from the pack or its evidence

### Requirement: Independent behaviour and load suites

Behaviour and load suites SHALL have separate entrypoints, prerequisites, namespaces,
execution windows, run state, evidence and reports. Either suite SHALL be preparable
and runnable without executing the other. Passing one MUST NOT imply passing the other.

#### Scenario: Operator schedules only behaviour testing
- **GIVEN** no load-testing window is authorized
- **WHEN** the behaviour session starts or resumes
- **THEN** no large workload is submitted
- **AND** load testing remains prepared but unexecuted in its own report

#### Scenario: Load session starts independently
- **GIVEN** a separately approved load window and an appropriate verified baseline
- **WHEN** the load session begins
- **THEN** it does not require successful completion of an earlier behaviour session
- **AND** any required setup is identified within the load suite

### Requirement: Representative large import workloads

The load suite SHALL prepare a 50,000-row connected relational workload and a separate
40,000-operation distribution/paradata workload. It SHALL report actual CSV rows,
parent records, files, binaries and bytes separately and verify persisted outcomes
mechanically rather than requiring record-by-record human inspection.

#### Scenario: Relational load workload
- **GIVEN** verified references and available synthetic identifiers
- **WHEN** the relational load pack is built
- **THEN** it contains 50,000 CSV data rows spanning parent and dependent records
- **AND** expected counts and relationships are available for all generated rows

#### Scenario: Distribution and paradata load workload
- **GIVEN** independently prepared test files across multiple parent records
- **WHEN** the distribution/paradata workload is built
- **THEN** it contains 20,000 distribution rows and 20,000 corresponding paradata rows
- **AND** assertions cover content, MIME types, history, metadata and transaction grouping

#### Scenario: Performance observations are unavailable
- **GIVEN** a completed load import without access to service CPU or memory metrics
- **WHEN** the agent produces the load report
- **THEN** phase durations, counts, throughput and available operator observations are reported
- **AND** unavailable resource metrics are marked unmeasured, never inferred as healthy

#### Scenario: Combined relational workload is blocked by a known defect
- **GIVEN** a source-confirmed importer defect that rejects components whose documentation units are created in the same import
- **WHEN** the relational load suite is prepared before the defect is fixed
- **THEN** it provides a two-import substitute, 30,000 project/Fieldwork event/documentation unit rows followed by 20,000 component/find rows, with each import measured and reported as a substitute
- **AND** the original single 50,000-row import remains blocked with the defect fix as prerequisite and is never reported as measured or passed

### Requirement: Efficient batches without masked checks

The pack SHALL combine compatible cases to reduce manual uploads while recording
every intended check. Cases whose parser failure, batch rejection, dependency or cascade
can conceal another check SHALL be separated or sequenced so execution is observable.

#### Scenario: Parser error aborts a ZIP
- **GIVEN** a malformed CSV prevents later files from being validated
- **WHEN** the invalid-input suite is generated
- **THEN** those later checks are assigned independent executable batches
- **AND** an aborted batch cannot mark unvisited checks as passed

#### Scenario: Parent deletion cascades to children
- **GIVEN** both explicit child deletion and parent cascade behaviour require coverage
- **WHEN** deletion packs are prepared
- **THEN** independent graph copies or verified setup stages exercise both paths
- **AND** cascade absence does not substitute for exercising an explicit child operation

#### Scenario: Known source defect would abort a batch
- **GIVEN** a source-confirmed defect that raises an uncaught exception during validation and fails the whole import job
- **WHEN** batches are generated before the defect is fixed
- **THEN** every row that triggers the defect is moved to a separate deferred batch, and its coverage items are `blocked` with the named fix as prerequisite
- **AND** the remaining checks in the original batch stay executable, and a deferred batch MUST NOT be offered as a next instruction card until its prerequisite is recorded as met

### Requirement: PO-based terminology and exact UI labels

The pack SHALL derive domain terminology and operator control labels from the repository
PO catalogs, recording message keys and source revision. English planning prose SHALL
retain exact Czech labels where they identify the operator's UI. Technical CSV and DB
identifiers SHALL remain unchanged and distinguishable from human-facing terms.

#### Scenario: Human uses the Czech administration
- **GIVEN** a step starts or downloads a bulk import
- **WHEN** the instruction is rendered
- **THEN** it names the applicable exact Czech control, such as `Zahájit import`
  or `Stáhnout log importu`, alongside the technical task context
- **AND** domain terms use catalog translations such as Fieldwork events, Sites,
  Spatial unit and Archaeological documentation point

#### Scenario: Deployed wording differs from the pack
- **GIVEN** a label differs from the pinned PO catalog
- **WHEN** the human reports the actual wording
- **THEN** the session records translation/deployment drift
- **AND** the agent does not silently guess which destructive control to use

### Requirement: Human-only browser operation

Live browser operation and evidence capture SHALL belong exclusively to the human.
Agents SHALL perform preparation, inspect supplied evidence and perform authorized
safe non-browser verification where possible. Browser automation and direct API
submission substituting for a human import action SHALL be excluded.

#### Scenario: Import step requires browser interaction
- **GIVEN** a ready ZIP and a human-operated test session
- **WHEN** the next step requires upload, confirmation, stop or download
- **THEN** the agent supplies the exact human action and waits for its outcome
- **AND** the agent does not drive the browser or submit the import through another route

#### Scenario: Verification can be performed without a browser
- **GIVEN** authorized read access or operator-exported query results
- **WHEN** checksums, XML, history or row differences need checking
- **THEN** the agent performs the mechanical comparison
- **AND** the human is not asked to inspect or transcribe every record

#### Scenario: Human supplies a screenshot
- **GIVEN** the human captures the live UI and supplies the image as evidence
- **WHEN** its labels or visible results need checking
- **THEN** the agent can inspect the image without browser access
- **AND** it distinguishes visible evidence from unobserved interactions or responsiveness

### Requirement: Executable operator instructions

Every human step SHALL identify prerequisites, the exact input and its location,
operation and control labels, expected observations, waiting/stopping conditions,
evidence to retain, and the next agent checkpoint. Steps SHALL distinguish expected
negative outcomes from unexpected failures and avoid requiring inferred commands.

#### Scenario: Operator starts a batch
- **GIVEN** a resolved run directory and a verified batch input
- **WHEN** the agent presents its instruction card
- **THEN** it provides the full local ZIP path, selected operation and expected state
- **AND** it names the evidence destination and what must be returned before continuing

#### Scenario: Unexpected failure occurs
- **GIVEN** a result differs from the instruction card
- **WHEN** the operator reports the failure
- **THEN** the next instruction preserves evidence and initiates diagnosis
- **AND** it does not automatically retry mutations or proceed into dependent batches

### Requirement: Retained evidence with explicit retrieval and handoff

The pack SHALL specify evidence filenames, locations, retrieval routes and retention
for each checkpoint. It SHALL preserve original reports, input hashes, key mappings,
baseline/result exports and required UX observations. Server paths, human downloads
and agent-readable workspace paths MUST be distinguished explicitly.

#### Scenario: Import report is saved on the server
- **GIVEN** the UI displays `Report uložen` with a container path
- **WHEN** the operator retrieves the report
- **THEN** instructions use `Stáhnout log importu` or `Reporty hromadného importu`
  to obtain the relevant XLSX and place it at the specified local evidence path
- **AND** a container path is not presented as a directly accessible workstation path

#### Scenario: Evidence is handed to a fresh agent
- **GIVEN** a partially completed run with retained evidence
- **WHEN** the operator supplies its agent-readable directory or requested attachments
- **THEN** the agent can identify the revision, suite, run, batch, task IDs and last checkpoint
- **AND** original evidence and prior results are retained through diagnosis and cleanup

### Requirement: Read-only verification and explicit state differences

Verification tools SHALL use read-only DB/API access and compare all expected domain
changes, history and Fedora targets, including unaffected controls. They SHALL check
direct resource responses, XML and binary contents where applicable. Indexed search
results alone SHALL NOT prove persistence or deletion.

#### Scenario: Paradata-only import
- **GIVEN** a paradata-only operation and captured baseline
- **WHEN** the agent verifies the result
- **THEN** it checks paradata contents and the absence of unintended DB/history/XML changes
- **AND** it does not mistake expected Fedora version changes for a metadata-XML change

#### Scenario: SQL cannot be run by the agent
- **GIVEN** no authorized database connection is available
- **WHEN** a checkpoint needs database evidence
- **THEN** the pack supplies a complete read-only query and exact export instructions
- **AND** the agent consumes the export while missing results remain unverified

### Requirement: Phase-specific recovery and controlled cleanup

The pack SHALL specify rollback, partial-commit and recovery expectations by phase and
record boundary. Recovery SHALL be derived from reconciled actual state. Cleanup SHALL
identify exact run-owned targets and retain evidence; live mutations, service disruption
and cleanup require authorization for their own operation and target.

#### Scenario: Failure follows committed parent groups
- **GIVEN** earlier parent groups committed before a later group failed
- **WHEN** recovery inputs are prepared
- **THEN** they distinguish committed, rolled-back and unprocessed operations
- **AND** the original INSERT ZIP is not blindly replayed

#### Scenario: Fault injection or cleanup is not authorized
- **GIVEN** a test requires live infrastructure changes or deletion of test data
- **WHEN** that operation lacks authorization
- **THEN** the case remains blocked and evidence is preserved
- **AND** a simulated result or an alternative mutation route does not satisfy it

### Requirement: Evidence-based completion reports

Reports SHALL distinguish prepared, passed, failed, blocked, unexecuted and explicitly
inapplicable checks and link executed outcomes to evidence. Class, branch, DB, history,
Fedora, UX and load coverage SHALL be visible separately. Mandatory missing evidence
MUST prevent an overall completeness claim.

#### Scenario: Data passes while UX has no human observation
- **GIVEN** database and Fedora assertions pass without the required visual observation
- **WHEN** the behaviour report is generated
- **THEN** data assertions pass and the UX check remains unexecuted
- **AND** the entire scenario is not labelled fully passed

#### Scenario: Rerun after a fix
- **GIVEN** a new deployed revision and an earlier failed run
- **WHEN** a new session starts
- **THEN** it creates a distinct evidence run and rechecks inventory and prerequisites
- **AND** it retains earlier findings and does not inherit passing outcomes without evidence

#### Scenario: Source-confirmed defect is reported without a live run
- **GIVEN** checks deferred because of a known importer defect
- **WHEN** the behaviour or load report is generated
- **THEN** a known-defects section names each defect's source location, trigger conditions, deferred coverage items and deferred batches, labelled source-confirmed rather than observed live
- **AND** the deferred items count as blocked, prevent an overall completeness claim, and become executable again only in a run against a deployment that contains the fix
