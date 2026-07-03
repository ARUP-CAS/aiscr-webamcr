# Workflow-evolution legacy evidence

Created: 2026-07-03
Expanded: 2026-07-04 after reviewer feedback.

This report preserves and classifies the retired `.agents/prompts/prompt_evolution/`
channel. The original files were sibling-local evidence for improving the
codebase-review workflow before the hub-canonical `aiscr-codebase-review`
workflow owned the active feedback path.

## Classification

All source files matched the legacy `<task_id>_prompt_update.md` convention and
were retained as evidence here before removing the retired prompt-evolution
directory. No hub backlog handoff was approved for these notes in this session.
Future U05 review runs may use this report as evidence, but new workflow changes
still require an explicit human-approved report-to-backlog handoff.

## Evidence Inventory

The notes below preserve implementation-relevant facts from the retired source
files. They are intentionally more detailed than a status summary so the deleted
legacy files are not needed for future implementation work.

### T01 Repository Map

Source: `T01_prompt_update.md`
Disposition: retained implementation evidence.

- Treat `webclient/` as the Django project root, not the repository root.
  `manage.py` and `requirements.txt` live under `webclient/`.
- Verify whether `pyproject.toml`, `package.json`, and `locale` actually exist
  before requiring them in review setup; they were not found at the expected
  repository-root locations during the legacy run.
- Add or preserve an explicit Django app mapping. The original prompt named
  domain entities but did not map them to app directories.
- Flag `core` as a large app and likely split target for ORM analysis; the
  legacy run recorded it as the largest app.
- Keep these files in later task scope:
  `webclient/webclient/settings/base.py`, `webclient/webclient/celery.py`,
  `webclient/cron/tasks.py`, and
  `webclient/notifikace_projekty/tasks.py`.

### T02 Dependency Graph

Source: `T02_prompt_update.md`
Disposition: retained implementation evidence.

- If `package.json` is absent, record it as N/A and move CDN/frontend dependency
  review to T07 instead of spending review time searching for it.
- Define cross-app import scope explicitly. Prefer production-code imports by
  default; include tests only when the review asks for a test-specific graph.
- Distinguish module-level imports from lazy imports inside functions. Lazy
  imports reduce but do not remove circular-dependency risk.
- Define fan-in/fan-out thresholds, for example fan-in greater than 10 as a
  decomposition candidate.
- Use `INSTALLED_APPS` from `webclient/webclient/settings/base.py` as the
  authoritative Django app list.
- Add `webclient/services/` to important directories because it contains shared
  service functions imported by multiple apps.
- Add `webclient/xml_generator/` to T02 scope because it works as a cross-cutting
  base-model library.

### T03 ORM Analysis

Source: `T03_prompt_update.md`
Disposition: retained implementation evidence.

- Check whether models cache initial foreign-key values in `__init__()` so
  `save()` does not need an extra SELECT to compare old and new FK values.
- Audit unexpected model imports. The legacy note specifically called out
  `cached_property` imported from `distlib.util`; imports in models should come
  from Django, the Python standard library, or declared dependencies.
- Search for `len(queryset.all())` and similar patterns that should use
  `.count()`.
- Check deprecated or risky ORM APIs, including `.extra()`,
  `select_related` without explicit fields, and unparameterized `raw()`.
- Split views ORM analysis when needed. The legacy run called out
  `arch_z/views.py`, `dokument/views.py`, and `projekt/views.py` as very large
  files that should be handled as a separate T03b scope.
- Use the app table in `AGENTS.md` for planning; the legacy note found it useful
  for splitting ORM work.
- Treat the `urgent` database/router as an architectural special case used by
  sequence models such as `ProjektSekvence`, `AkceSekvence`, and `PianSekvence`.
- Include `webclient/*/signals.py`, `webclient/*/managers.py`,
  `webclient/history/models.py`, and `webclient/komponenta/models.py` in ORM
  scope where relevant.

### T04 Docker Build Analysis

Source: `T04_prompt_update.md`
Disposition: retained implementation evidence.

- For every service that reads Docker secrets, verify the injection pattern:
  Grafana `__FILE` suffix, PostgreSQL `POSTGRES_PASSWORD_FILE`, Redis entrypoint
  substitution, and Elasticsearch/Logstash entrypoint wrappers.
- Compare shared dev/prod image versions for ELK, Prometheus, Grafana, Selenium,
  and other shared services. Major version gaps should be documented as at least
  medium severity.
- Check whether each compose service belongs to its environment. Test tooling
  such as Selenium should not be present in production compose files; dev-only
  services should not leak into production assumptions.
- Check PID 1 and signal handling for multi-process containers; they should use
  a supervisor such as `tini` or `s6-overlay`, or a correct `exec` entrypoint
  pattern.
- Check exposure of monitoring and admin interfaces including Grafana,
  Prometheus, Kibana, and Elasticsearch.
- Link T04 findings into T05 security review to avoid duplicate or disconnected
  reporting.
- Remember that `redis_image` and `amcr_image` may be supplied through `.env` or
  deployment scripts; without that context, production image analysis is
  incomplete.
