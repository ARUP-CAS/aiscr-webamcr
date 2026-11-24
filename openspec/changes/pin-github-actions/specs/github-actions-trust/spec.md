# GitHub Actions trust

## Purpose

Keep workflow action dependencies immutable and reviewable while preserving SSH
testing, scoped credentials, safe workflow-input handling, automated updates,
and a documented path to safe policy activation.

## ADDED Requirements

### Requirement: Immutable external action references

Every active external `uses:` reference in repository workflow files SHALL use
a full 40-character commit SHA and a same-line comment naming its associated
release version. This applies to GitHub-owned and third-party actions alike.
A release comment SHALL belong unambiguously to one external call.

#### Scenario: External actions have verified release pins

- **GIVEN** a workflow references an external action, including an action subpath
- **WHEN** the dependency revision is reviewed
- **THEN** the reference contains a full commit SHA verified in the upstream repository
- **AND** its same-line version comment identifies the release associated with that commit

#### Scenario: Mutable or incomplete references are rejected

- **GIVEN** an active external action uses a tag, branch, shortened SHA, or missing version comment
- **WHEN** workflow dependencies are validated
- **THEN** validation reports the offending workflow location and fails

#### Scenario: Multiple calls cannot share an ambiguous release comment

- **GIVEN** a flow-style YAML line contains multiple external calls and one trailing release comment
- **WHEN** workflow dependencies are validated or inventoried
- **THEN** processing fails with the workflow location instead of assigning that comment to every call

#### Scenario: Unambiguous flow syntax remains supported

- **GIVEN** a flow-style mapping contains one full-SHA external call with its release comment
- **WHEN** workflow dependencies are validated
- **THEN** the call is accepted without requiring conversion to block style
- **AND** version-like text inside another quoted value does not substitute for a real comment

### Requirement: Duplicate workflow mapping keys are rejected

Workflow dependency validation SHALL reject duplicate keys in YAML mappings
with file and line diagnostics before extracting or inventorying action
references.

#### Scenario: A duplicate key cannot hide an action reference

- **GIVEN** a workflow mapping repeats a key, including a pinned first `uses` followed by a mutable second `uses`
- **WHEN** workflow dependencies are validated or inventoried
- **THEN** processing fails at the duplicate key's location
- **AND** no partial inventory replaces the existing documentation

### Requirement: Local workflow references remain local

Same-repository `./` workflow references SHALL remain local and SHALL be
excluded from the external-action SHA and version-comment requirement.

#### Scenario: Publishing uses the caller's local workflow

- **GIVEN** the release workflow calls `./.github/workflows/publish_images.yml`
- **WHEN** external action dependencies are pinned and validated
- **THEN** the local call remains unchanged and passes dependency validation

### Requirement: Native SSH authentication across workflow steps

The DEV test workflow SHALL authenticate with the existing configured key
using native SSH-agent tooling instead of `webfactory/ssh-agent`. The loaded
identity SHALL remain available to the subsequent SSH and SCP steps without
exposing the private key in logs or persisted workflow artifacts.

#### Scenario: Isolated SSH and result-retrieval steps share the agent

- **GIVEN** a disposable valid key and isolated step environments with remote clients replaced by test fixtures
- **WHEN** the workflow setup, SSH, and result-retrieval shell steps execute
- **THEN** the SSH and both SCP clients can access the same loaded identity
- **AND** only the agent socket and PID are persisted between steps

#### Scenario: Key loading fails safely

- **GIVEN** the configured private key cannot be loaded
- **WHEN** native agent initialization runs
- **THEN** the step fails before remote execution
- **AND** the private key is absent from logs and result artifacts

### Requirement: SSH-agent cleanup

The DEV test and deployment workflows SHALL stop their native SSH agents
after their final use, including when key loading, remote execution, or
result retrieval fails. Cleanup SHALL preserve the original operation's
failure result.

#### Scenario: Failure still releases the agent

