# Issue #4183: CI execution record

Plan: `.agents/plans/2026-11-01-issue-4183-ci-implementation.md`.

## Decisions and progress

- Design and explicit module lists approved on 2026-11-01. Execute natively.
- User requires no external requests, including Digiarchiv. CI settings use
  inert external URLs, and tests must run with outbound access restricted to
  local PostGIS/Redis. Install dependencies before restricting test execution.
- Ruling: Keep execution records and helpers under `.agents/`, overriding the
  skill's `.superpowers/` scratch layout to follow repository governance.
- Ruling: Reuse the existing agent branch and preserve the user's checkout;
  no additional worktree is needed for these scoped changes.
- Pre-flight: settings supply the aliases consumed by the wrapper; explicit
  lists supply the labels consumed by both jobs; workflow must preserve the
  wrapper's exit status in summaries despite nonblocking job conclusions.
- Baseline: cached application image, network disabled, could not load the old
  CI settings because inherited `dev.py` tries hostname resolution. The missing
  runner remains a separate defect established by source inspection.
- Local host has no Django/GIS installation. Use disposable containers with
  mounted source for verification only; the proposed Actions jobs still run
  Python directly on the runner with two service containers.
- Ruling: Add standard-library regression checks for the new CI helpers,
  because omitted coverage or broken network enforcement could silently pass.
  No new Django application tests were added.
- Ruling: Move `core.tests.test_import_data_template` to the service-backed job:
  despite using SimpleTestCase, template rendering uses the real Redis cache.
- Ruling: Repair the existing password-signal test's stale on-commit mock so it
  executes the callback without opening a database; observed failure became a
  passing existing test without changing production signal behavior.
- Network implementation: Python audit hooks fail before external DNS/connect;
  a RuntimeError avoids HTTP retry delays while preserving unittest cleanup.
  A dedicated unprivileged Linux user has IPv4/IPv6 OUTPUT rules allowing only
  PostGIS/Redis destinations. Native clients and subprocesses are also blocked.
  Rules are smoke-tested before Django imports and removed afterward. The Actions
  agent and dependency-install steps retain their network access.

## Operation

No Compose file is used. The fast job has no services; the database job has
PostGIS and Redis. The application is a Python test process on the runner.
`default` and `urgent` use one test database over separate Django connections.

CI installs `webclient/requirements-test.txt` and native GIS dependencies, then:

```bash
python .agents/scripts/run_django_ci.py --validate
python -m unittest discover -s .agents/scripts -p test_django_ci.py -v
bash .agents/scripts/with_ci_network.sh fast "$RUNNER_TEMP/django-fast" "$(command -v python)"
# The database job also supplies exact service IPs obtained from docker inspect.
bash .agents/scripts/with_ci_network.sh database "$RUNNER_TEMP/django-database" "$(command -v python)"
```

The firewall launcher is only for disposable Linux CI runners with passwordless
sudo and iptables. It creates a dedicated user; do not run it on a shared host.
For local Python diagnostics, the following still blocks Python socket calls,
but does not apply the kernel firewall to native clients or subprocesses:

```bash
python .agents/scripts/run_django_ci.py --suite fast --output-dir /tmp/amcr-fast
python .agents/scripts/run_django_ci.py --suite database --output-dir /tmp/amcr-database
```

Database runs require disposable local PostGIS/Redis on ports 5432/6379. Database
defaults are `amcr_ci`, user `amcr_ci`, password `ci-only-password`; override these
with `AMCR_CI_DB_NAME`, `AMCR_CI_DB_USER`, and `AMCR_CI_DB_PASSWORD`. The Python-only
launcher also supports `AMCR_CI_DB_PORT` and `AMCR_CI_REDIS_PORT`. The CI firewall
deliberately permits only the workflow's fixed ports 5432/6379.

After publication, manually dispatch with:

```bash
gh workflow run django-tests.yml --ref agents/codex/4183-unit-test-ci
```

