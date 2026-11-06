# Django test CI

`.github/workflows/django-tests.yml` runs two independent advisory jobs on PRs to
`main` or `test`, and supports manual dispatch. Python runs directly on the
runner. The fast job has no service containers; the database job uses PostGIS
and Redis. The existing Selenium workflow is separate.

## Test selection

`django_ci_suites.json` lists exact module names under `fast`, `database`, or
`excluded`. Add new test modules explicitly; validation rejects unassigned,
missing, duplicate, and overlapping entries. Put mixed modules and modules using
real Redis in `database`. Exclusions require reasons.

```bash
python scripts/ci/run_django_ci.py --validate
python -m unittest discover -s scripts/ci -p test_django_ci.py -v
```

## Running tests

Install `webclient/requirements-test.txt` and the native GIS dependencies first.
For local Python diagnostics:

```bash
python scripts/ci/run_django_ci.py --suite fast --output-dir /tmp/amcr-fast
python scripts/ci/run_django_ci.py --suite database --output-dir /tmp/amcr-database
```

The database suite requires disposable PostGIS and Redis on localhost ports
5432 and 6379. The database name and user default to `amcr_ci`, with the test-only
password `ci-only-password`. Override them with `AMCR_CI_DB_NAME`,
`AMCR_CI_DB_USER`, and `AMCR_CI_DB_PASSWORD`. The Python launcher also supports
`AMCR_CI_DB_PORT` and `AMCR_CI_REDIS_PORT`. Both Django database aliases use the
same test database through separate connections.

The Python launcher rejects external DNS and socket calls before importing the
application. CI also runs `with_ci_network.sh`, which restricts a dedicated
unprivileged user's IPv4/IPv6 traffic to the database/cache services. This covers
native clients and subprocesses as well. Caught network denials still fail the
suite. Dependency installation runs before network restrictions.

Use the firewall launcher only on disposable Linux runners with passwordless
sudo and iptables; it creates a dedicated user and permits the workflow's fixed
service ports. The `acl` package is required: `prepare_ci_access.sh` gives that
user read-only access to the checkout and traversal through private parent
directories. Only the results directory is writable; unrelated files remain
private. Local Python-only diagnostics do not provide the kernel firewall.

## Results

Each suite writes `test.log`, `network.log`, and `summary.md` to its output
directory. The workflow publishes summaries and keeps log artifacts for 14 days.
Setup failures receive fallback summaries; service initialization failures are
visible in GitHub's initialization log before job steps can run.

The checks are initially nonblocking. Existing database/import tests still have
unmocked external calls and missing/stale fixtures; these are reported as errors,
not silently omitted. Making the checks required is a separate maintainer
decision.