- **GIVEN** native SSH-agent initialization succeeded
- **WHEN** a subsequent SSH or SCP step fails
- **THEN** the workflow attempts agent cleanup through an unconditional cleanup step

#### Scenario: Deployment releases its single-step agent on every exit

- **GIVEN** deployment creates an SSH agent within its SSH connection step
- **WHEN** key loading or remote execution fails, or remote execution completes
- **THEN** the step attempts to stop the agent before exiting
- **AND** cleanup does not turn a failed operation into success

### Requirement: SSH private keys have step-scoped exposure

The DEV test and deployment workflows SHALL expose their private keys only
to the steps that load them. Keys SHALL be consumed from step environment
variables without shell tracing, and SHALL NOT be placed in job-wide
environment variables, cross-step state, logs, or artifacts.

#### Scenario: Other deployment steps do not receive the private key

- **GIVEN** a deployment job includes tag normalization, checkout, VPN, and SSH steps
- **WHEN** its private-key environment is configured
- **THEN** the key is scoped to the SSH connection step that loads it
- **AND** the other steps do not inherit a job-level private-key variable

### Requirement: Workflow values remain data across shell boundaries

Manual deployment/test inputs and reference names SHALL be consumed as data
without becoming local or remote shell script text. Remote test execution
SHALL use a static script body and argument transport that preserves values
through both shell boundaries.

#### Scenario: Deployment tag content cannot execute before validation

- **GIVEN** a supplied deployment tag contains command substitution, quotes, or a newline
- **WHEN** tag normalization processes that value
- **THEN** no command embedded in the value executes
- **AND** an invalid tag is rejected before deployment

#### Scenario: DEV test input cannot become a remote command

- **GIVEN** a supplied test number contains shell syntax instead of digits
- **WHEN** the test workflow prepares or transports its inputs
- **THEN** the value is rejected without executing its contents locally or remotely
- **AND** no remote deployment or test command is invoked

#### Scenario: Reference names survive remote argument transport literally

- **GIVEN** a valid workflow reference name contains characters meaningful to a shell
- **WHEN** that reference is passed to the remote deployment command
- **THEN** the receiving script obtains the original value as a single argument
- **AND** the reference's characters are not interpreted as commands

### Requirement: Manual workflow inputs are validated before remote work

Deployment/test workflows SHALL validate deployment tags and test selection
inputs before connecting VPN or executing SSH. Invalid input SHALL fail
without deployment or test execution. Existing valid inputs, defaults,
deployment-source selection, and test modes SHALL retain their behavior.

#### Scenario: Valid deployment tags preserve normalization

- **GIVEN** an accepted numeric release tag with or without a leading `v` and an optional supported prerelease suffix
- **WHEN** deployment inputs are validated
- **THEN** the Git tag retains the `v` prefix and the image tag omits it
- **AND** the selected environment and image source retain their existing behavior

#### Scenario: Valid test modes preserve their commands

- **GIVEN** `test_mod` is `vsechny`, `neuspesne`, or `konkretni`, `nasadit_verzi` is a boolean, and every supplied test number is decimal digits
- **WHEN** inputs are validated with a nonempty test number required for `konkretni`
- **THEN** all-tests, failed-tests, or numbered-test execution keeps its existing command and optional deployment behavior

#### Scenario: Invalid test selections fail before connection

- **GIVEN** an unknown test mode, a nonnumeric supplied test number, a missing number for `konkretni`, or an invalid deployment boolean
- **WHEN** the manual test workflow validates its inputs
- **THEN** it fails before VPN connection or SSH execution

### Requirement: Remote test summaries are read as data

The DEV result step SHALL read downloaded summaries without executing their
contents. It SHALL require exactly one `PASSED` and one `FAILED` assignment
with nonnegative decimal counts, emit canonical numeric outputs, and reject
other content. It SHALL validate the complete file before publishing either
outputs or the report, fail on invalid input, and preserve agent cleanup.

