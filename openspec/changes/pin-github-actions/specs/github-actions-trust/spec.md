# GitHub Actions trust

## Purpose

Keep workflow action dependencies immutable and reviewable, keep SSH
credentials and workflow inputs safe, and document a safe path to
repository-wide SHA enforcement.

## ADDED Requirements

### Requirement: Immutable external action references

Every active external `uses:` reference in repository workflows SHALL use a
full 40-character commit SHA with a same-line comment naming its release.
This applies to GitHub-owned and third-party actions. Each release comment
SHALL belong unambiguously to one external call.

#### Scenario: External actions have verified release pins

- **GIVEN** a workflow references an external action, including an action subpath
- **WHEN** the dependency revision is reviewed
- **THEN** the reference contains a full commit SHA verified in the upstream repository
- **AND** its same-line comment identifies the release of that commit

#### Scenario: Mutable or incomplete references are rejected

- **GIVEN** an active external action uses a tag, branch, shortened SHA or no version comment
- **WHEN** workflow dependencies are validated
- **THEN** validation fails and reports the workflow location

#### Scenario: Several calls cannot share one release comment

- **GIVEN** a flow-style YAML line contains several external calls and one trailing comment
- **WHEN** workflow dependencies are validated or inventoried
- **THEN** processing fails with the workflow location

#### Scenario: Unambiguous flow syntax remains supported

- **GIVEN** a flow-style mapping contains one pinned external call with its release comment
- **WHEN** workflow dependencies are validated
- **THEN** the call is accepted without conversion to block style
- **AND** version-like text inside another quoted value does not count as a comment

### Requirement: Duplicate workflow mapping keys are rejected

Workflow dependency validation SHALL reject duplicate YAML mapping keys with
file and line diagnostics before extracting action references.

#### Scenario: A duplicate key cannot hide an action reference

- **GIVEN** a workflow mapping repeats a key, such as a pinned `uses` followed by a mutable `uses`
- **WHEN** workflow dependencies are validated or inventoried
- **THEN** processing fails at the duplicate key's location
- **AND** no partial inventory replaces the existing documentation

### Requirement: Local workflow references remain local

Same-repository `./` workflow references SHALL remain unchanged and SHALL be
excluded from the SHA and release-comment requirement.

#### Scenario: Publishing uses the caller's local workflow

- **GIVEN** the release workflow calls `./.github/workflows/publish_images.yml`
- **WHEN** external action dependencies are validated
- **THEN** the local call passes validation unchanged

### Requirement: Native SSH authentication across workflow steps

The DEV test workflow SHALL load its configured key with native SSH-agent
tooling instead of `webfactory/ssh-agent`. The loaded identity SHALL remain
available to the later SSH and SCP steps. The private key SHALL NOT appear in
logs, cross-step state or artifacts.

#### Scenario: SSH and result retrieval share the agent

- **GIVEN** a valid key and isolated steps whose remote clients are replaced by fixtures
- **WHEN** the setup, SSH and result-retrieval steps run
- **THEN** the SSH and SCP clients use the same loaded identity
- **AND** only the agent socket and PID are passed between steps

#### Scenario: Key loading fails safely

- **GIVEN** the configured private key cannot be loaded
- **WHEN** agent initialization runs
- **THEN** the step fails before any remote execution
- **AND** the private key is absent from logs and artifacts

### Requirement: SSH-agent cleanup

The DEV test and deployment workflows SHALL stop their SSH agents after last
use, including when key loading, remote execution or result retrieval fails.
Cleanup SHALL NOT turn a failed operation into success.

#### Scenario: A later SSH or SCP step fails

- **GIVEN** the DEV test workflow initialized its agent
- **WHEN** a later SSH or SCP step fails
- **THEN** an unconditional cleanup step stops the agent
- **AND** the job remains failed

#### Scenario: Deployment releases its single-step agent

- **GIVEN** deployment creates its agent within the SSH step
- **WHEN** key loading fails, remote execution fails or remote execution completes
- **THEN** the step stops the agent before exiting and keeps the original result

### Requirement: SSH private keys have step-scoped exposure

Both SSH workflows SHALL expose their private key only to the step that loads
it, read it from that step's environment without shell tracing, and SHALL
NOT place it in job-wide environment, cross-step state, logs or artifacts.

#### Scenario: Other deployment steps do not receive the key

- **GIVEN** a deployment job with tag normalization, checkout, VPN and SSH steps
- **WHEN** its environment is configured
- **THEN** only the SSH step receives the private key

### Requirement: Workflow values remain data across shell boundaries

Manual inputs and reference names SHALL be consumed as data and SHALL NOT
become local or remote shell script text. Remote test execution SHALL use a
static script body with arguments quoted for both shell boundaries.

#### Scenario: Deployment tag content cannot execute

- **GIVEN** a deployment tag containing command substitution, quotes or a newline
- **WHEN** tag normalization processes the value
- **THEN** no embedded command executes and the invalid tag is rejected

#### Scenario: A test number cannot become a remote command

- **GIVEN** a test number containing shell syntax instead of digits
- **WHEN** the test workflow validates or transports its inputs
- **THEN** the value is rejected without executing locally or remotely
- **AND** no deployment or test command is invoked

#### Scenario: Reference names arrive literally

- **GIVEN** a valid reference name containing characters meaningful to a shell
- **WHEN** it is passed to the remote deployment command
- **THEN** the remote script receives the original value as one argument

### Requirement: Manual workflow inputs are validated before remote work

The deployment and test workflows SHALL validate deployment tags and test
selection before connecting the VPN or running SSH. Invalid input SHALL fail
without deployment or tests. Valid inputs, defaults, source selection and
test modes SHALL keep their behavior.

#### Scenario: Valid deployment tags keep their normalization

