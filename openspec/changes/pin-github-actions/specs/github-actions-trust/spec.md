# GitHub Actions trust

## Purpose

Keep workflow action dependencies immutable and reviewable while preserving SSH
testing, automated updates, and a documented path to safe policy activation.

## ADDED Requirements

### Requirement: Immutable external action references

Every active external `uses:` reference in repository workflow files SHALL use
a full 40-character commit SHA and a same-line comment naming its associated
release version. This applies to GitHub-owned and third-party actions alike.

#### Scenario: External actions have verified release pins

- **GIVEN** a workflow references an external action, including an action subpath
- **WHEN** the dependency revision is reviewed
- **THEN** the reference contains a full commit SHA verified in the upstream repository
- **AND** its same-line version comment identifies the release associated with that commit

#### Scenario: Mutable or incomplete references are rejected

- **GIVEN** an active external action uses a tag, branch, shortened SHA, or missing version comment
- **WHEN** workflow dependencies are validated
- **THEN** validation reports the offending workflow location and fails

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

The DEV test workflow SHALL stop its native SSH agent after its final use,
including when intervening remote execution or result retrieval fails.

#### Scenario: Failure still releases the agent

- **GIVEN** native SSH-agent initialization succeeded
- **WHEN** a subsequent SSH or SCP step fails
- **THEN** the workflow attempts agent cleanup through an unconditional cleanup step

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

### Requirement: Dependency documentation remains durable

The dependency page SHALL describe enduring behavior, rationale, and relevant
operating instructions. It SHALL NOT contain the completion report of a
particular PR or require a temporary analysis snapshot as an inventory source
or supporting document.

#### Scenario: A maintainer reads dependency guidance after delivery

- **GIVEN** the Actions dependency page is reached from the documentation index
- **WHEN** a maintainer follows its maintenance and operational instructions
- **THEN** they remain meaningful independently of the originating PR
- **AND** the page does not depend on `.agents/analysis/github-actions-trust.json`

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