#### Scenario: Valid result summaries preserve reporting

- **GIVEN** the producer's `PASSED` and `FAILED` records with decimal counts, including zero or leading zeros
- **WHEN** the result step reads either record order using LF/CRLF or a final record without a newline
- **THEN** it emits canonical decimal outputs and the existing report without executing the file
- **AND** positive failed counts remain visible to the existing workflow failure check

#### Scenario: Incomplete or malformed summaries publish no results

- **GIVEN** an empty summary, duplicate/missing/unknown keys, malformed values, empty records, or NUL bytes
- **WHEN** the result step validates the downloaded file
- **THEN** it fails and leaves the outputs and human-readable summary unchanged

#### Scenario: Summary contents cannot execute shell commands

- **GIVEN** a downloaded summary contains appended shell commands or command substitution in a value
- **WHEN** the result step reads the summary
- **THEN** it rejects the content without executing an embedded command or canary
- **AND** it publishes no partial results

#### Scenario: Summary validation failure still releases the agent

- **GIVEN** the result SCP clients use the loaded identity and the downloaded summary is invalid
- **WHEN** validation fails
- **THEN** the unconditional cleanup step still stops the agent
- **AND** the result step remains failed

### Requirement: Deployment cannot consume subsequent test commands

Non-interactive deployment and test operations SHALL NOT consume the command
stream of the remote shell that invokes them. A successful optional deployment
SHALL be followed by the requested test mode. A required deployment failure
SHALL fail the operation before test execution.

#### Scenario: A deployment child reads standard input

- **GIVEN** deployment is enabled and a nested deployment command attempts to consume stdin
- **WHEN** the remote workflow runs each supported test mode
- **THEN** successful deployment is followed by exactly the requested test invocation and its original arguments
- **AND** none of the remaining remote script is supplied to the deployment child as input

#### Scenario: Deployment is disabled or fails

- **GIVEN** valid all-tests, failed-only, or numbered-test input
- **WHEN** deployment is disabled or a required enabled deployment operation fails
- **THEN** the disabled case reaches test selection, while the failed-deployment case exits unsuccessfully without starting tests

### Requirement: Published results belong to the current execution attempt

The workflow SHALL accept counts and artifacts only when their execution
identity and explicit outcome match the current attempt and selected mode.
Missing, incomplete, mismatched, or older results SHALL NOT establish success.
Publication SHALL distinguish completed tests, an allowed no-op, and an
execution error without evaluating downloaded data.

#### Scenario: A current attempt completes

- **GIVEN** a completed current attempt with matching identity, selection, summary, and any required spreadsheet
- **WHEN** the workflow validates and publishes its results
- **THEN** counts and artifacts refer to that attempt and their reported execution outcome is explicit
- **AND** the existing numeric summary remains subject to complete non-evaluating validation

#### Scenario: A run is skipped or interrupted while older results exist

- **GIVEN** an earlier passing result exists and the current attempt never starts or stops before publishing a complete outcome
- **WHEN** result retrieval or validation runs
- **THEN** the workflow fails without accepting the earlier counts or artifact as current

#### Scenario: Downloaded results disagree about their attempt

- **GIVEN** the retrieved outcome, summary, selection, or required spreadsheet is missing or belongs to a different attempt
- **WHEN** the result bundle is validated
- **THEN** it is rejected before successful results are reported or an artifact is presented as current

#### Scenario: Completed tests fail

- **GIVEN** the current attempt completes with a nonzero test result
- **WHEN** its matching diagnostic results are available
- **THEN** the workflow can retain those results while remaining failed
- **AND** result retrieval and unconditional cleanup cannot turn that failure into success

### Requirement: Previous results remain selection input

Failed-only and numbered-test selection SHALL retain access to the previous
spreadsheet independently of current-attempt output. Failed-only selection
with no remaining failures SHALL produce an explicit current-attempt no-op.
Missing or unreadable selection input and an unknown numbered test SHALL fail
without reusing earlier output as a successful new result.