The manifest lists exact modules under `fast`, `database`, or `excluded`. Add new
modules explicitly; inventory validation rejects unassigned, missing, duplicate,
and overlapping entries. Mixed modules and modules using real Redis belong in
`database`. Exclusions need reasons and are limited to Selenium, external
integration, and empty placeholders. The firewall converts even caught network
attempts into suite failure. Mocked HTTP calls do not make real requests.

Both jobs are advisory (`continue-on-error: true`), and neither depends on the
other. Summaries retain actual test outcomes and failure names; artifacts retain
full logs for 14 days. Install/inventory failures receive fallback summaries.
Service-container startup errors happen before job steps and remain visible in
GitHub's initialization log; no in-job summary can run if initialization fails.
Promotion to required checks remains a separate maintainer decision.

## Verification so far

- Inventory: 40 fast modules, 107 database/service modules, 16 excluded modules.
- Seven helper regression checks pass, including denied DNS, denied non-service
  sockets, swallowed denial detection, failure exit-code preservation, readable
  summaries, and new-module inventory rejection.
- Fast suite: 507 tests passed in 2.2 seconds (about 4 seconds including startup)
  in the cached Python 3.14.4 / Django 6.0.8 Linux image. A second run through the
  real iptables launcher also passed all 507 tests, including its firewall probe.
- Final database run through the kernel firewall: 2,076 tests discovered;
  1,291 executed in 48.8 seconds (58.5 seconds including startup), with 432 errors,
  including class-setup errors that prevent methods from running.
  399 errors are unmocked Fedora access blocked before DNS; one is unmocked
  Crossref access. Other failures expose missing UserNotificationType fixtures,
  unavailable dynamic identifier values, and a stale `core.admin.pofile` mock.
  Four template errors from production static paths were fixed by disabling
  CI precompilation and using temporary media/static paths. The four targeted
  tests and their final service-backed run passed. No failing module is omitted.
- Real Redis record-lock tests observed passing, including cross-process
  contention, under the isolated service-backed environment.
- Source is read-only during local verification. The ignored local
  `webclient/.baseline_test` copy is masked, matching a clean GitHub checkout and
  avoiding false failures in the existing source-scanning logging test.
- Hosted Python 3.12 execution has not been run. The cached Linux image provides
  useful application evidence but does not establish the hosted workflow result.
- Python 3.12 compilation of the application and new helpers passed.
- All pre-commit hooks passed over the full file set in a disposable checkout,
  including the new helpers. The existing tracked-file checks also passed in
  the working checkout without introducing unrelated changes.
- `actionlint` passed for the new workflow. Both service image tags were verified
  against registry manifests; local database verification used the cached
  PostGIS 16/3.4 image with its bundled initialization/restore scripts masked.
- Final independent review found one inventory gap: conventional `test*.py`
  modules directly under an app package were missed. A regression demonstrated
  the failure for both `test_new.py` and `tests_extra.py`; discovery now matches
  Django's filename pattern and all seven helper checks pass. No deferred minor
  findings were reported.

## Remaining work and scope limits

The CI implementation is reviewable, but the database suite is not green. Repair
unmocked external calls and missing/stale fixtures before making it required.
This implementation deliberately does not turn failing tests into skips, supply
fake successful HTTP responses globally, or change production application logic.
No hosted workflow was dispatched and no branch was pushed.

The implementation steps are delivered together with this evidence; their
expected all-green database outcome is not claimed. The plan's task completion
contract cannot be marked fully green while these baseline failures remain.

Ruling costs: retaining `.agents/` artifacts and the current branch only changes
artifact placement/isolation, not application behavior; helper checks add a small
maintenance cost; service-backed template placement adds no services to the fast
job; the signal-test callback mock verifies immediate callback behavior but does
not claim to test database commit ordering. Broad fixture repair is deferred
because changing hundreds of setup behaviors would exceed this CI task's scope.

References consulted: GitHub's service-container documentation
(https://docs.github.com/en/actions/tutorials/use-containerized-services/use-docker-service-containers)
and Django's test database alias documentation
(https://docs.djangoproject.com/en/6.0/topics/testing/advanced/).
