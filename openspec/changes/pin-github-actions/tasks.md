# Tasks

Source: [ARUP-CAS/aiscr-webamcr#4394](https://github.com/ARUP-CAS/aiscr-webamcr/issues/4394).
Contracts: [github-actions-trust](specs/github-actions-trust/spec.md),
[ci-test-results](specs/ci-test-results/spec.md) and
[deployment-automation](specs/deployment-automation/spec.md).
Approach: [design.md](design.md).

Groups 1-4 summarize the work delivered in `0735cb560`..`f11aa5629`. The
round-by-round history is in [design.md](design.md#review-history). Groups 5
and 6 are the simplification revision. Group 7 covers the first live DEV run,
review round nine and a leaked test annotation in hosted pre-commit.

## 1. Action pins and inventory

- [x] 1.1 Pin every external action to a verified SHA and release comment at the latest compatible release; verified by full-coverage parser tests and upstream commit readback.
- [x] 1.2 Harden the parser against mutable references, shared release comments and duplicate keys, with file and line diagnostics; verified by fixture mutations.
- [x] 1.3 Generate the inventory through `docs/generate_module_docs.py` and the existing hook, and align `CONTRIBUTING.md` with CI discovery; verified by exact, independently defined rows and idempotent regeneration.
- [x] 1.4 Write the Czech Actions dependency page with Trivy and Cosign rationale, maintenance and enforcement runbook, and remove the temporary JSON snapshot; verified by a strict documentation build and a reference search.
- [x] 1.5 Keep the Dependabot configuration; verified by the workflow regression suite.

## 2. Workflow SSH and inputs

- [x] 2.1 Replace `webfactory/ssh-agent` with a native agent shared across steps and stopped unconditionally; verified with a disposable key and isolated steps.
- [x] 2.2 Limit the deployment key to its SSH step and stop that agent through an EXIT trap; verified by lifecycle fixtures.
- [x] 2.3 Validate inputs before VPN and SSH, and pass them as quoted arguments to a static remote script through the shared helper loaded from the workflow revision; verified by canary, quoting and older-tag fixtures.
- [x] 2.4 Detach deployment and test commands from the remote script's stdin; verified by a stdin-consuming fixture in all three modes.

## 3. DEV test results

- [x] 3.1 Read the downloaded summary as bounded data; verified by valid, malformed, oversized and canary fixtures.
- [x] 3.2 Make runner outcomes reflect actual execution, with separate skip and expected-failure counts and no paths in diagnostics; verified by process, selection and canary fixtures on Windows and Linux.
- [x] 3.3 Bind published results to the run attempt, annotate failures from the validated report, and upload only the verified bundle; verified by producer and consumer fixtures.
- [x] 3.4 Register Selenium driver cleanup at creation and classify workbook rows per test; verified by lifecycle fixtures.
- [x] 3.5 Put DEV tests and DEV deployments in one concurrency group; verified by expression regressions.

## 4. Deployment automation

- [x] 4.1 Propagate required failures through the deployment scripts and wrappers, and record success only after readiness; verified by stubbed command-chain fixtures.
- [x] 4.2 Check readiness of the target stack with `scripts/check_stack_ready.py`; verified by health and inspection fixtures.
- [x] 4.3 Move repeated code into `scripts/deployment_helpers.sh`, add log rotation and the Swarm diagnostic, and remove unused state; verified by deployment fixtures.
- [x] 4.4 Validate test and production deployment requests and help before side effects; verified by option fixtures.
- [x] 4.5 Align the deployment runbook, Selenium guide and older-tag guidance; verified by strict documentation builds.

## 5. Result directory and production script simplification

- [x] 5.1 Replace the per-attempt directories and lock files with the `current/` and `previous/` rotation in `webclient/run_tests.py` and `webclient/test_run_results.py`, as described in [design.md](design.md#result-directories-and-run-identity). Delete `webclient/test_run_retention.py` and the v1 and duplicate-ID handling. Verify with runner fixtures for a first run, two consecutive runs (older `previous/` removed, root workbook unchanged), a symlinked directory (run fails, link target intact) and the existing completed, error, no-op and selection cases.
- [x] 5.2 Point `.github/workflows/run-tests.yml` at `/opt/selenium_test/current` and update the `scripts/start_selenium_tests.sh` usage text. Delete `scripts/test_pre_commit_retention.py` and update the execution and pipeline fixtures. Verify that the workflow, report and pipeline suites pass on Windows and isolated Linux, that a stale outcome left by the previous run is rejected, and that no reference to the per-attempt layout or retention module remains.
- [x] 5.3 Remove `set -eo pipefail` from `scripts/prod_deploy.sh` after confirming that every required operation checks its status explicitly. Verify with `bash -n` and the deployment fixtures:
  - failing pull, deployment, removal and the Swarm precondition still exit nonzero with their diagnostics;
  - a failing optional command no longer aborts the script;
  - validation, help and the valid modes are unchanged.
- [x] 5.4 Update `docs/source/12_zavislosti/github_actions.rst` and `docs/source/09_testovani/selenium_testy.rst`: describe the result layout, remove the retention narrative, and state that a manual run during a CI run is unsupported. Regenerate the script documentation with the existing generators so the retention pages and their index entries disappear. Verify idempotent regeneration and a strict Sphinx build of the affected pages.

## 6. Close-out

- [x] 6.1 Run these checks:
  - `compileall` and full pre-commit;
  - `scripts` test discovery on Windows and isolated Linux;
  - strict validation of this change and aggregate OpenSpec validation.

  Inspect the diff to confirm only the planned files changed.
- [x] 6.2 Update the single rolling usage entry for this change with runtime and model metadata, results and limits. No hub asset change or sync is planned; any future sync needs a reviewed dry run before a separately approved apply.

## 7. Live DEV run and review round nine

- [x] 7.1 Make `scripts/check_stack_ready.py` run on the deployment host's Python 3.6, as found by the [DEV run](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45771045340/job/139747914273): pass the inspection deadline explicitly instead of through `contextvars`, and call `subprocess.run` with `stdout` and `stderr` pipes and `universal_newlines` instead of `capture_output` and `text`. Record the 3.6 floor in the module docstring. Adapt `scripts/test_pre_commit_stack_ready.py` and add a guard that parses the script with the Python 3.6 grammar and rejects later standard-library modules and `subprocess.run` arguments. Verify with the stack-ready and deployment fixtures on Windows and isolated Linux. Optionally, with separate approval, run the script in a `python:3.6-slim` container without Docker and confirm that it reports the inspection failure instead of an import error or `TypeError`. The DEV rerun in the workflow follow-up is the live confirmation.
- [x] 7.2 Correct the manual Compose section of `docs/source/02_instalace_nasazeni/nasazovani.rst` (round-nine observation O16, a deliberate exception to the scope freeze): `amcr_image`, `redis_image` and `proxy_image` select the images with registry and tag, and `IMAGE_TAG` only passes the version to the application containers. Verify with a strict Sphinx build of the page.
- [x] 7.3 Repeat the 6.1 checks, regenerate the script documentation with the existing generators, and update the rolling usage entry.
- [x] 7.4 Capture runner and report output in `scripts/test_pre_commit_execution.py`, so no fixture line reaches the CI log, where `::error::Selhalo 1 testů` became a false annotation in the [pre-commit job](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45895469093/job/140168151293) (a deliberate exception to the scope freeze). Assert that the report prints the annotation only when tests failed. Verify that both `scripts` suites leave stdout empty on Windows and isolated Linux.

## Workflow follow-up

These steps are outside this change's completion and each needs its own approval.

- Update the PR title and description: add a reading order (workflows and pins, runner and results, deployment scripts, generated docs, OpenSpec) and an explicit note on the `scripts/prod_deploy.sh` changes.
- Before merge, dispatch `Run tests` from the PR branch with deployment enabled, then with deployment disabled. Record run URLs, revisions and attempt IDs.
- After merge into `test`, the first TEST deployment of a release containing this change is the first live run of `prod_deploy.sh`. Verify the deployed version and stack readiness before any production deployment.
- File follow-up issues for pre-existing review observations deferred by the scope freeze. Optionally, add Selenium screenshots to the workflow artifact.
- Observe a Dependabot PR that updates both a SHA and its release comment.
- Promote the pinned workflows to `main` and audit every other ref intended to run.
- Enable only `sha_pinning_required`, read it back, and run the pinned and tag-pinned probes.
- Reconcile this evidence with the issue's acceptance criteria before closing the issue.
- Sync specs or archive this change only on explicit instruction.