#### Scenario: Previous results select a new run

- **GIVEN** a readable previous spreadsheet and a valid failed-only or numbered selection
- **WHEN** a new execution attempt is prepared and run
- **THEN** selection is resolved from the previous spreadsheet and current output is attributed independently
- **AND** preparing current output does not destroy the input needed for selection

#### Scenario: There are no failed tests to rerun

- **GIVEN** failed-only mode reads valid previous results containing no failed tests
- **WHEN** selection completes
- **THEN** the attempt reports an explicit successful no-op with no tests executed
- **AND** it does not present the previous spreadsheet as newly executed test output

#### Scenario: Selection cannot identify the requested tests

- **GIVEN** missing or unreadable selection input, or a requested numbered test absent from that input
- **WHEN** selection is attempted
- **THEN** the attempt fails with a diagnostic outcome and cannot report a successful no-op or stale results

### Requirement: Required operation failures reach the workflow

Required build, deployment, database-clone, and test failures SHALL propagate
through nested commands and wrappers as unsuccessful workflow outcomes.
Dependent operations SHALL stop after a prerequisite fails. A failed
deployment or readiness check SHALL NOT update the recorded successfully
deployed version. Explicitly optional operations SHALL retain their documented
warning behavior.

#### Scenario: A nested deployment operation fails

- **GIVEN** a required image build, pull, stack removal, or deployment command fails
- **WHEN** its containing scripts return to the workflow
- **THEN** failure remains nonzero, dependent operations stop, and later logging cannot replace it with success

#### Scenario: Database cloning or a wrapped child fails

- **GIVEN** a required database clone or test child exits unsuccessfully inside a terminal or container wrapper
- **WHEN** the wrapper and caller finish
- **THEN** failure reaches the workflow and tests cannot proceed after a failed clone

#### Scenario: Deployment fails a final check

- **GIVEN** a deployment or its required readiness check fails
- **WHEN** deployment bookkeeping is reached
- **THEN** the operation fails and the previous successfully deployed version record is preserved

#### Scenario: An optional maintenance operation fails

- **GIVEN** only an explicitly optional operation such as memory compaction fails
- **WHEN** all required deployment checks succeed
- **THEN** the documented warning remains visible without falsely failing or masking a required operation

### Requirement: Test runner outcomes reflect actual execution

The runner SHALL check migration and test subprocess results and consume
their complete output before determining an outcome. Startup errors, missing
or inconsistent test summaries, and incomplete execution SHALL fail rather
than produce a passing zero-count result. An ordinary test execution SHALL
require actual tests to run; the separately defined failed-only no-op is the
only successful zero-execution outcome.

#### Scenario: Migration fails

- **GIVEN** test database migration exits unsuccessfully
- **WHEN** the runner handles its result
- **THEN** it fails before starting tests and does not publish a completed passing result

#### Scenario: Tests crash before their summary

- **GIVEN** test startup fails or output lacks a complete consistent execution summary
- **WHEN** the runner derives its outcome
- **THEN** it reports failure instead of inferring success from missing failure counts

#### Scenario: Output capture completes in either logging mode

- **GIVEN** a test process completes while console or file-output readers still have buffered data
- **WHEN** the runner determines counts and publishes its outcome
- **THEN** its counts and outcome reflect both fully captured streams, the complete summary, and the actual process result
- **AND** a failing process remains unsuccessful even if parsed failure counts are zero

### Requirement: Readiness verifies the required target stack

Deployment readiness SHALL verify required services, running tasks, and
applicable health checks within the target stack. Missing required services,
unhealthy or non-running required tasks, and failed inspection commands SHALL
NOT establish readiness. Waiting SHALL have a bounded deadline and failure
SHALL propagate to the caller.

#### Scenario: A required task is already unhealthy

