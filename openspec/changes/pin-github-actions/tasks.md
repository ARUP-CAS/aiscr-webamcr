# Tasks

Source: [ARUP-CAS/aiscr-webamcr#4394](https://github.com/ARUP-CAS/aiscr-webamcr/issues/4394).
Contracts: [github-actions-trust](specs/github-actions-trust/spec.md),
[ci-test-results](specs/ci-test-results/spec.md) and
[deployment-automation](specs/deployment-automation/spec.md).
Approach: [design.md](design.md).

Groups 1-4 summarize the work delivered in `0735cb560`..`f11aa5629`. The
round-by-round history is in [design.md](design.md#review-history). Groups 5
and 6 are the simplification revision. Group 7 covers the live DEV runs,
review rounds nine to thirteen and a leaked test annotation in hosted
pre-commit.

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

## 7. Live DEV runs and review rounds nine to thirteen

- [x] 7.1 Make `scripts/check_stack_ready.py` run on the deployment host's Python 3.6, as found by the [DEV run](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45771045340/job/139747914273): pass the inspection deadline explicitly instead of through `contextvars`, and call `subprocess.run` with `stdout` and `stderr` pipes and `universal_newlines` instead of `capture_output` and `text`. Record the 3.6 floor in the module docstring. Adapt `scripts/test_pre_commit_stack_ready.py` and add a guard that parses the script with the Python 3.6 grammar and rejects later standard-library modules and `subprocess.run` arguments. Verify with the stack-ready and deployment fixtures on Windows and isolated Linux. Optionally, with separate approval, run the script in a `python:3.6-slim` container without Docker and confirm that it reports the inspection failure instead of an import error or `TypeError`. The DEV rerun in the workflow follow-up is the live confirmation.
- [x] 7.2 Correct the manual Compose section of `docs/source/02_instalace_nasazeni/nasazovani.rst` (round-nine observation O16, a deliberate exception to the scope freeze): `amcr_image`, `redis_image` and `proxy_image` select the images with registry and tag, and `IMAGE_TAG` only passes the version to the application containers. Verify with a strict Sphinx build of the page.
- [x] 7.3 Repeat the 6.1 checks, regenerate the script documentation with the existing generators, and update the rolling usage entry.
- [x] 7.4 Capture runner and report output in `scripts/test_pre_commit_execution.py`, so no fixture line reaches the CI log, where `::error::Selhalo 1 testů` became a false annotation in the [pre-commit job](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45895469093/job/140168151293) (a deliberate exception to the scope freeze). Assert that the report prints the annotation only when tests failed. Verify that both `scripts` suites leave stdout empty on Windows and isolated Linux.
- [x] 7.5 In `select_tests` of `webclient/run_tests.py`, accept a test name when every dotted part is a Python identifier (`str.isidentifier()`), replacing the ASCII-only pattern. In the [DEV run](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45895898223/job/140169581355), that pattern rejected the 17 Selenium tests with Czech letters in their names, so every full run ended as an error at publication. Use a real non-ASCII name, such as `ez.tests.test_selenium.AkceExterniZdroj.test_117_zapsani_externího_zdroje_p_001`, in the selection, publication and pipeline fixtures, and keep rejecting a name with a non-identifier part. Verify that the new fixtures fail against the current pattern and pass after the change, on Windows and isolated Linux.
- [x] 7.6 Report the failure cause as described in [design.md](design.md#runner-diagnostics), a deliberate exception to the scope freeze:
  - in `webclient/run_tests.py`, print and record `Chyba testovacího běhu (<stage>): <type>: <message>`, with the results root replaced in its configured, absolute and resolved forms, control characters turned into spaces and the length bounded;
  - in `webclient/test_run_results.py`, accept only a single bounded message line;
  - in `scripts/collect_test_results.py`, show the cause of an error outcome in the step summary and as one escaped `::error::` annotation;
  - replace the stage-only fixtures with fixtures for a secret-backed root, a message containing the configured and resolved root, workflow-command text in the cause and a failing error publication;
  - update the diagnostics paragraph in `docs/source/12_zavislosti/github_actions.rst`.

  Verify on Windows and isolated Linux. After push, the hosted CodeQL run must report no `py/clear-text-logging-sensitive-data` alert; otherwise fall back to the runner's own messages and the exception type.
- [x] 7.7 Repeat the 6.1 checks, regenerate the script documentation with the existing generators, and update the rolling usage entry.
- [x] 7.8 Restrict `DEFAULT_TESTS` in `webclient/run_tests.py` to the 11 Selenium modules, as described in [design.md](design.md#dev-runs-only-selenium-tests): remove the two Fedora integration modules and the four #4450 modules. The [failed-only DEV run](https://github.com/ARUP-CAS/aiscr-webamcr/actions/runs/45959732625/job/140374449093) reported success because their 68 failures never reached the workbook. Add a regression test that parses each default module and fails, naming the module, when a class with test methods does not derive from `BaseSeleniumTestClass`, directly or through a class in the same module such as `AkceTestClass`. Update the Fedora section of `docs/source/09_testovani/integracni_testy.rst`, which still lists both integration modules in the full DEV run: they now run only through its manual Docker command. Verify that the test fails against the current list and passes after the change, on Windows and isolated Linux, and that no fixture depends on a removed module.
- [x] 7.9 In `docs/source/02_instalace_nasazeni/nasazovani.rst`, replace `./logs/git_prod_deploy` (line 167) with `./scripts/git_prod_deploy.sh` and `logs/git_prod_deploy.sh -h` (line 169) with `./scripts/git_prod_deploy.sh -h` (round-ten observation O17, a deliberate exception to the scope freeze). Keep `logs/git_prod_deploy` on line 168, which names the script's log directory. Verify with a strict Sphinx build of the page.
- [x] 7.10 In `extract_docstrings` of `docs/generate_module_docs.py`, render positional-only, `*args`, keyword-only and `**kwargs` parameters in function signatures, with a bare `*` before keyword-only parameters when there is no `*args` (round-ten observation O18, a deliberate exception to the scope freeze). Add a generator regression test that fails against the current extraction, then regenerate with the existing hook. The same extraction feeds the Django module pages, so 99 signatures on 28 pages change: the six script functions `log_msg`, `docker`, `git_output`, `_compose`, `_library` and `vprint`, and mostly `**kwargs` on signal receivers. Verify that no signature loses or renames a parameter, that regeneration is idempotent, and that a strict Sphinx build of every changed page adds no diagnostic.
- [x] 7.11 Repeat the 6.1 checks, regenerate the script documentation with the existing generators, and update the rolling usage entry with DEV runs 45911203331 and 45959732625 and round ten, replacing its stale statement that the 7.6 checkbox is uncommitted.
- [x] 7.12 In `BaseSeleniumTestClass` (`webclient/core/tests/test_selenium.py`), record an ERROR row for a test whose `setUp` fails, as described in [design.md](design.md#every-failed-test-keeps-a-workbook-row) (round-eleven Medium finding, a deliberate exception to the scope freeze):
  - move the workbook read, padding and write out of `_record_test_result` into a function that takes the status and does not use the driver; `_record_test_result` keeps classifying the result and calls it;
  - register a cleanup in `setUp` before any setup step. The cleanup writes an ERROR row only when `tearDown` has not started and this test is among the result's errors, so a skip or a normal run writes no second row;
  - in `scripts/test_pre_commit_selenium_lifecycle.py`, extract the new function with the other methods. Cover a setup failure before driver creation (a failing database clone), at driver creation (a failing `webdriver.Remote`) and after it (the existing `setup_error` fixture), each producing exactly one ERROR row for the test, with the setup error as the only reported error and a created driver released once. Also cover a skip raised in `setUp`, which writes no row, and a passing and a failing test, which each still write exactly one row.

  Verify that the new cases fail against the current class and pass after the change, on Windows and isolated Linux.
- [x] 7.13 In `webclient/run_tests.py`, before a completed outcome is published, compare the FAIL and ERROR rows of `current/results.xlsx` with `counts["failed"]`. When they differ, raise an error that states both counts, so the run publishes an error outcome and the root workbook is not replaced (round-eleven Medium finding, a deliberate exception to the scope freeze). `selection_content` already validates the current workbook with `select_tests("neuspesne", "", current)`; reuse that result instead of reading the workbook again. In `scripts/test_pre_commit_execution.py`, cover a full, a failed-only and a numbered run whose workbook lacks a failed test's row, each ending as an error with the root workbook unchanged, and a full run whose failed rows match, followed by a failed-only run that selects them. Verify that the new cases fail against the current runner and pass after the change, on Windows and isolated Linux.
- [x] 7.14 Repeat the 6.1 checks, regenerate the script documentation with the existing generators, and update the rolling usage entry with round eleven, DEV run 45999248513, tasks 7.12 and 7.13 and F1's tracking in #4570.
- [x] 7.15 In `CustomTextTestResult._exc_info_to_string` of `webclient/core/tests/runner.py`, read `progress_index` with a default and skip the test-number prefix when it is absent, so a class-level `setUpClass` error reported by unittest as an `_ErrorHolder` is recorded instead of aborting the run with `AttributeError` (round-twelve observation O19, fixed in round thirteen as a deliberate exception to the scope freeze). Add `CustomResultTests` to `scripts/test_pre_commit_selenium_lifecycle.py`: a class-setup failure keeps the result usable, and a normal numbered failure keeps its prefix. Verify both cases fail against the pre-fix method and pass after it, run the `scripts` suites, and regenerate the script page.
- [x] 7.16 Narrow the "A failure has no workbook row" scenario in [specs/ci-test-results/spec.md](specs/ci-test-results/spec.md#requirement-every-failed-test-of-a-completed-run-has-a-workbook-row) to runs that execute test bodies, add a single-class setup scenario that ends with the missing-summary error, align the requirement's error wording with both scenarios, and update the rolling usage entry and this task list with the O19 guard and the two round-thirteen record findings.

## Workflow follow-up

These steps are outside this change's completion and each needs its own approval.

- Update the PR title and description: add a reading order (workflows and pins, runner and results, deployment scripts, generated docs, OpenSpec) and an explicit note on the `scripts/prod_deploy.sh` changes.
- Before merge, dispatch a full `Run tests` from the PR branch with deployment enabled, then with deployment disabled. Record run URLs, revisions and attempt IDs. Both runs are expected to pass, because DEV runs only Selenium tests. The single-test run 45999248513 (attempt 2) already passed deployment, readiness and publication at `64cdbd48b`.
- Ask the owner of [ARUP-CAS/aiscr-webamcr#4465](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4465), in a comment that needs its own approval, to add `core.tests.test_organization_ownership` and `heslar.tests.test_organization_import_guard` to its inventory when rebasing, so every test removed from DEV runs there.
- After merge into `test`, the first TEST deployment of a release containing this change is the first live run of `prod_deploy.sh`. Verify the deployed version and stack readiness before any production deployment.
- File follow-up issues for pre-existing review observations deferred by the scope freeze. Optionally, add Selenium screenshots to the workflow artifact.
- Add round-ten finding F1 to [ARUP-CAS/aiscr-webamcr#4570](https://github.com/ARUP-CAS/aiscr-webamcr/issues/4570), which already covers the SSH and VPN steps of both workflows: extract the ssh-agent key-load block shared by `deployment.yml` and `run-tests.yml` into a helper loaded from the workflow revision, and apply the `~/.ssh` and `known_hosts` permissions in both. Revise the issue through its issue workflow; the write needs its own approval. Round eleven left F1 open until the issue mentions it.
- After the round-eleven fixes are pushed, reply on the F1 thread with the revised #4570 and on the round-eleven Medium thread; posting needs its own approval. Round eleven confirmed O17 and O18.
- Decide whether the two Fedora integration modules should get their own DEV step with separate reporting. Since task 7.8 they run only through the manual Docker command in the integration-test guide.
- Observe a Dependabot PR that updates both a SHA and its release comment.
- Promote the pinned workflows to `main` and audit every other ref intended to run.
- Enable only `sha_pinning_required`, read it back, and run the pinned and tag-pinned probes.
- Reconcile this evidence with the issue's acceptance criteria before closing the issue.
- Sync specs or archive this change only on explicit instruction.
