# CI test results

## Purpose

Make a DEV test run publish only results that the current run actually
produced, with complete counts, a usable previous run for diagnosis, and
reliable Selenium cleanup.

## ADDED Requirements

### Requirement: Deployment cannot consume subsequent test commands

Non-interactive deployment and test commands SHALL NOT read the command
stream of the remote shell that invokes them. A successful optional
deployment SHALL be followed by the requested tests. A failed required
deployment SHALL fail the run before tests start.

#### Scenario: A deployment child reads standard input

- **GIVEN** deployment is enabled and a nested deployment command reads stdin
- **WHEN** the remote workflow runs any supported test mode
- **THEN** exactly the requested test command runs afterwards with its original arguments

#### Scenario: Deployment is disabled or fails

- **GIVEN** a valid test selection
- **WHEN** deployment is disabled, or an enabled deployment fails
- **THEN** the disabled case starts the tests, and the failed case exits unsuccessfully without starting them

### Requirement: Remote test summaries are read as data

The result step SHALL parse the downloaded summary without executing it. It
SHALL require exactly one nonnegative decimal `PASSED` and one `FAILED`
value, reject anything else, and read at most 4097 bytes, rejecting
summaries over 4096 bytes. Validation SHALL complete before any count is
reported.

#### Scenario: A valid summary is reported

- **GIVEN** `PASSED` and `FAILED` records with decimal counts in either order, with LF or CRLF line endings and with or without a final newline
- **WHEN** the result step reads the summary
- **THEN** it reports the canonical counts without executing the file

#### Scenario: Malformed or executable content is rejected

- **GIVEN** a summary that is empty, oversized, has duplicate, missing or unknown keys, malformed values, NUL bytes or appended shell commands
- **WHEN** the result step reads it
- **THEN** it fails without executing any embedded command and publishes no counts
- **AND** the SSH agent cleanup still runs

### Requirement: Published results belong to the current run attempt

The workflow SHALL accept counts and artifacts only from an outcome whose run
attempt identity, mode and test number match the current run. A missing,
incomplete or mismatched outcome SHALL fail the job. The outcome SHALL
distinguish completed tests, an allowed no-op and an execution error.

#### Scenario: A current run completes

- **GIVEN** a completed run whose outcome, summary and required workbook match its identity and selection
- **WHEN** the workflow validates the results
- **THEN** it reports the counts and state of that run

#### Scenario: The run never starts or stops early

- **GIVEN** an earlier run left a passing outcome and the current run never starts or stops before publishing its outcome
- **WHEN** the workflow retrieves results
- **THEN** it fails without accepting the earlier outcome as current

#### Scenario: Files disagree about their run

- **GIVEN** an outcome, summary or workbook that is missing, altered or belongs to another run attempt
- **WHEN** the result bundle is validated
- **THEN** it is rejected before any result is reported

#### Scenario: Completed tests fail

- **GIVEN** the current run completes with failed tests
- **WHEN** the workflow reports its validated results
- **THEN** it annotates the failed count, keeps the results available and remains failed
- **AND** an invalid bundle or execution error produces no failed-count annotation

### Requirement: Workflow artifact upload uses only the verified bundle

The result step SHALL export only `ARTIFACTS` as its step output, signal
upload only after the bundle is verified, and keep its download plan outside
the uploaded directory.

#### Scenario: A verified bundle is uploaded

- **GIVEN** a current validated outcome and its listed files
- **WHEN** the workflow uploads the results
- **THEN** the artifact contains only the outcome and its verified files

#### Scenario: Retrieval or validation fails

- **GIVEN** a missing, incomplete or mismatched result
- **WHEN** the result step cannot verify it
- **THEN** it does not signal upload eligibility and the failure remains visible

### Requirement: Each run starts from an empty result directory and keeps the previous run

Before producing output, a test run SHALL replace the `previous/` result
directory with the existing `current/` one and create an empty `current/`.
Earlier runs SHALL be removed. The rotation SHALL NOT touch the root
selection workbook and SHALL NOT delete anything outside the results root.

#### Scenario: A run starts after earlier runs

- **GIVEN** the results root holds `current/` and `previous/` from two earlier runs
- **WHEN** a new run starts
- **THEN** the older `previous/` is removed, the last run's output becomes `previous/`, and `current/` is empty
- **AND** the root selection workbook is unchanged

#### Scenario: The first run on a host

- **GIVEN** the results root has no `current/` or `previous/`
- **WHEN** a run starts
- **THEN** it creates an empty `current/` and proceeds

#### Scenario: A result directory is a symbolic link

- **GIVEN** `current/` or `previous/` is a symbolic link
- **WHEN** a run starts
- **THEN** the run fails before producing output and deletes nothing behind the link