- **GIVEN** required replica counts match but a required target-stack task is unhealthy
- **WHEN** readiness is checked
- **THEN** the stack is not declared healthy and cannot complete deployment successfully while that state persists

#### Scenario: Required services are missing or inspection fails

- **GIVEN** a required service or stack is absent, required replicas are missing, or a required inspection command fails
- **WHEN** readiness is evaluated
- **THEN** empty or incomplete inspection output cannot establish success
- **AND** persistent unready states fail by the configured deadline

#### Scenario: Expected inactive and unrelated services exist

- **GIVEN** unrelated unhealthy containers, intentionally zero-scaled services, or expected completed one-shot jobs coexist with a ready target stack
- **WHEN** readiness is evaluated
- **THEN** unrelated containers do not affect the result and declared inactive or completed jobs do not create false failures
- **AND** required active target-stack services still satisfy their own task and health checks

### Requirement: Dependabot preserves pin maintenance

The repository SHALL retain weekly `github-actions` version updates targeting
`test`, including the `docker-actions` and `attest` groups. The existing CI
test discovery SHALL exercise regression coverage for that configuration and
the SHA/version-comment reference format.

#### Scenario: Action update configuration remains compatible

- **GIVEN** the repository's action update configuration and pinned workflow references
- **WHEN** the existing CI test-discovery command runs
- **THEN** tests verify the weekly schedule, `test` target, and both update groups
- **AND** tests validate full SHA references with same-line release-version comments

### Requirement: Retained third-party actions have trust records

Dependency documentation SHALL contain a discoverable registry of every
retained third-party action, with its upstream owner, exposure, and retention
rationale. It SHALL record explicit decisions and reasons for Trivy and the
Cosign installer. Current dependency versions SHALL be derived from workflow
references rather than a separately maintained version list.

#### Scenario: Inventory and registry agree

- **GIVEN** the implemented workflow inventory
- **WHEN** a maintainer follows the dependency documentation index
- **THEN** every retained third-party action has an inventory entry and documented owner, exposure, and rationale
- **AND** the dispositions of `aquasecurity/trivy-action` and `sigstore/cosign-installer` are recorded

### Requirement: Dependency inventory follows workflow references

The generated Actions inventory SHALL include each active external action
path, its upstream owner/source, release version, full commit, and workflow
locations, including GitHub-owned actions. Local references and commented-out
steps SHALL be excluded. Different releases of the same action SHALL remain
distinguishable.

#### Scenario: Changed workflow dependencies refresh the inventory

- **GIVEN** active workflow dependencies have been added, removed, or updated
- **WHEN** the standard dependency-documentation generator runs
- **THEN** the generated inventory reflects the resulting workflow references and locations
- **AND** obsolete entries disappear and differing releases remain distinguishable
- **AND** local references and commented-out actions produce no inventory entries

#### Scenario: External reusable workflow calls appear in the inventory

- **GIVEN** a workflow contains a job-level external reusable call and a step-level action, each with a full SHA and release comment
- **WHEN** the standard inventory generator runs
- **THEN** both calls appear with their own action path, release, commit, and workflow location
- **AND** a job-level local reusable call remains excluded

### Requirement: Inventory refresh uses the existing documentation process

Actions inventory generation SHALL run through the existing dependency
documentation and pre-commit process without network access or credentials.
It SHALL preserve authored rationale and instructions, produce deterministic
output, and signal changed generated files using the existing process.

#### Scenario: Pre-commit refresh preserves authored documentation

- **GIVEN** workflow references changed and the dependency page contains authored instructions
- **WHEN** the existing documentation pre-commit hook runs
- **THEN** the inventory is refreshed and changed files are reported
- **AND** authored instructions and rationale remain unchanged
- **AND** another generation run without input changes produces no diff

### Requirement: Action maintenance follows ordinary dependency updates

