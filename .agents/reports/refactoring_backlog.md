# Refactoring backlog — AMČR (aiscr-webamcr)

> Review prose follows the canonical English-default rule; verbatim Czech is preserved where field names or AIS CR domain identifiers matter.
> Structural improvements discovered during the audit.
>
> **Note on priority vs. severity:** The priority sections (High / Medium / Low)
> reflect the **refactoring priority** (impact on architecture and business logic).
> This classification may differ from the **bug severity** in `bugs.md`, which reflects
> the technical risk of the defect itself. When an item cross-references BUG-XXX,
> both values are intentional — refactoring priority and bug severity use a different
> evaluation frame.

---

## High Priority

<!-- Architectural problems, security debt, ORM performance -->

### [T02] CIRC-01: Circular dependency projekt ↔ oznameni
- **Files:** `webclient/oznameni/models.py`, `webclient/projekt/forms.py`, `webclient/projekt/views.py`, `webclient/projekt/urls.py`
- **Description:** Mutual imports at the module level between projekt and oznameni. An unstable architecture that may cause an ImportError on further extension.
- **Recommendation:** Merge oznameni into projekt or extract the shared logic into core.
- **Effort:** L

### [T02] ARCH-01: The overgrown `core` application
- **Files:** `webclient/core/` (77 .py files, 26 migrations)
- **Description:** Core is imported by 16+ applications. It contains middleware, permissions, constants, signals, logging — too many responsibilities. Global impact of changes.
- **Recommendation:** Decompose into core.permissions, core.logging, core.middleware, core.signals.
- **Effort:** XL

### [T02] ARCH-02: The `dokument` application — excessive fan-out
- **Files:** `webclient/dokument/`
- **Description:** Imports 8 other applications — the highest fan-out in the repository. A potential violation of the single-responsibility principle.
- **Recommendation:** Audit the dependencies, consider signals or a services layer.
- **Effort:** M

### [T03] ORM-01: Extra SELECT in the save() methods of ArcheologickyZaznam and SamostatnyNalez
- **Files:** `webclient/arch_z/models.py:531`, `webclient/pas/models.py:182`
- **Description:** On every `save()` call (where `pk != None`), an extra `SELECT get(pk=self.pk)` is done to detect a change of `pristupnost`. The correct solution is to store the initial value in `__init__()`, as with `initial_stav`.
- **Recommendation:** Add `self._initial_pristupnost = self.pristupnost` in `__init__()`, and in `save()` compare with `self._initial_pristupnost`.
- **Effort:** S

### [T03] ORM-02: N+1 in the check_pred_* methods
- **Files:** `webclient/projekt/models.py`, `webclient/arch_z/models.py`
- **Description:** The methods `check_pred_uzavrenim()` and `check_pred_odeslanim()` make N+1 queries when iterating over akce and documentation units. See BUG-002.
- **Recommendation:** prefetch_related before calling the check methods, or accept prefetched data as a parameter.
- **Effort:** M

### [T03] ORM-03: Missing indexes on pas.SamostatnyNalez
- **Files:** `webclient/pas/models.py`
- **Description:** The FK fields `projekt`, `katastr`, `pristupnost`, `stav` have no `db_index=True`. For a table with thousands of records, indexes are key.
- **Recommendation:** Add `db_index=True` or indexes via a migration.
- **Effort:** S

## Medium Priority

<!-- Optimizations, module decomposition, Docker build -->

### [T02] CIRC-02: Circular dependency adb ↔ xml_generator
- **Files:** `webclient/adb/models.py`, `webclient/xml_generator/generator.py`
- **Description:** adb.models imports BaseAmcrModel from xml_generator.models; xml_generator.generator imports VyskovyBod from adb.models at the module level.
- **Recommendation:** Move BaseAmcrModel/ModelWithMetadata into core or an amcr_base module.
- **Effort:** M

### [T02] ARCH-03: Duality of responsibilities in xml_generator
- **Files:** `webclient/xml_generator/`
- **Description:** xml_generator serves both as a base-model library (BaseAmcrModel) and as an XML generator. Imported by 10 applications.
- **Recommendation:** Split into amcr_base (base models) and xml_generator (purely an XML generator).
- **Effort:** M