### Requirement: Previous results remain selection input

Failed-only and numbered runs SHALL select tests from the previous root
workbook, independently of the current run's output. A failed-only run with
no remaining failures SHALL publish an explicit successful no-op. Missing or
unreadable input and an unknown test number SHALL fail the run. Selection
and publication SHALL accept a test name when every dotted part is a Python
identifier, including identifiers with non-ASCII letters.

#### Scenario: Previous results select a new run

- **GIVEN** a readable root workbook and a failed-only or numbered selection
- **WHEN** the run is prepared
- **THEN** tests are selected from that workbook and preparing the new output does not remove it

#### Scenario: No failed tests remain

- **GIVEN** a failed-only run whose root workbook lists no failures
- **WHEN** selection completes
- **THEN** the run publishes a successful no-op without presenting old output as new

#### Scenario: Selection cannot identify the tests

- **GIVEN** a missing or unreadable workbook, or a numbered test absent from it
- **WHEN** selection is attempted
- **THEN** the run publishes an error outcome and fails

#### Scenario: Test names contain non-ASCII letters

- **GIVEN** a previous or newly written workbook with test names such as `ez.tests.test_selenium.AkceExterniZdroj.test_117_zapsani_externího_zdroje_p_001`
- **WHEN** selection or publication validates the workbook
- **THEN** the names are accepted, and a name with a dotted part that is not an identifier is still rejected

### Requirement: DEV test runs contain only workbook-tracked Selenium tests

The DEV test runner's default selection SHALL contain only modules whose test
classes record a workbook row for every test. Unit, import and integration
tests outside Selenium SHALL NOT run in the DEV test workflow.

#### Scenario: A full DEV run selects its tests

- **GIVEN** a full DEV run
- **WHEN** the runner selects its default tests
- **THEN** every selected module is a Selenium module whose test classes derive from the workbook-writing base class

#### Scenario: Failed-only follows a run with failures

- **GIVEN** a completed full run in which tests failed
- **WHEN** a failed-only run selects from the root workbook
- **THEN** every failed test of that run is selected and the run does not publish the successful no-op

#### Scenario: A non-Selenium module is added to the DEV defaults

- **GIVEN** a default module with a test class that does not record workbook rows
- **WHEN** the regression suite runs
- **THEN** it fails and names the module

### Requirement: Every failed test of a completed run has a workbook row

A Selenium test whose setup fails SHALL record an ERROR workbook row without
using the driver, because its teardown does not run. A run SHALL publish a
completed outcome only when the FAIL and ERROR rows written to its workbook
match its `FAILED` count. Otherwise it SHALL publish an error outcome and
SHALL leave the root selection workbook unchanged; the error SHALL state the
mismatch when the run executed test bodies, and the missing complete summary
when it did not.

#### Scenario: Setup fails

- **GIVEN** a Selenium test whose setup raises before, during or after driver creation
- **WHEN** the test finishes
- **THEN** the workbook has one ERROR row for that test and the setup error remains the reported error
- **AND** a driver that was created is released exactly once

#### Scenario: A failure has no workbook row

- **GIVEN** a run that executed test bodies and in which unittest counts a failure or error that has no FAIL or ERROR row, such as a failed class setup in a multi-class run or a failed workbook write
- **WHEN** the runner publishes its outcome
- **THEN** it publishes an error outcome stating the mismatch and the root selection workbook is unchanged

#### Scenario: A class setup fails with no executed test

- **GIVEN** a run in which the only class fails `setUpClass` and unittest reports `Ran 0 tests`
- **WHEN** the runner publishes its outcome
- **THEN** it publishes an error outcome stating that the complete test summary is missing, and the root selection workbook is unchanged

### Requirement: Test runner outcomes reflect actual execution

The runner SHALL check migration and test process results and read the
complete output before deciding an outcome. Startup errors, missing or
inconsistent summaries and runs that execute no test body SHALL fail. The
failed-only no-op SHALL be the only successful run without executed tests.

#### Scenario: Migration fails

- **GIVEN** test database migration exits unsuccessfully
- **WHEN** the runner handles the result
- **THEN** it fails before starting tests

#### Scenario: Tests crash before their summary

- **GIVEN** test startup fails or the output lacks a complete consistent summary
- **WHEN** the runner derives its outcome
- **THEN** it reports failure instead of zero passes and zero failures

#### Scenario: Output is still buffered when the process exits

- **GIVEN** a test process finishes while console or file logging still holds buffered output
- **WHEN** the runner publishes its outcome
- **THEN** counts reflect both complete streams and the actual process result

### Requirement: Published counts distinguish actual passes from other outcomes