Actions updates SHALL use the existing Dependabot, human dependency-review,
and documentation-refresh process. Documentation SHALL add instructions only
where relevant and SHALL NOT require a separate maintenance workflow,
scheduled trust reviews, recurring review-date bookkeeping, or special
approvals for routine dependency updates.

#### Scenario: A routine Dependabot action update is reviewed

- **GIVEN** Dependabot proposes an action SHA and release-comment update
- **WHEN** the normal dependency review and documentation refresh take place
- **THEN** the workflow pin and generated inventory reflect the selected release
- **AND** no additional Actions-only maintenance procedure is required

#### Scenario: Bot changes use existing refresh points

- **GIVEN** the shared documentation CI excludes Dependabot source branches
- **WHEN** a Dependabot PR is opened
- **THEN** no Actions-specific privileged bot execution path is required
- **AND** the inventory is refreshed at the existing pre-commit or dependency-documentation refresh points

### Requirement: Dependency updates preserve compatibility and explain material risk

Action dependency changes SHALL preserve the required runner, input, output,
and workflow behavior. Material compatibility or security constraints that
affect the selected release SHALL be explained with the dependency update,
including relevant trust in nested actions and downloaded tools.

#### Scenario: A selected release has a relevant constraint

- **GIVEN** a release assessment identifies a relevant compatibility limitation or published vulnerability
- **WHEN** the dependency update is prepared for normal human review
- **THEN** the chosen release and material constraint or residual risk are explained with source evidence
- **AND** the assessment distinguishes the action wrapper from its nested dependencies and executable defaults

### Requirement: Execution fixtures select isolated operational commands

Execution regression fixtures SHALL preserve executable permissions and
verify that operational commands resolve to their fixture stubs before
executing the local or emulated remote command chain. Missing or unusable
stubs SHALL fail without falling through to real deployment commands.
Negative controls SHALL establish the intended failure stage rather than
accepting any unrelated nonzero result.

#### Scenario: Linux executes the combined fixture

- **GIVEN** command stubs copied into an isolated execution fixture
- **WHEN** the combined workflow chain runs on Linux
- **THEN** the copied commands remain executable and local and emulated remote command resolution selects the stubs
- **AND** a missing, non-executable, or shadowed stub stops the fixture before operational execution

#### Scenario: A negative control fails for an unrelated reason

- **GIVEN** a fixture intends to exercise a named deployment, runner, or result-validation failure
- **WHEN** the operation fails at another stage or never creates its prerequisite current outcome
- **THEN** the fixture fails instead of accepting that unrelated error as coverage

### Requirement: Runner diagnostics do not disclose configured paths

Runner-owned console diagnostics and outcome messages SHALL use only
validated attempt identifiers and controlled failure stages. They SHALL NOT
include configured filesystem paths or raw caught exception text. Failure to
publish an error outcome SHALL remain nonzero without disclosing the exception
through an uncaught traceback.

#### Scenario: An attempt uses a secret-backed output root

- **GIVEN** the runner obtains its output root from secret-backed settings or an explicit configuration value
- **WHEN** it creates and completes an attempt
- **THEN** runner-owned diagnostics identify the attempt without printing the configured root
- **AND** outcome identity, result status, and artifact paths retain their existing behavior

#### Scenario: A runner failure contains sensitive exception text

- **GIVEN** configuration, attempt creation, selection, migration, execution, summary, or publication raises an exception containing a synthetic sensitive value
- **WHEN** the runner reports failure
- **THEN** stderr and any published outcome message contain a controlled failure stage and omit that value and configured path
- **AND** the operation remains unsuccessful

#### Scenario: Error outcome publication also fails

- **GIVEN** a runner error is followed by an exception while publishing its error outcome
- **WHEN** the runner exits
- **THEN** it returns a nonzero status and emits a fixed publication diagnostic
- **AND** no uncaught traceback or raw exception value is printed

### Requirement: Dependency checks belong to the existing test suite

