# Issue #4183: Django test CI design

Status: approved by the user on 2026-11-01 after clarification of the database
aliases and container topology.

## Intent and scope

Run all current non-Selenium Django unit and database tests, including import
tests, on GitHub-hosted runners. Run on pull requests targeting `main` or `test`
and through manual dispatch. Initial checks must be nonblocking and require no
VPN, deployed DEV server, or credentials for external application services.
External integration tests are excluded even when they are not Selenium tests.

## Approaches

1. Discover tests and automatically split them by database requirements. New tests
   join automatically, but this requires custom suite-selection logic.
2. Maintain explicit module lists for database-free and database-backed jobs.
   This is easier to inspect, but contributors must maintain the lists. A module
   containing both kinds belongs wholly to the database-backed job.

The user selected approach 2, superseding their earlier selection of approach 1.

## Proposed implementation

- Add a separate workflow with two independent jobs. Use explicit module labels
  in one versioned location; include the current import test packages. Inventory
  the full suite before finalizing those labels, rather than copying the outdated
  inventory in the issue.
- The fast job runs modules requiring no database or live application services.
  The database job supplies disposable PostGIS and Redis services. Redis remains
  real because record-lock tests explicitly assert Redis backend behavior.
  Django runs directly on the GitHub runner; there is no application container
  and no Docker Compose file is used by the new workflow.
- Use Python 3.12 and the repository's compiled test requirements. Install the
  native GIS libraries required by the existing PostGIS backend. These are
  proposed implementation defaults based on the current repository setup.
- Repair `github_ci.py` by explicitly selecting Django's standard DiscoverRunner;
  merely deleting its runner setting would inherit the Selenium runner from
  `dev.py`. Retain `SKIP_SELENIUM_TESTS = True`, disable external integration
  tests, and isolate logging, cache connections, and email from DEV services.
  User clarification: no external requests may occur, including Digiarchiv.
  Disable its update URL and use inert external endpoints; restrict the Linux
  test user's network traffic as well as Python socket calls before Django
  imports. Only local PostGIS/Redis connections are permitted during tests.
- Configure both database aliases (`default` and `urgent`) for the disposable
  test environment and verify their required test-database relationship. Do not
  assume that PostGIS startup alone makes the database suite runnable.
- Publish per-job outcomes and readable failure details in the Actions summary,
  retaining complete logs as artifacts. Preserve actual test exit outcomes in
  reporting while allowing the initial checks to remain nonblocking.
- Document local equivalents, manual execution, excluded integration tests, and
  how to update the module lists when adding tests.

## Constraints and non-goals

Keep the existing `run-tests.yml` and Selenium execution unchanged. Do not make
the new checks required, change production behavior, or add unrelated tests or
repository script tests. Keep AI design and planning artifacts under `.agents/`
as required by repository governance. Changes originate from `test` and require
human review before merge.

## Validation and remaining decisions

Verify settings and runner loading, then execute each explicit suite in its
intended environment. Confirm that the fast suite opens no database and that
Selenium and external integration tests cannot execute. Validate workflow
triggers, nonblocking failure behavior, summaries for failures and setup errors,
and artifact retention. Measure both job durations.

The implementer will choose exact workflow and module-list filenames, reporting
mechanism, service health checks, compatible image pins, and timeouts. Existing
test failures or dependencies on preloaded reference data must be reported;
silently skipping failing tests does not satisfy coverage of the current suite.
No runtime verification has been performed during brainstorming.
