# Django unit and import test CI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run all current non-Selenium Django unit and database tests, including import tests, in initially nonblocking GitHub Actions jobs.

**Architecture:** Two independent jobs consume explicit, disjoint module lists. Django runs directly on the runner; only the database job starts PostGIS and Redis service containers. Use Django's standard DiscoverRunner and a thin command wrapper for selection and reporting, without automatic classification or a custom Django runner.

**Tech Stack:** Python 3.12, Django, GitHub Actions, PostGIS, Redis, existing compiled test requirements.

**Spec:** [Approved design](2026-10-31-issue-4183-ci-design.md)

**Execution state:** Implementation delivered on the agent branch; verification
and remaining baseline failures are recorded in
`../reports/issue_4183_ci.md`. Fast tests and helper checks pass, but the existing
database suite is not green, so its all-green completion contract remains open.

## Global Constraints

- Run on pull requests targeting `main` or `test` and through manual dispatch.
- Initial checks must be nonblocking and require no VPN, deployed DEV server, or credentials for external application services.
- External integration tests are excluded even when they are not Selenium tests.
- Keep the existing `run-tests.yml` and Selenium execution unchanged.
- Do not make the new checks required, change production behavior, or add unrelated tests or repository script tests.
- Keep AI design and planning artifacts under `.agents/` as required by repository governance.
- Work on `agents/codex/4183-unit-test-ci`, created from `test`; require human review before merge.
- Do not edit ignored secrets, manually edit migrations, or stage unrelated existing artifacts.

## Review Focus

- New or renamed test modules must be identified as unassigned during inventory validation, rather than silently omitted.
- Mixed modules must run wholly in the database job; empty suites and duplicate labels must fail validation.
- `urgent` must see the same test database as `default`, while retaining the separate connection semantics exercised by existing tests.
- Setup errors must appear in summaries even when the test command never starts; test failures must retain their real outcome despite nonblocking checks.
- No job may require Fedora, a live Celery worker, ClamAV, Elasticsearch, or deployed HTTP endpoints; unexpected dependencies must be reported rather than silently skipped.
- User clarification: settings must disable external integrations and test execution must block all external network requests, including hard-coded URLs and native/subprocess clients.

## File responsibilities

- Modify `webclient/webclient/settings/github_ci.py`: isolated CI settings and standard runner.
- Create `.agents/config/django_ci_suites.json`: explicit `fast`, `database`, and `excluded` lists, with reasons for exclusions.
- Create `.agents/scripts/run_django_ci.py`: validate the inventory, launch a named suite, stream and retain output, write its summary, and return the child exit code.
- Create `.agents/scripts/django_ci_network.py` and `.agents/scripts/with_ci_network.sh`: fail Python network calls before DNS and restrict the unprivileged test user's IPv4/IPv6 traffic to local services; keep the Actions agent unrestricted.
- Create `.agents/scripts/test_django_ci.py`: regression checks for inventory coverage, reporting, and network enforcement; no new Django application tests.
- Create `.github/workflows/django-tests.yml`: runner setup, service health checks, two jobs, nonblocking behavior, summary and artifact publication.
- Create `.agents/reports/issue_4183_ci.md`: execution instructions, module-list maintenance, verification results, and limitations.

### Task 1: Make CI settings load and provision a fresh test database

**Interfaces:** `--settings=webclient.settings.github_ci` loads the standard `django.test.runner.DiscoverRunner`. CI database and Redis host/port values come from documented `AMCR_CI_*` environment variables, defaulting to localhost. No production settings are changed.

- [ ] Reproduce settings/runner loading with the existing compiled requirements in a Python 3.12 environment. Record the existing missing-runner failure. Use a disposable environment, not local ignored configuration.
- [ ] Change `github_ci.py` to import `base` rather than `dev`. Explicitly set the standard runner, `SKIP_SELENIUM_TESTS = True`, and `FEDORA_INTEGRATION_TESTS = False`. Supply test-only allowed hosts, local-memory email, ordinary static-file storage, disabled reCAPTCHA, and console-only logging. Disable ORM cacheops to avoid incidental Redis access in the fast job; keep the real Django Redis cache for the database job.
- [ ] Configure both aliases using localhost CI connection values. Set the `urgent` test alias to mirror `default`; verify this preserves behavior for the existing multi-connection tests. Keep migrations enabled, including GIS functions and identifier sequences. Never clone the DEV database.
- [ ] Start disposable PostGIS and Redis locally where available. Match PostGIS to `Dockerfile-DB` and Redis to `redis/Dockerfile`; verify selected image tags before writing the workflow. No Compose or application container is required.
- [ ] Run `cd webclient && python manage.py check --settings=webclient.settings.github_ci` and representative existing fast tests (`core.tests.test_soubor_razeni`) and database tests (`api.tests.test_api_permissions`, `api.tests.test_record_lock_cache`, `cron.tests.test_run_data_import_validation`). Expect the standard runner to load, migrations to initialize a fresh database, Redis assertions to pass, and no external service access. Investigate failures rather than weakening assertions.
- [ ] Before committing, perform repository-required Python compilation and pre-commit checks in a way that does not retain unrelated generated changes. Stage only task changes and commit with `[chore] Isolate Django CI settings (#4183)`.

