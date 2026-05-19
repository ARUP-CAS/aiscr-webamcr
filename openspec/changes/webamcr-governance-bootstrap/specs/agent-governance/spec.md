## ADDED Requirements

### Requirement: OpenSpec is the requirement surface for agent-governance changes
The repository SHALL use OpenSpec change artifacts to describe durable
agent-governance changes before implementation.

#### Scenario: Agent-governance change is proposed
- **GIVEN** an agent-governance change is planned for `aiscr-webamcr`
- **WHEN** the change affects repository policy, vendor surfaces, or hub-sync expectations
- **THEN** the change SHALL be captured under `openspec/changes/` before implementation

#### Scenario: OpenSpec artifacts are validated
- **GIVEN** OpenSpec artifacts are created or edited
- **WHEN** verification runs
- **THEN** `npx openspec validate --all` SHALL pass before the change is treated as ready

### Requirement: Vendor surfaces are tracked hub-synchronized content
The repository SHALL treat `.cursor/`, `.claude/`, `.codex/`, `.gemini/`,
`.clinerules/`, and `.qodo/` as repository-tracked agent-vendor surfaces when
they are materialized from the `aiscr-management` hub baseline.

#### Scenario: Vendor folders are restored
- **GIVEN** a declared vendor surface is missing from the repository
- **WHEN** hub configuration sync is approved and applied
- **THEN** the missing surface SHALL be restored from `aiscr-management/.agents/local_configs/aiscr-webamcr/`

#### Scenario: Vendor folders are reviewed
- **GIVEN** a vendor surface differs from the hub baseline
- **WHEN** alignment is evaluated
- **THEN** the difference SHALL be resolved by hub sync or recorded as an intentional override

#### Scenario: Specialized assets are included
- **GIVEN** the repository sync recipe selects specialized asset groups
- **WHEN** vendor surfaces are materialized from the hub baseline
- **THEN** the materialized surface SHALL include the selected rules, skills, agents, and reference files from those asset groups

### Requirement: Local bootstrap metadata records alignment state
The repository SHALL record bootstrap alignment metadata in
`.agents/local_overrides.toml`.

#### Scenario: Bootstrap metadata is refreshed
- **GIVEN** a governance bootstrap or alignment run changes the repository
- **WHEN** the run completes its write-capable steps
- **THEN** `.agents/local_overrides.toml` SHALL record the OpenSpec schema, alignment date, and hub revision used as the baseline

#### Scenario: Intentional drift is preserved
- **GIVEN** a tracked governance path intentionally differs from the hub baseline
- **WHEN** the difference is accepted by a maintainer
- **THEN** the override SHALL include the path, reason, added date, and review date

### Requirement: Hub sync apply remains approval-gated
The repository SHALL require a reviewed dry-run and explicit human approval
before applying hub configuration sync that writes vendor surfaces.

#### Scenario: Sync is previewed
- **GIVEN** vendor surfaces need to be populated or refreshed from the hub
- **WHEN** sync is prepared
- **THEN** a dry-run SHALL be produced before any apply command is run

#### Scenario: Sync apply is separate
- **GIVEN** a dry-run identifies expected vendor-surface writes
- **WHEN** the current run is scoped as dry-run only
- **THEN** no sync apply SHALL be executed in that run

### Requirement: Root governance describes the tracked-vendor posture
Root governance files SHALL describe the current tracked-vendor-folder posture
and SHALL NOT claim that synchronized vendor folders are gitignored local-only
content.

#### Scenario: AGENTS and CLAUDE are reviewed
- **GIVEN** `.gitignore` no longer excludes `.cursor/`, `.claude/`, or `.codex/`
- **WHEN** `AGENTS.md` and `CLAUDE.md` are read by assistants
- **THEN** they SHALL describe vendor surfaces as tracked, hub-synchronized repository content