`PASSED` SHALL exclude skips and expected failures. `FAILED` SHALL include
failures, errors and unexpected successes. Skips and expected failures SHALL
be reported separately. The outcome's counts SHALL agree with the total, the
two-key summary and the process result, or the run fails.

#### Scenario: A run has mixed results

- **GIVEN** a run with passes, skips, expected failures and failures
- **WHEN** the counts are published
- **THEN** each category is reported separately and the categories add up to the total

#### Scenario: Only expected failures execute

- **GIVEN** every executed test is an expected failure and the process succeeds
- **WHEN** the outcome is validated
- **THEN** it is accepted with zero `PASSED`, zero `FAILED` and a positive expected-failure count

#### Scenario: Every selected test is skipped

- **GIVEN** an ordinary run in which every test is skipped
- **WHEN** the runner decides its outcome
- **THEN** the run fails and is not presented as the failed-only no-op

#### Scenario: Counts are invalid or inconsistent

- **GIVEN** an outcome with an unsupported version, missing or negative counts, or counts that disagree with the summary or process result
- **WHEN** the workflow validates it
- **THEN** it fails before reporting results

### Requirement: Selenium resources survive test-output failures

A Selenium test SHALL register driver cleanup as soon as the driver is
created. A failing workbook write or later setup step SHALL NOT skip driver
cleanup or base teardown, and the original error SHALL remain visible.
Normal completion SHALL quit the driver once.

#### Scenario: Writing the workbook fails during teardown

- **GIVEN** a local or remote driver exists and the workbook write raises
- **WHEN** teardown runs
- **THEN** the driver is released, base teardown runs and the write error is reported

#### Scenario: Setup fails after driver creation or the test passes

- **GIVEN** a created driver and a failing later setup step, or a normal test completion
- **WHEN** cleanup runs
- **THEN** the session is released exactly once

### Requirement: Workbook rows reflect the current test's own result

Each workbook row SHALL record OK, FAIL or ERROR from the current test's own
outcome. Failures or errors of other tests in the same run SHALL NOT change
it.

#### Scenario: An earlier test errored

- **GIVEN** an earlier test errored and the current test fails an assertion
- **WHEN** the current row is written
- **THEN** it records FAIL, not ERROR

### Requirement: Runner diagnostics report the cause without configured paths

A runner failure SHALL be reported with the run attempt, stage, exception
type and message. The message SHALL have the configured results root
replaced by a placeholder in its configured, absolute and resolved forms,
control characters turned into spaces and a bounded length. The runner SHALL
print this cause to stderr and record it as the outcome message. Outcome
validation SHALL reject a message that is not one bounded line.

#### Scenario: The output root comes from secret-backed settings

- **GIVEN** the runner reads its output root from secret-backed settings
- **WHEN** a run completes or fails
- **THEN** console output and the outcome identify the run without printing the root

#### Scenario: A failure message contains the results root

- **GIVEN** a runner stage raises an exception whose message contains the results root in its configured or resolved form
- **WHEN** the runner reports the failure
- **THEN** stderr and the outcome show the stage, the exception type and the message with the root replaced by the placeholder, and the run fails

#### Scenario: Publishing the error outcome fails

- **GIVEN** the runner cannot publish its error outcome
- **WHEN** it finishes
- **THEN** it prints the cause, exits nonzero and shows no uncaught traceback

### Requirement: The workflow shows the cause of an error outcome

For a downloaded error outcome, the workflow SHALL show the recorded cause in
its step summary and as one error annotation, escaped as workflow-command
data, and the step SHALL fail.

#### Scenario: An error outcome reaches the workflow

- **GIVEN** a downloaded error outcome with a recorded cause
- **WHEN** the workflow reports it
- **THEN** the step summary and one error annotation show the cause, and the step fails

#### Scenario: A cause contains workflow-command text

- **GIVEN** an exception message with a line break followed by workflow-command syntax
- **WHEN** the runner records the cause and the workflow reports it
- **THEN** the cause stays on one line and the only workflow command emitted for it is the single error annotation

### Requirement: DEV tests and deployments do not overlap

The DEV test workflow and DEV deployment SHALL share one concurrency group
without cancelling an active run, because they share a checkout and stack.
TEST deployment SHALL use a separate group.

#### Scenario: A DEV deployment is requested during a DEV test run

- **GIVEN** a DEV test run with or without deployment and a DEV deployment request
- **WHEN** their concurrency settings are evaluated
- **THEN** both use the same DEV group with `cancel-in-progress: false`

#### Scenario: TEST deployment runs independently

- **GIVEN** a TEST deployment while DEV work is active
- **WHEN** concurrency groups are evaluated
- **THEN** TEST uses a group distinct from DEV