- Add `redis/docker-entrypoint.sh`, `scripts/entrypoint.sh`,
  `scripts/entrypoint.dev.sh`, and
  `prometheus/collectors/pg_stat_statements.yaml` to relevant scope.

### T05 Security Analysis

Source: `T05_prompt_update.md`
Disposition: retained implementation evidence.

- Start Django security review with `python manage.py check --deploy` and record
  warnings for DEBUG, SECRET_KEY, ALLOWED_HOSTS, HTTPS settings, and cookie
  security.
- For CVE scanning, prefer `pip audit` or `safety check` in CI. If unavailable,
  record CVE audit as recommended and add a security follow-up instead of
  pretending the check was completed.
- Classify `mark_safe()` by data provenance:
  hardcoded HTML widgets are lower risk, model/DB values without escaping are
  medium risk, direct request/user input is high risk, and `format_html()` is
  preferred for dynamic content.
- Distinguish placeholder secrets from potentially real credentials. Placeholder
  markers include `changeme`, `test_key`, `PLACEHOLDER`, `your_key_here`, and
  `secret`; random-looking hex/base64 strings, email addresses, or third-party
  URLs deserve closer review and possible rotation advice.
- Audit custom authentication backend behavior. `user_can_authenticate()` should
  return `False` for inactive users, not raise an exception.
- Use GitHub CLI issue lookup when available to cross-reference existing issues.
- Include NGINX/proxy context because HTTPS headers may be set outside Django
  settings; `proxy/default.conf` is critical for HSTS, SSL redirects, and
  security headers.
- Keep Django version context in mind; the legacy note cited Django 5.2-specific
  security defaults.
- Add `webclient/core/middleware.py` or `webclient/core/middleware/`,
  `webclient/webclient/urls.py`, and all model files exposing
  `get_ident_cely_link` to T05/XSS scope.

### T06 Celery Analysis

Source: `T06_prompt_update.md`
Disposition: retained implementation evidence.

- Record that this project uses `django_celery_beat`; database-managed beat
  schedules cannot be fully audited from repository files alone.
- For external calls in tasks, explicitly check missing HTTP timeouts and missing
  retry policies, and write them under `error_handling_issues` or
  `timeout_issues`.
- Decide whether helper tasks such as `write_value_to_redis` and simple wrappers
  need detailed task-level entries or can be summarized by module while focusing
  detailed analysis on domain-critical tasks.

### T07 Frontend Analysis

Source: `T07_prompt_update.md`
Disposition: retained implementation evidence.

- Systematically search for larger inline scripts in key templates such as
  `base.html`, describe them, and list extraction candidates under
  `template_inline_scripts.extraction_candidates`.
- If the project uses dark mode, separately assess its implementation:
  `prefers-color-scheme`, data attributes, and SCSS layering should be summarized
  in `frontend_analysis.json`.
- For CDN scripts such as Google Tag Manager or Analytics, document SRI status
  but do not automatically treat missing SRI as a security defect for
  first-party tooling.

### T08 Documentation Analysis

Source: `T08_prompt_update.md`
Disposition: retained implementation evidence.

- Include documentation generators that call `subprocess`, especially license or
  conversion scripts, and assess return-code checks, invalid-output handling, and
  CI-readable errors.
- For Selenium/test documentation, verify whether the generator enforces required
  sections such as `Steps` and `Expected`, and define what should happen when
  those sections are missing, including whether CI should fail.

### T09 CI/CD Analysis

Source: `T09_prompt_update.md`
Disposition: retained implementation evidence.

- Review not only test workflows and pre-commit hooks, but also container
  scanners such as Docker Scout or Trivy and static analysis such as CodeQL or
  Bandit.
- Check whether `.github/dependabot.yml` covers Python dependencies and GitHub
  Actions; propose configuration when missing.
- In `cicd_analysis.json`, record how CI/CD supports security: image signing,
  SBOM, SARIF upload, provenance, and similar controls.

### T10 Scripts Analysis

Source: `T10_prompt_update.md`
Disposition: retained implementation evidence.

- Treat configuration files such as `crontab.txt` and `uwsgi_site.ini` as related
  artifacts, not executable scripts to analyze line by line. Document what they
  launch, schedule, or configure, and any resulting logging/error-handling risk.
- Keep documentation generators under T08; T10 should cover only the root
  `scripts/` directory.
- Standardize `scripts_analysis.json` issue entries with `id`, `severity`,
  `summary`, `scripts`, and `recommendation`.
- For shell scripts, check `set -e`, `set -u`, and `set -o pipefail`. For scripts
  that run destructive operations such as `DROP DATABASE`, `rm -rf`, or file
  overwrite, verify required environment variables or arguments.

## Cleanup Decision

The original `.agents/prompts/prompt_evolution/` directory is no longer an active
feedback channel. The implementation-relevant notes from every legacy source
file are preserved above, and the retired source files can remain deleted. New
workflow-evolution feedback remains sibling-local evidence unless a maintainer
explicitly approves a backlog handoff.
