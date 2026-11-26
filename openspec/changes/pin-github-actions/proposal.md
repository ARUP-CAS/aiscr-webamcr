# Proposal

Source: [ARUP-CAS/aiscr-webamcr#4394](https://github.com/ARUP-CAS/aiscr-webamcr/issues/4394).
Pull request: [ARUP-CAS/aiscr-webamcr#4544](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4544).

## Why

Workflows that receive SSH keys, registry credentials and image-signing
permissions referenced their actions by mutable tags. They need immutable
references and recorded trust decisions before repository-wide SHA enforcement
can be enabled.

The only DEV run of the first implementation reported success without running
any tests. Investigating it exposed pre-existing gaps through which the DEV
Selenium pipeline could also report success after a crash, a failed deployment
or with results from an earlier run. The workflow change cannot be accepted
while its only live check is unreliable, so this change also makes that check
trustworthy.

## What Changes

### Action trust (the issue's scope)

- Pin every external `uses:` reference to a verified 40-character commit SHA
  with a same-line release comment, selecting the latest compatible releases.
  Local `./` calls stay unchanged.
- Replace `webfactory/ssh-agent` with native `ssh-agent`, limit both SSH keys
  to the step that loads them, and stop each agent on every exit.
- Pass manual workflow inputs and reference names as data, validating them
  before VPN or SSH.
- Keep `aquasecurity/trivy-action` and `sigstore/cosign-installer` with pins
  and recorded rationale.
- Generate the Actions inventory through the existing dependency-documentation
  generator and pre-commit hook. The parser rejects ambiguous release comments
  and duplicate YAML keys.
- Keep the existing Dependabot configuration and human review. Add no separate
  Actions maintenance process.
- Document the runbook for enabling `sha_pinning_required`. Executing it is
  follow-up.

### DEV test results (found during delivery)

- Detach deployment and test commands from the remote script's stdin.
- Read the downloaded summary as data instead of executing it.
- Fail on migration errors, crashes, incomplete output and zero executed tests.
  Report skips and expected failures separately from passes.
- Report why a failed run failed: the runner names the stage, the exception
  type and its message with configured result paths removed, and the
  workflow shows that cause in its summary and as an annotation.
- Bind published results to the GitHub run attempt. Each run empties a
  `current/` result directory and keeps the preceding run in `previous/`. The
  workflow rejects a missing or mismatched outcome.
- Keep the previous workbook as selection input for failed-only and numbered
  runs.
- Release Selenium drivers when workbook writing fails, and classify each
  workbook row by that test's own result.
- Serialize DEV tests and DEV deployments in one concurrency group.

### Deployment automation (found during delivery)

- Propagate required build, pull, removal, deployment, clone and test failures
  through all wrappers. Record a successful deployment only after the
  readiness check passes.
- Check readiness against the target stack's required services and health.
- Validate deployment requests and help before any side effect. Share the
  repeated helper code and rotate old deployment logs.
- **Production impact:** `scripts/prod_deploy.sh` is the documented production
  command. It gains failure propagation, request validation and a sourced
  helper, but no `set -e`.

### Simplification in this revision

- Replace the ten-run retention, lock files and compatibility code for a
  result format that was never deployed with the `current/` and `previous/`
  directories.
- Remove `set -eo pipefail` from `scripts/prod_deploy.sh`.

### Scope freeze

Further review findings are fixed in this PR only when this PR introduced them
and they are Critical or High. Other findings, including pre-existing
observations, go to a follow-up issue.

This change affects CI/CD security policy and deployment and test automation.
Production Django behavior, business data and governance rules are
unaffected. Out of scope: container image pinning, replacing `docker/*`
actions, automatic rollback, and other repositories.

## Capabilities

### New Capabilities

- `github-actions-trust`: Immutable action references, workflow SSH key
  handling, safe workflow inputs, the generated inventory, retained-action
  rationale, ordinary maintenance and the enforcement runbook.
- `ci-test-results`: DEV test runs publish only results produced by the
  current run, with complete counts and reliable Selenium cleanup.
- `deployment-automation`: Deployment scripts and wrappers report real
  failures, verify readiness and validate requests before side effects.

### Modified Capabilities

None. The repository has no durable capability specs yet.

## Impact

- Workflows: the six files in `.github/workflows/`.
- Test runner and results: `webclient/run_tests.py`,
  `webclient/test_run_results.py`, the test-only output setting,
  `webclient/core/tests/test_selenium.py`, `scripts/collect_test_results.py`.
- Deployment: `scripts/prod_deploy.sh`, `scripts/test_deploy.sh`,
  `scripts/start_selenium_tests.sh`, both `scripts/ci_deployment/` wrappers,
  and new `scripts/deployment_helpers.sh`, `scripts/ssh_arguments.sh` and
  `scripts/check_stack_ready.py`.
- Documentation: `docs/generate_module_docs.py`,
  `docs/source/12_zavislosti/github_actions.rst`, the deployment and Selenium
  guides, generated script pages, and `CONTRIBUTING.md`.
- Tests: focused regression suites under `scripts/`, run by the existing CI
  test job.
- Governance: generated assistant assets come from the `aiscr-management`
  baseline recorded in `.agents/delivery-manifest.json`. This change needs no
  hub delivery or sync.

Follow-up outside this change includes the DEV and TEST live checks, an
observed Dependabot update, promotion to `main`, and policy activation with
its probes. See [tasks.md](tasks.md#workflow-follow-up).