- **GIVEN** a release tag with or without a leading `v` and an optional supported prerelease suffix
- **WHEN** deployment inputs are validated
- **THEN** the Git tag keeps the `v` prefix and the image tag omits it

#### Scenario: Valid test modes keep their commands

- **GIVEN** `test_mod` is `vsechny`, `neuspesne` or `konkretni`, `nasadit_verzi` is a boolean, and any test number is decimal
- **WHEN** inputs are validated, requiring a number for `konkretni`
- **THEN** the selected test mode and optional deployment run as before

#### Scenario: Invalid test selections fail before connection

- **GIVEN** an unknown mode, a nonnumeric number, a missing number for `konkretni` or an invalid boolean
- **WHEN** the test workflow validates its inputs
- **THEN** it fails before VPN connection or SSH

### Requirement: Dependabot preserves pin maintenance

The repository SHALL keep weekly `github-actions` updates targeting `test`,
including the `docker-actions` and `attest` groups. The existing CI test job
SHALL cover that configuration and the SHA and release-comment format.

#### Scenario: Update configuration remains compatible

- **GIVEN** the action update configuration and pinned workflows
- **WHEN** the existing CI test discovery runs
- **THEN** tests verify the weekly schedule, the `test` target and both groups
- **AND** tests validate full SHA references with release comments

### Requirement: Retained third-party actions have trust records

Dependency documentation SHALL record every retained third-party action with
its owner, exposure and retention rationale, including explicit decisions
for Trivy and the Cosign installer. Both SHALL stay pinned with their
scanning and signing behavior preserved.

#### Scenario: Inventory and registry agree

- **GIVEN** the workflow inventory
- **WHEN** a maintainer follows the dependency documentation index
- **THEN** every retained third-party action has an inventory entry and documented owner, exposure and rationale

#### Scenario: Pinning preserves scanning and signing

- **GIVEN** the image-publishing workflow
- **WHEN** its external actions are pinned
- **THEN** both Trivy calls and the Cosign installer remain, with SBOM, vulnerability report and signing behavior unchanged

### Requirement: The Actions inventory is generated from workflow references

The existing dependency-documentation generator and pre-commit hook SHALL
derive the Actions inventory from active workflow references. Each entry
SHALL list action path, owner, release, full commit and workflow locations.
Local and commented calls SHALL be excluded. Generation SHALL run offline,
deterministically, and keep authored text.

#### Scenario: Changed references refresh the inventory

- **GIVEN** workflow dependencies were added, removed or updated
- **WHEN** the generator runs
- **THEN** the inventory matches the workflow references, obsolete rows disappear and different releases stay distinguishable

#### Scenario: Reusable workflow calls are inventoried

- **GIVEN** a job-level external reusable workflow call and a step-level action, both pinned
- **WHEN** the generator runs
- **THEN** both appear with their own path, release, commit and location
- **AND** a local reusable call remains excluded

#### Scenario: Refresh keeps authored documentation

- **GIVEN** the dependency page contains authored instructions
- **WHEN** the pre-commit hook refreshes the inventory twice without input changes
- **THEN** authored text is unchanged and the second run produces no diff

### Requirement: Action updates follow ordinary dependency maintenance

Action updates SHALL use the existing Dependabot, human review and
documentation refresh process, with no separate Actions workflow, scheduled
trust review or review-date bookkeeping. An update SHALL keep runner, input
and output behavior and explain material compatibility or security
constraints.

#### Scenario: A routine Dependabot update is reviewed

- **GIVEN** Dependabot proposes a new SHA and release comment
- **WHEN** the normal review and documentation refresh take place
- **THEN** the pin and the generated inventory reflect the selected release without an Actions-only procedure

#### Scenario: A selected release has a relevant constraint

- **GIVEN** an assessment finds a relevant compatibility limitation or published advisory
- **WHEN** the update is prepared for review
- **THEN** the chosen release and its residual risk are explained with sources
- **AND** the explanation distinguishes the action wrapper from nested actions and downloaded tools

### Requirement: Dependency documentation remains durable

The dependency page SHALL describe enduring behavior, rationale and operating
instructions. It SHALL NOT report the completion of a particular PR or depend
on a temporary analysis snapshot. Local test instructions SHALL use the same
discovery pattern as CI.

#### Scenario: A maintainer reads the guidance after delivery

- **GIVEN** the Actions page is reached from the documentation index
- **WHEN** a maintainer follows its instructions
- **THEN** they remain meaningful independently of the originating PR
- **AND** the page does not depend on `.agents/analysis/github-actions-trust.json`

#### Scenario: Local test instructions match CI

- **GIVEN** CI discovers dependency tests with `test_generate_*.py`
- **WHEN** a developer follows the local commands in `CONTRIBUTING.md`
- **THEN** the same pattern runs both the Actions and JavaScript generation tests

### Requirement: Documented repository enforcement readiness

The repository SHALL document rollout of pinned workflows to every intended
execution ref, separately approved activation of `sha_pinning_required` that
keeps other Actions settings, positive and negative probes, and recovery.
Executing these steps SHALL remain subject to their approvals.

#### Scenario: Unprepared refs prevent activation

- **GIVEN** an intended release, default-branch or manually dispatched ref still uses mutable references
- **WHEN** a maintainer follows the readiness procedure
- **THEN** the runbook requires deferring activation until that ref is prepared or explicitly retired

#### Scenario: Policy verification is observable

- **GIVEN** a maintainer reviews the activation and recovery instructions
- **WHEN** the verification procedure is inspected
- **THEN** it requires API readback of `sha_pinning_required: true`, a successful pinned control and a policy-specific rejection of a tag-pinned control
- **AND** the probes use no secrets, infrastructure access, publication or write-token permissions