Action-reference validation and inventory generation SHALL have regression
coverage in the existing repository test suite, executed by its existing CI
test job. The tests SHALL exercise production parsing and generation behavior
rather than serving as the operational inventory generator.

#### Scenario: The existing test suite exercises inventory maintenance

- **GIVEN** action-reference and inventory-generation regression tests
- **WHEN** the existing CI test job runs
- **THEN** it executes those tests alongside the existing workflow and dependency-documentation tests
- **AND** the coverage detects invalid pins, stale inventory entries, authored-section changes, and non-idempotent generation

#### Scenario: Inventory expectations detect missing and unexpected rows

- **GIVEN** an isolated fixture with external step calls, external reusable calls, and local/commented calls
- **WHEN** inventory regression coverage compares output with independently defined expected rows
- **THEN** a missing external reusable row or an unexpected row causes the test to fail
- **AND** the expected rows are not computed by the production reference traversal

### Requirement: Dependency documentation remains durable

The dependency page SHALL describe enduring behavior, rationale, and relevant
operating instructions. It SHALL NOT contain the completion report of a
particular PR or require a temporary analysis snapshot as an inventory source
or supporting document.
Local test instructions SHALL name the dependency-generation discovery
pattern used by CI, and SSH lifecycle descriptions SHALL match the workflow.

#### Scenario: A maintainer reads dependency guidance after delivery

- **GIVEN** the Actions dependency page is reached from the documentation index
- **WHEN** a maintainer follows its maintenance and operational instructions
- **THEN** they remain meaningful independently of the originating PR
- **AND** the page does not depend on `.agents/analysis/github-actions-trust.json`

#### Scenario: Local test instructions include both generation suites

- **GIVEN** CI discovers dependency tests with `test_generate_*.py`
- **WHEN** a developer follows CONTRIBUTING's local regression commands
- **THEN** the same discovery pattern runs both Actions and JavaScript generation tests

#### Scenario: SSH documentation describes the actual step arrangement

- **GIVEN** the DEV workflow retrieves the current attempt's outcome and result files and has unconditional agent cleanup followed by VPN disconnection and result checking
- **WHEN** the dependency page describes the agent lifecycle
- **THEN** it accurately describes the shared identity and cleanup after SSH/SCP use
- **AND** it does not describe multiple separate SCP steps or cleanup as the workflow's final step

### Requirement: Retained scanner and signer integrations

Image publishing SHALL retain `aquasecurity/trivy-action` and
`sigstore/cosign-installer` with verified full commit SHA pins and documented
trust reviews. The retention rationale and remaining trust in downloaded
tools SHALL be recorded in the dependency registry.

#### Scenario: Pinning preserves scanning and signing

- **GIVEN** the existing image-publishing workflow
- **WHEN** external action dependencies are made immutable
- **THEN** both Trivy calls and the Cosign installer remain with verified SHA pins
- **AND** the existing SBOM, vulnerability-report, and signing behavior is preserved

### Requirement: Documented repository enforcement readiness

The repository SHALL provide a runbook covering compatible rollout to every
intended execution ref, separately approved policy activation, preservation
of other Actions settings, positive/negative probes, and recovery. Executing
the operations SHALL remain subject to their stated readiness and approval
prerequisites.

#### Scenario: Unprepared refs prevent activation

- **GIVEN** an intended release, default-branch, or manually dispatched workflow ref still uses mutable action references
- **WHEN** a maintainer follows the documented readiness procedure
- **THEN** the runbook requires deferring activation until that ref is prepared or explicitly retired from execution

#### Scenario: The runbook defines observable policy verification

- **GIVEN** a maintainer reviews the activation and recovery instructions
- **WHEN** the policy verification procedure is inspected
- **THEN** it specifies API readback of `sha_pinning_required: true`, a successful pinned control, and policy-specific rejection of a tag-pinned control
- **AND** it requires approval and excludes secrets, infrastructure access, publication, and write-token permissions from the probes
