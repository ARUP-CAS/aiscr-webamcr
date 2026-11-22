# GitHub Actions trust

## Purpose

Keep workflow action dependencies immutable and reviewable while preserving SSH
testing, automated updates, and safely ordered repository policy enforcement.

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

#### Scenario: DEV execution and result retrieval share the agent

- **GIVEN** valid existing VPN, key, and known-host configuration
- **WHEN** an authorized manual DEV test run reaches SSH authentication
- **THEN** the remote test command connects successfully
- **AND** the later SCP steps retrieve the results using the same loaded identity

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
`test`, including the `docker-actions` and `attest` groups. Acceptance SHALL
include an actual Dependabot PR updating a pinned SHA together with its
same-line version comment; documentation of support alone is insufficient.

#### Scenario: A release update changes both SHA and comment

- **GIVEN** SHA-pinned action dependencies and a newer upstream release
- **WHEN** Dependabot opens the corresponding update PR
- **THEN** its diff updates both the action commit SHA and version comment
- **AND** the PR targets `test` and preserves applicable update grouping

### Requirement: Retained third-party actions have trust records

Dependency documentation SHALL contain a discoverable registry of every
retained third-party action, with its upstream owner, maintenance status,
last review date, review frequency, and trust rationale. The registry SHALL
record explicit decisions and reasons for Trivy and the Cosign installer.

#### Scenario: Inventory and registry agree

- **GIVEN** the implemented workflow inventory
- **WHEN** a maintainer follows the dependency documentation index
- **THEN** every retained third-party action has a registry entry with all required fields
- **AND** the dispositions of `aquasecurity/trivy-action` and `sigstore/cosign-installer` are recorded

### Requirement: Dependency reviews remain actionable

The documented maintenance procedure SHALL cover resolving and verifying
release SHAs and updating version comments. Trust records SHALL be reviewed
at least quarterly and on major updates or material security or ownership
changes.

#### Scenario: A maintainer adds or updates an action

- **GIVEN** a proposed external action dependency or release update
- **WHEN** a maintainer follows the documented procedure
- **THEN** the resulting pin is traceable to an upstream release commit
- **AND** the relevant trust record is reviewed when its review trigger applies

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

### Requirement: Repository enforcement follows compatible rollout

The repository SHALL enable `sha_pinning_required` only after the pinned
workflows have reached every ref intended to remain executable. Acceptance
SHALL include API evidence that the setting is true, a successful pinned
control, and rejection of a deliberately tag-pinned action in a harmless
authorized probe.

#### Scenario: Unprepared refs prevent activation

- **GIVEN** an intended release, default-branch, or manually dispatched workflow ref still uses mutable action references
- **WHEN** enforcement readiness is assessed
- **THEN** activation is deferred until that ref is prepared or explicitly retired from execution

#### Scenario: The repository rejects a mutable action

- **GIVEN** the compatible rollout is complete and enforcement is enabled with approval
- **WHEN** a harmless approved workflow probe references an action by tag
- **THEN** GitHub rejects the workflow for the SHA-pinning policy
- **AND** a pinned control remains executable and the policy API reports `sha_pinning_required: true`