### Task 2: Inventory and execute explicit suites with useful reporting

**Interfaces:** `python .agents/scripts/run_django_ci.py --validate` validates coverage without selecting suites automatically. `python .agents/scripts/run_django_ci.py --suite fast|database --output-dir PATH` launches `manage.py test` with the corresponding explicit labels, CI settings, `--noinput`, and verbosity 2. It writes `test.log` and `summary.md` beneath PATH, appends the summary to `GITHUB_STEP_SUMMARY` when supplied, and returns the actual test process exit code.

- [ ] Inventory test modules across every Django app, including `tests.py`, `tests/test_*.py`, nested mapper modules, and `cron/tests/`. Read inherited base classes and explicit database/service access; do not assume every `core` test is database-free. Record exact module labels, not package-wide selections that may later include unwanted tests.
- [ ] Populate `django_ci_suites.json` with all current module labels. Put mixed modules wholly in `database`. Explicitly exclude Selenium and external integration modules with a reason; cover mocked Fedora tests normally. Keep repository script tests outside these lists.
- [ ] Implement the wrapper using the Python standard library. Validate missing module paths, duplicate and overlapping labels, empty runnable lists, and discovered test modules absent from all three lists. Discovery is a coverage check only; it never assigns tests to jobs. Run the child from `webclient` using the current interpreter.
- [ ] Stream merged stdout/stderr to the console and log. Summarize suite name, elapsed time, process outcome, test totals when available, and unittest `FAIL:`/`ERROR:` entries. For import, settings, or startup errors without a normal test result, show a bounded diagnostic log tail. Keep the full log as the artifact source. Handle launch errors with a nonzero return code and an explicit summary.
- [ ] Run inventory validation and both full suites. Confirm no unassigned modules, no database creation in the fast job, import package coverage, and integration exclusions. Exercise reporting with an invalid label and a temporary failing test fixture under `.agents/`; remove temporary probes before staging. Do not add new product test modules for this issue.
- [ ] Record exact commands, counts, durations, unresolved failures, and external dependencies in `.agents/reports/issue_4183_ci.md`. Perform required checks and commit only task files with `[chore] Add explicit Django CI suites and reporting (#4183)`.

### Task 3: Connect both suites to GitHub Actions and document operation

**Interfaces:** Both jobs call Task 2's wrapper and consume its outputs. Workflow-level summary steps also cover dependency-install and service/setup failures that precede the wrapper.

- [ ] Create `django-tests.yml` with `pull_request` branches `[main, test]` and `workflow_dispatch`. Use `permissions: contents: read`, checkout without persisted credentials, Python 3.12, dependency caching keyed by compiled requirements, and finite job timeouts. Use ordinary PR execution, never `pull_request_target`.
- [ ] Install compiled `webclient/requirements-test.txt` without refreshing pins. Install native GIS, PostgreSQL-client, gettext, and libmagic packages needed by the suite on the selected Ubuntu runner. Verify initialization first; do not copy the complete production image build blindly.
- [ ] Configure separate `fast` and `database` jobs with job-level `continue-on-error: true`, so failures remain visible in reporting without blocking PR progress. The jobs must not depend on each other's success. The fast job has no services; the database job has only the verified PostGIS and Redis images, mapped to localhost with readiness probes and disposable non-secret CI credentials.
- [ ] Run inventory validation and the corresponding wrapper command in each job. Use `if: always()` summary and artifact steps. If setup or tests did not produce a summary, publish the failed or skipped setup/test step outcomes explicitly. Retain logs for 14 days and include useful artifact names per suite. Do not add PR comments or modify branch protection.
- [ ] Extend `.agents/reports/issue_4183_ci.md` with local commands, `gh workflow run django-tests.yml --ref <branch>`, the container topology, explicit-list maintenance, exclusion policy, and promotion-to-required-check as a later maintainer decision.
- [ ] Validate YAML and Actions expressions with `actionlint` where available. Inspect triggers, absence of secret requirements, separate job independence, failure reporting, and unchanged `run-tests.yml`. Run inventory validation and full suites once after the final relevant change. If a hosted run is authorized and available, verify both jobs on GitHub and record duration and results; otherwise identify hosted execution as unverified.
- [ ] Run required compilation and pre-commit checks, inspect the scoped diff, and commit with `[chore] Run Django unit and import tests in Actions (#4183)`. Do not push or open a PR unless requested.

## Completion evidence

The report must distinguish observed results from static expectations: suite counts
and timing, fresh-database initialization, real Redis checks, excluded integrations,
failure-summary probes, lint results, and any hosted-run limitations. Existing
test failures remain visible and documented; green CI achieved by quietly dropping
tests is not completion.