### [T06] CELERY-01: Harden the error handling of long Celery tasks
- **Files:** `webclient/cron/tasks.py`
- **Description:** The tasks `update_all_redis_snapshots`, `update_single_redis_snapshot`, and `update_materialized_views` have no central exception handling. An error in the middle of a batch (e.g. a Redis/DB outage or a problem in REFRESH MATERIALIZED VIEW) terminates the whole task without a summary and without a clear log of partial success.
- **Recommendation:** Wrap the main loops/calls in `try/except` blocks with a summary log (count of processed items, the current class/model, the name of the materialized view) and consistent behavior on failure.
- **Effort:** S

### [T06] CELERY-02: Timeout and error handling for the external HTTP call
- **Files:** `webclient/cron/tasks.py`
- **Description:** The task `call_digiarchiv_update_task` calls `requests.get(settings.DIGIARCHIV_URL)` without an explicit `timeout` and without `try/except`. On an outage or a slow service response, the worker may wait disproportionately long and the logs contain no clear information about the cause.
- **Recommendation:** Add a reasonable `timeout` and wrap the call in a `try/except` with error logging; optionally set a retry strategy via Celery (e.g. countdown/max_retries).
- **Effort:** S

### [T06] CELERY-03: Limit the polling pattern in check_hlidaci_pes
- **Files:** `webclient/notifikace_projekty/tasks.py`
- **Description:** The task `check_hlidaci_pes` waits in a while loop (`time.sleep(0.5)`) for the creation of a project in the DB, without an upper time limit. On a misconfiguration or a transaction rollback, it may run longer than desired and block the worker.
- **Recommendation:** Prefer scheduling the task via `transaction.on_commit()` (running only after the transaction is committed) or add a maximum iteration count / time budget with safe termination and a log once it is exceeded.
- **Effort:** M

### [T02] REQ-01: Mixed production and development dependencies in requirements.txt
- **Files:** `webclient/requirements.txt`
- **Description:** Selenium, debug-toolbar, pre-commit, coverage, sphinx, etc. are in the production requirements.txt. The production image is unnecessarily large.
- **Recommendation:** Split into requirements.txt, requirements-dev.txt, requirements-test.txt.
- **Effort:** S

### [T08] DOCS-01: Separate requirements for the documentation build
- **Files:** `readthedocs.yaml`, `webclient/requirements.txt`
- **Description:** The Read the Docs build installs the complete `webclient/requirements.txt`, which also contains development and testing packages (Selenium, debug-toolbar, Sphinx, etc.). For a documentation build this is unnecessary and increases both time and the risk of dependency conflicts.
- **Recommendation:** Create a separate file (e.g. `docs/requirements.txt`) with the minimal set of packages for the documentation and switch the installation in `.readthedocs.yaml` to that file.
- **Effort:** S

### [T08] DOCS-02: Improve error handling in the license generator
- **Files:** `docs/licenses/convert_to_rst.py`
- **Description:** The script runs `pip-licenses` via `subprocess.run` and, without checking the return code, directly parses the JSON output. On a tool error or invalid output it ends with a traceback without an understandable message.
- **Recommendation:** Check `returncode` and wrap `json.loads` in a `try/except` with a clear error message (e.g. missing `pip-licenses`), optionally returning a non-zero exit code for a clear failure in CI.
- **Effort:** S

### [T10] SCRIPTS-01: Unify the fail-fast behavior and wrappers in the deploy scripts
- **Files:** `scripts/prod_deploy.sh`, `scripts/dev_deploy.sh`, `scripts/test_deploy.sh`, `scripts/git_prod_deploy.sh`
- **Description:** The deploy scripts use their own `er()` wrapper for logging and error propagation, but do not globally use `set -e`/`set -u`. Errors in commands outside `er()` may manifest only indirectly (e.g. in subsequent steps or only in the log).
- **Recommendation:** Add `set -e` (possibly `set -u`) and review which commands should be wrapped in `er()` and which may fail "softly". Also unify the structure of the helper functions across the scripts so they are easily maintainable.
- **Effort:** S

### [T08] DOCS-03: Enforce docstring completeness for Selenium tests
- **Files:** `docs/generate_selenium_test_docs.py`
- **Description:** The Selenium documentation generator assumes that all tests have a docstring and the required `Steps` and `Expected` sections. A missing section leads to incomplete documentation without a clear warning.
- **Recommendation:** Add a check and a summary report of missing sections/docstrings and, when running in CI (e.g. in a pre-commit hook), the option to fail the build if the minimal documentation rules are not met.
- **Effort:** M

