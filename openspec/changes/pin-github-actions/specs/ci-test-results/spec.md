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
unreadable input and an unknown test number SHALL fail the run.

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

### Requirement: Runner diagnostics do not disclose configured paths

Runner messages and outcome text SHALL identify the run attempt and a fixed
failure stage only. They SHALL NOT include configured filesystem paths or
raw exception text. If publishing an error outcome also fails, the runner
SHALL exit nonzero without an uncaught traceback.

#### Scenario: The output root comes from secret-backed settings

- **GIVEN** the runner reads its output root from secret-backed settings
- **WHEN** a run completes or fails
- **THEN** console output and the outcome identify the run without printing the root

#### Scenario: A failure carries sensitive exception text

- **GIVEN** any runner stage raises an exception containing a sensitive value
- **WHEN** the runner reports the failure
- **THEN** stderr and the outcome name only the stage, and the run fails

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
