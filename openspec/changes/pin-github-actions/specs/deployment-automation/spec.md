# Deployment automation

## Purpose

Make the DEV, TEST and production deployment scripts and their CI wrappers
report real failures, verify that the target stack is ready, and validate
requests before changing anything.

## ADDED Requirements

### Requirement: Required operation failures reach the caller

Required build, pull, stack removal, deployment, database clone and test
failures SHALL propagate through nested scripts and wrappers as nonzero
results, and dependent operations SHALL stop. Explicitly optional
operations SHALL keep their warning behavior without failing the run.

#### Scenario: A nested deployment operation fails

- **GIVEN** a required build, pull, removal or deployment command fails
- **WHEN** the containing scripts return to the workflow
- **THEN** the result stays nonzero, dependent operations do not run, and later logging cannot replace it with success

#### Scenario: Database cloning fails inside a container wrapper

- **GIVEN** the database clone exits unsuccessfully inside its container or terminal wrapper
- **WHEN** the wrapper and caller finish
- **THEN** the failure reaches the workflow and tests do not start

#### Scenario: An optional maintenance operation fails

- **GIVEN** only an optional operation such as memory compaction fails
- **WHEN** all required operations succeed
- **THEN** the warning is shown and the deployment succeeds

### Requirement: Successful deployments are recorded only after readiness

A deployment SHALL update the last-successful-deployment record only after
its required operations and readiness check succeed. A failed deployment
SHALL keep the previous record. No automatic rollback is performed.

#### Scenario: Deployment fails its final check

- **GIVEN** a deployment or its readiness check fails
- **WHEN** bookkeeping is reached
- **THEN** the operation fails and the previous record is unchanged

### Requirement: Readiness verifies the required target stack

Readiness SHALL require every required service of the target stack to have
running tasks that are healthy where a health check exists. Missing services,
unhealthy or non-running tasks and failed inspections SHALL NOT count as
ready. Waiting SHALL end at a deadline with failure. The readiness check
SHALL run under the deployment host's `python3`, version 3.6 or later.

#### Scenario: The deployment host provides Python 3.6

- **GIVEN** a deployment host whose `python3` is version 3.6
- **WHEN** a deployment wrapper runs the readiness check
- **THEN** the check evaluates the stack instead of failing on an unavailable module or argument

#### Scenario: A required task is unhealthy

- **GIVEN** replica counts match but a required task is unhealthy
- **WHEN** readiness is checked
- **THEN** the stack is not ready and the deployment fails at the deadline if the state persists

#### Scenario: Services are missing or inspection fails

- **GIVEN** a required service is absent or an inspection command fails or returns nothing
- **WHEN** readiness is evaluated
- **THEN** the result is not ready

#### Scenario: Unrelated or intentionally inactive services exist

- **GIVEN** unhealthy containers outside the stack, services scaled to zero by design, or completed one-shot jobs
- **WHEN** readiness is evaluated for an otherwise ready stack
- **THEN** they do not cause a failure

### Requirement: Deployment requests are validated before side effects

The test and production deployment scripts SHALL validate the whole request
before any log setup, Swarm check, Docker or network operation, and reject
unsupported options, missing or invalid tags, invalid sources and unexpected
operands with a nonzero exit. A valid help request SHALL exit zero without
side effects.

#### Scenario: An unsupported option is supplied

- **GIVEN** an unsupported option, alone or after a valid one
- **WHEN** either script validates the request
- **THEN** it prints a diagnostic and exits nonzero without any Docker or file-system side effect

#### Scenario: Help is requested

- **GIVEN** `-h` alone or with other valid options, including on a host without Swarm
- **WHEN** the script accepts the request
- **THEN** it prints usage and exits zero without side effects

#### Scenario: A supported mode is selected

- **GIVEN** a valid request without help
- **WHEN** the script dispatches it
- **THEN** the existing source and tag selection, operation order and mode behavior are unchanged

### Requirement: Deployment entry points keep their diagnostics and logs

Each entry point SHALL report a missing Swarm with an explicit diagnostic and
a nonzero exit before dependent work. Log rotation SHALL delete only old
deployment logs under the existing age policy and keep the current log and
unrelated files. Removing an absent stack SHALL be a no-op.

#### Scenario: Swarm is not available

- **GIVEN** `docker node ls` fails
- **WHEN** a deployment entry point starts
- **THEN** it prints the Swarm diagnostic, exits nonzero, and runs no build, pull or deployment

#### Scenario: Old logs exist

- **GIVEN** old and recent deployment logs, the current log and unrelated files
- **WHEN** rotation runs
- **THEN** only old deployment logs are removed

#### Scenario: A stack is removed

- **GIVEN** an existing stack, an absent stack or a failing inspection
- **WHEN** either entry point requests removal
- **THEN** an existing stack is removed, an absent stack is skipped successfully, and inspection or removal failures stop the operation

### Requirement: DEV operations require exactly one current web container

Database cloning and test launch on DEV SHALL each find exactly one running
web container of the DEV Swarm service when they start. No container, several
containers or a failed lookup SHALL stop the operation before its command
runs.

#### Scenario: Container lookup does not yield one container

- **GIVEN** Docker lists zero or several matching containers, or the lookup fails
- **WHEN** cloning or test launch resolves its container
- **THEN** it fails before running its command

### Requirement: Manual deployment can select older release tags

The deployment workflow SHALL run the deployment code of the requested
release tag on the server, including tags older than the workflow's own
helper scripts. Guidance SHALL state that an older tag keeps its historical
failure handling.

#### Scenario: The requested tag predates the workflow helpers

- **GIVEN** the selected release tag does not contain the SSH helper used by the current workflow
- **WHEN** the deployment job prepares and sends its SSH command
- **THEN** it uses the helper from the workflow revision and the server deploys the requested tag

#### Scenario: A maintainer rolls back to an older tag

- **GIVEN** an older tag whose wrapper can report success despite a failed readiness check
- **WHEN** the maintainer follows the deployment guidance
- **THEN** the guide requires independent verification of the deployed version and stack readiness