### [T09] CI-01: Add Dependabot and a lightweight CodeQL workflow
- **Files:** `.github/` (new workflow and configuration)
- **Description:** The current pipeline uses Docker Scout and Trivy for scanning the Docker image, but has no separate check of Python dependencies (Dependabot) or static code analysis (CodeQL). The risk that vulnerable libraries in the code pass without warning is higher.
- **Recommendation:** Add `.github/dependabot.yml` for Python and GitHub Actions and a simple CodeQL workflow for Python (e.g. running on push/PR to the `dev` branch) to complement the image-level scanning.
- **Effort:** S

### [T10] SCRIPTS-01: Add set -e to the deploy and maintenance scripts
- **Files:** `scripts/prod_deploy.sh`, `scripts/dev_deploy.sh`, `scripts/test_deploy.sh`, `scripts/git_prod_deploy.sh`, `scripts/restore_database.sh`, `scripts/build_prod_image.sh`, `scripts/ci_deployment/deploy_server.sh`, `scripts/ci_deployment/deploy_test_server.sh`
- **Description:** Most scripts have no `set -e`; a command failure outside the `er()` wrapper may be overlooked. `restore_database.sh` performs a DROP/CREATE of the database without stopping on an error.
- **Recommendation:** Add `set -e` (and optionally `set -o pipefail`) at the start of each script; for interactive blocks consider disabling it temporarily. In `restore_database.sh`, additionally verify the required environment variables before running.
- **Effort:** S

### [T10] SCRIPTS-02: Extract the common functions of the deploy scripts into scripts/common.sh
- **Files:** `scripts/prod_deploy.sh`, `scripts/dev_deploy.sh`, `scripts/test_deploy.sh`, `scripts/git_prod_deploy.sh`
- **Description:** The functions `ask_continue`, `echo_dec`, `er()`, `check_create_network`, `check_stack_exists`, `check_file_exist` are repeated in the four scripts; maintenance and consistency are hindered.
- **Recommendation:** Create `scripts/common.sh` with the shared functions and load it in the deploy scripts via `source "$(dirname "$0")/common.sh"` (or a relative path from the repository root).
- **Effort:** M

### [T10] SCRIPTS-03: Fix db_connection_from_docker-web.py — use DB_PORT from the secret
- **Files:** `scripts/db/db_connection_from_docker-web.py`
- **Description:** The script reads `DB_NAME`, `DB_PASS`, `DB_USER`, `DB_HOST` from the JSON secret, but not `DB_PORT`; the DB connection therefore always uses the default port 5432. With a non-standard port the health check is incorrect.
- **Recommendation:** Add reading of `DB_PORT` (with a default of 5432) and pass `port=...` to `psycopg2.connect()`. See BUG-014.
- **Effort:** S

## Low Priority

<!-- Cosmetic changes, documentation, minor code quality -->

### [T03] ORM-04: Replace eval() with int() in the identifier generators
- **Files:** `webclient/projekt/models.py:663`, `webclient/arch_z/models.py:331`, `webclient/arch_z/models.py:889`
- **Description:** Three occurrences of `eval(i)` to convert a number from a string. See BUG-001.
- **Recommendation:** Replace with `int(i)`, add validation `i.isdigit()`.
- **Effort:** S

### [T03] ORM-05: Fix the cached_property import in uzivatel/models.py
- **Files:** `webclient/uzivatel/models.py:28`
- **Description:** Import from `distlib.util` instead of `functools`. See BUG-003.
- **Recommendation:** `from functools import cached_property`
- **Effort:** S

### [T03] ORM-06: Replace .extra() in arch_z/filters.py with RawSQL
- **Files:** `webclient/arch_z/filters.py:773-775`
- **Description:** `.extra(where=["ST_Z(geom) >= %s"])` has been deprecated since Django 4.0.
- **Recommendation:** Use `RawSQL` or a PostGIS function.
- **Effort:** S

### [T03] ORM-07: Squash migrations for applications with 20+ migrations
- **Applications:** uzivatel (31), core (26), arch_z (20), dokument (19)
- **Description:** 152 migrations in total — the applications with the most migrations are candidates for `squashmigrations`.
- **Recommendation:** Gradual squash after the schema stabilizes, starting with less critical applications.
- **Effort:** M

### [T02/T04] DOCKER-DEP-01: logstash without depends_on elasticsearch
- **Files:** `docker-compose.yml`
- **Description:** The logstash service has no depends_on: elasticsearch — a potential race condition on concurrent startup.
- **Recommendation:** Add depends_on: [elasticsearch] to the logstash service.
- **Effort:** S

### [T04] DOCKER-01: Fix the secret injection for Grafana, Elasticsearch, Logstash
- **Files:** `docker-compose.yml:149,180-181,201`, `docker-compose-test.yml:169`, `git_docker-compose.yml:144`
- **Description:** `GF_SECURITY_ADMIN_PASSWORD`, `ELASTIC_PASSWORD`, `LOGSTASH_INTERNAL_PASSWORD` are set to file paths or secret names, not to their values. The Grafana admin password is effectively non-functional.
- **Recommendation:** Grafana: use `GF_SECURITY_ADMIN_PASSWORD__FILE`. Elasticsearch/Logstash: an entrypoint wrapper script that reads the secret from the file.
- **Effort:** S
- **Severity:** Medium

### [T04] DOCKER-02: Celery worker logs DEBUG in production
- **Files:** `docker-compose.yml:81`
- **Description:** `celery -A webclient worker -l DEBUG` — excessive logging, potential exposure of sensitive data in production.
- **Recommendation:** Change to `-l INFO`.
- **Effort:** S
- **Severity:** Medium

### [T04] DOCKER-03: ELK Stack major version gap (prod 9.x vs dev 8.x)
- **Files:** `docker-compose.yml`, `docker-compose-dev-local-db*.yml`
- **Description:** Production, test, and git-deploy use ELK 9.3.1; the dev compose files use 8.19.0. The major version gap causes different behavior of xpack.security and the API.
- **Recommendation:** Synchronize to the same major version (dev = prod recommended).
- **Effort:** S
- **Severity:** Medium

### [T04] DOCKER-04: sudo access in the production container
- **Files:** `Dockerfile:99`
- **Description:** `usermod -aG sudo user` — the production application user is a member of the sudo group.
- **Recommendation:** Remove the sudo group, use specific NOPASSWD rules for necessary operations.
- **Effort:** S
- **Severity:** Medium

### [T04] DOCKER-05: Selenium in the production docker-compose.yml
- **Files:** `docker-compose.yml`
- **Description:** The Selenium service belongs exclusively in the testing environment.
- **Recommendation:** Remove it from docker-compose.yml, keep it only in docker-compose-test.yml.
- **Effort:** S
- **Severity:** Low

### [T04] DOCKER-06: Fedora Dockerfile — multiple apt-get update, no PID 1
- **Files:** `fedora/Dockerfile`
- **Description:** Three separate RUN apt-get update commands without apt-get clean enlarge the image. CMD runs two processes without a process supervisor.
- **Recommendation:** Merge the RUN blocks, add tini or an entrypoint script.
- **Effort:** S
- **Severity:** Low

### [T02] REQ-02: sphinxcontrib-mermaid without a version specification
- **Files:** `webclient/requirements.txt`
- **Description:** The sphinxcontrib-mermaid package has no fixed version — non-deterministic builds.
- **Recommendation:** Add a specific version.
- **Effort:** S

### [T01] ARCH-04: cron and notifikace_projekty without tests
- **Files:** `webclient/cron/`, `webclient/notifikace_projekty/`
- **Description:** Both applications have no tests, even though cron imports 6 other applications.
- **Recommendation:** Add unit tests for the Celery tasks.
- **Effort:** M

### [T05] SEC-01: Fix the DEBUG fallback in production.py
- **Files:** `webclient/webclient/settings/production.py:3`
- **Description:** `get_secret("DEBUG", "True")` — the fallback is "True" → DEBUG=True with a missing key. See BUG-010.
- **Recommendation:** Change the fallback to "False".
- **Effort:** S
- **Severity:** High

### [T05] SEC-02: Rotate the Mailtrap credentials and replace with placeholders
- **Files:** `webclient/webclient/settings/sample_secrets_mail_client.json`
- **Description:** Seemingly real Mailtrap sandbox credentials in a commit. See BUG-011.
- **Recommendation:** Verify, rotate, replace with obvious placeholders.
- **Effort:** S
- **Severity:** Medium

### [T05] SEC-03: Add Django security headers to production.py
- **Files:** `webclient/webclient/settings/production.py`
- **Description:** Missing `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_CONTENT_TYPE_NOSNIFF`. The Django security check (`manage.py check --deploy`) will report failures.
- **Recommendation:** Add to production.py and add `manage.py check --deploy` to the CI pipeline.
- **Effort:** S
- **Severity:** Medium

### [T05] SEC-XSS: Audit mark_safe() in the vypis/ application
- **Files:** `webclient/vypis/fields.py:363,438`, `webclient/vypis/views.py:79`
- **Description:** Three places apply `mark_safe()` to values from the DB or model properties. See BUG-012.
- **Recommendation:** Rewrite using `format_html()` or ensure `escape()` before mark_safe.
- **Effort:** M
- **Severity:** Medium

### [T05] SEC-04: Add CVE scanning to the CI pipeline
- **Files:** `.github/workflows/` (a new step)
- **Description:** There is no automatic CVE check in the Python dependencies.
- **Recommendation:** Add `pip audit` or `safety check` as a CI step.
- **Effort:** S
- **Severity:** Medium

### [T07] FRONT-01: Extract the larger inline scripts from base.html
- **Files:** `webclient/templates/base.html`
- **Description:** The `base.html` template contains several larger inline scripts (datepicker initialization, automatic hiding of flash messages, periodic authentication check, the language switcher). The logic is correct, but harder to reuse and less readable in inline form.
- **Recommendation:** Move these blocks into separate JS files in `static/js/` (e.g. `datepicker-init.js`, `messages.js`, `auth_check.js`, `language_switcher.js`) and load them in the template via `{% static %}`.
- **Effort:** S

### [T07] FRONT-02: Consider a bundler/minification for the custom JS
- **Files:** `webclient/static/js/`
- **Description:** The custom JavaScript (map scripts, helpers, theme-toggle) is served as multiple separate files without a bundler and minification. In production this increases the number of HTTP requests and the size of the assets.
- **Recommendation:** Consider deploying a lightweight bundler (e.g. Webpack/Vite/rollup) or at least a minification step within the existing `django-compressor` setup for the custom JS.
- **Effort:** M

### [T07b] FRONT-03: Add XHR onerror handlers in all map scripts
- **Files:** `webclient/static/js/mapa_arch_z.js`, `mapa_pas.js`, `mapa_projekty.js`, `mapa_doc.js`, `mapa_oznameni.js`
- **Description:** None of the map scripts implements an `xhr.onerror` handler — a network failure is silent. The user gets no feedback on a backend outage.
- **Recommendation:** Add consistent error handling (onerror + onreadystatechange with a status check) with a user message. Consider a central helper function for XHR calls.
- **Effort:** S
- **Severity:** Medium

### [T07b] FRONT-04: Wrap JSON.parse in try/catch in the map and modal scripts
- **Files:** `webclient/static/js/mapa_arch_z.js`, `mapa_pas.js`, `mapa_projekty.js`, `mapa_doc.js`, `mapa_oznameni.js`, `modal_forms_class.js`
- **Description:** JSON.parse(this.responseText) is called without try/catch — invalid JSON (e.g. a 500 HTML page) causes an uncontrolled failure.
- **Recommendation:** Wrap in try/catch and log/display the error.
- **Effort:** S
- **Severity:** Medium

### [T07b] FRONT-05: Refactor mapa_pins.js — a factory function instead of duplication
- **Files:** `webclient/static/js/mapa_pins.js`
- **Description:** 235 lines define 4 color variants of icons with extensive duplication (copy-paste with a single color change).
- **Recommendation:** Replace with a factory function `createPinIcon(color)` and reduce to ~50 lines.
- **Effort:** S
- **Severity:** Low

### [T07b] FRONT-06: Eliminate the implicit global variables in the map scripts
- **Files:** `webclient/static/js/mapa_arch_z.js`, `mapa_pas.js`
- **Description:** Variables like `rs`, `geom`, `zoomed`, `coor`, `akce_ident_cely` are not declared with let/const/var — they become implicit globals.
- **Recommendation:** Add `let`/`const` declarations and consider the ESLint `no-undef` rule.
- **Effort:** S
- **Severity:** Medium
