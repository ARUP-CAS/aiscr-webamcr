# Tracked bugs — AMČR (aiscr-webamcr)

> Review prose follows the canonical English-default rule; verbatim Czech is preserved where exact source wording, field names, or AIS CR domain identifiers matter.
> Before adding a new bug, check the existing GitHub Issues (currently 113 open).
>
> Statuses: `already tracked (Issue #XXX)` | `extends existing issue #XXX` | `new issue candidate`
>
> Severity values: `Critical` | `High` | `Medium` | `Low`

---

<!-- Entries are added by agents after completing individual tasks -->

### BUG-001: eval() on values from the database in the identifier generators

- **Files:**
  - `webclient/projekt/models.py:663` — `Projekt.set_permanent_ident_cely()`
  - `webclient/arch_z/models.py:331` — `ArcheologickyZaznam.set_lokalita_permanent_ident_cely()`
  - `webclient/arch_z/models.py:889` — `get_akce_ident()`
  - `webclient/dokument/models.py:441` — `Dokument.set_permanent_ident_cely()` *(found in T03c)*
  - `webclient/ez/models.py:301` — `get_perm_ez_ident()` *(found in T03c)*
- **Severity:** Medium
- **GitHub Issue:** new issue candidate
- **Description:** All five places use `eval(i)` to convert a textual number (a segment of `ident_cely` from the DB) to an integer. Although the values are internally generated and their format is controlled by the application, `eval()` is an inherently dangerous function — if the ident_cely format were compromised (e.g. by a faulty data migration), arbitrary Python code could be executed. See SEC-ORM-001 through SEC-ORM-005 in `orm_analysis.json`.
- **Recommended fix:** Replace `eval(i)` with `int(i)` in all five places. Add format validation before the conversion (e.g. `i.isdigit()`).
- **Task:** T03

---

### BUG-002: N+1 queries in ArcheologickyZaznam.check_pred_odeslanim() and Projekt.check_pred_uzavrenim()

- **Files:**
  - `webclient/arch_z/models.py:240-268`
  - `webclient/projekt/models.py:561-578`
- **Severity:** Medium
- **GitHub Issue:** new issue candidate
- **Description:** `check_pred_odeslanim()` calls `self.dokumentacni_jednotky_akce.all()` twice and, for each DJ, makes a query on `dj.komponenty.komponenty.all()`. `check_pred_uzavrenim()` calls `self.akce_set.all()` twice and, for each akce, runs a cascading `check_pred_odeslanim()`. These methods are called on every attempt to advance the record's state — for projects with multiple akce and DJ, the number of queries can reach dozens.
- **Recommended fix:** Add `prefetch_related` in the view methods before calling `check_pred_*`. Refactor the `check_pred_*` methods to accept prefetched data as a parameter.
- **Task:** T03

---

### BUG-003: Import of cached_property from distlib.util instead of functools

- **Files:** `webclient/uzivatel/models.py:28`
- **Severity:** Low
- **GitHub Issue:** new issue candidate
- **Description:** `from distlib.util import cached_property` — `distlib` is a packaging tool (part of pip), not Django or the Python standard library. The correct implementation is `from functools import cached_property` (Python 3.8+). The import works, but it is unreliable as a dependency and confusing for developers.
- **Recommended fix:** `from functools import cached_property`
- **Task:** T03

---

### BUG-004: Extra SELECT in SamostatnyNalez.save() — the initial_pristupnost pattern is incomplete

- **File:** `webclient/pas/models.py:182-186`
- **Severity:** Medium
- **Alignment:** Severity raised from Low to Medium (2026-03-13); the extra SELECT runs on every record save and is an architectural anti-pattern — it corresponds to the High-priority classification of ORM-01 in refactoring_backlog.md.
- **GitHub Issue:** new issue candidate — cannot verify, GitHub Issues unavailable without authentication
- **Description:** The `SamostatnyNalez` model has an `initial_pristupnost` property, but its `save()` method still unconditionally calls `SamostatnyNalez.objects.get(pk=self.pk)` on every record save (where `pk is not None`). The correct pattern stores the initial value in `__init__()`, which eliminates the extra SELECT.
- **Recommended fix:** Add to `__init__()`: `self._initial_pristupnost = self.pristupnost`. In `save()`, compare `self._initial_pristupnost != self.pristupnost` without the extra SELECT.
- **Task:** T03b

---

### BUG-005: Missing db_index on Heslar.nazev_heslare (an FK used globally in limit_choices_to)

- **File:** `webclient/heslar/models.py:22-23`
- **Severity:** Medium
- **GitHub Issue:** new issue candidate — cannot verify, GitHub Issues unavailable without authentication
- **Description:** The `Heslar.nazev_heslare` field is an FK to `HeslarNazev` without `db_index=True`. This field is filtered in `limit_choices_to` in dozens of FK fields across the entire application (proj, pas, arch_z, uzivatel, dokument, adb, heslar, etc.). The absence of an index causes a table scan on the `heslar` table for every form query.
- **Recommended fix:** Add `db_index=True` to the `nazev_heslare` FK definition in `heslar/models.py`. Alternatively add an explicit `models.Index(fields=["nazev_heslare"])` in `Meta.indexes`.
- **Task:** T03b

---

### BUG-006: get_vyskovy_bod() calls .count() twice on the same queryset

- **File:** `webclient/adb/models.py:163-171`
- **Severity:** Low
- **GitHub Issue:** new issue candidate — cannot verify, GitHub Issues unavailable without authentication
- **Description:** The `get_vyskovy_bod()` function calls `vyskove_body.count()` twice — once to test for 0 and once to test for the maximum — each call runs a separate SQL COUNT query.
- **Recommended fix:** Store the result `count = vyskove_body.count()` once and compare `count == 0` and `count <= MAXIMAL_VYSKOVY_BOD + offset`.
- **Task:** T03b

---

### BUG-007: GF_SECURITY_ADMIN_PASSWORD set to a file path instead of the password

- **Files:**
  - `docker-compose.yml:149`
  - `docker-compose-test.yml:169`
  - `git_docker-compose.yml:144`
- **Severity:** Medium
- **GitHub Issue:** new issue candidate — cannot verify, GitHub Issues unavailable without authentication
- **Description:** Grafana `GF_SECURITY_ADMIN_PASSWORD=/run/secrets/grafana_admin_password` sets the admin password to a literal string (the file path), not to the contents of the Docker secret. Grafana does not support automatic reading of Docker secrets via `GF_SECURITY_ADMIN_PASSWORD`; the correct format is `GF_SECURITY_ADMIN_PASSWORD__FILE`. Consequence: the Grafana admin password is the literal string `/run/secrets/grafana_admin_password`.
- **Recommended fix:** Replace `GF_SECURITY_ADMIN_PASSWORD=...` with `GF_SECURITY_ADMIN_PASSWORD__FILE=/run/secrets/grafana_admin_password` in all three files.
- **Task:** T04

---

### BUG-008: ELASTIC_PASSWORD and LOGSTASH_INTERNAL_PASSWORD set to secret names

- **Files:**
  - `docker-compose.yml:180-181,201`
  - `git_docker-compose.yml:172-173,194`
- **Severity:** Medium
- **GitHub Issue:** new issue candidate — cannot verify, GitHub Issues unavailable without authentication
- **Description:** Elasticsearch `ELASTIC_PASSWORD=elastic_pass` and Logstash `LOGSTASH_INTERNAL_PASSWORD=logstash_elastic_pass` have the name of the Docker secret (a string) as their value, not its contents. Neither the Elasticsearch nor the Logstash Docker image supports the `_FILE` variant for these variables. Result: the Elasticsearch bootstrap password is set to the literal `"elastic_pass"` instead of the actual value from the secret.
- **Recommended fix:** Use an entrypoint wrapper script: `export ELASTIC_PASSWORD=$(cat /run/secrets/elastic_pass)` before starting Elasticsearch / Logstash.
- **Task:** T04

---

### BUG-009: sudo access for the application user in the production container

- **File:** `Dockerfile:99`
- **Severity:** Medium
- **GitHub Issue:** new issue candidate — cannot verify, GitHub Issues unavailable without authentication
- **Description:** `usermod -aG sudo user` adds the production application user to the `sudo` group. If an RCE exploit of the application occurs (e.g. via eval() — see BUG-001), an attacker can escalate privileges to root inside the container.
- **Recommended fix:** Remove `usermod -aG sudo user`. For necessary privileged operations (crontab setup), set specific NOPASSWD rules in `/etc/sudoers`.
- **Task:** T04

---

### BUG-010: Dangerous fallback for DEBUG in production.py

- **File:** `webclient/webclient/settings/production.py:3`
- **Severity:** High
- **GitHub Issue:** new issue candidate — cannot verify, GitHub Issues unavailable without authentication
- **Description:** `DEBUG = get_secret("DEBUG", "True") == "True"` — the default fallback is the string `"True"`. If the `DEBUG` key is missing from the secrets file, the production instance starts with `DEBUG=True`. This exposes full Python tracebacks, settings values, and deactivates Django's security checks.
- **Recommended fix:** Change the fallback to `"False"`: `DEBUG = get_secret("DEBUG", "False") == "True"`
- **Task:** T05

---

### BUG-011: Mailtrap credentials in a commit

- **File:** `webclient/webclient/settings/sample_secrets_mail_client.json`
- **Severity:** Medium
- **GitHub Issue:** new issue candidate — cannot verify, GitHub Issues unavailable without authentication
- **Description:** The file contains seemingly real Mailtrap sandbox credentials (`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`). Anyone with access to the repository can use these credentials to log into Mailtrap and read captured test emails.
- **Recommended fix:** Verify whether the credentials are active, and if so, rotate them. Replace them in the file with obvious placeholder values (e.g. `"PLACEHOLDER_USER"`, `"PLACEHOLDER_PASSWORD"`).
- **Task:** T05

---

### BUG-012: mark_safe() with values from the database in vypis/fields.py

- **Files:**
  - `webclient/vypis/fields.py:363` — `mark_safe(value.get_ident_cely_link)`
  - `webclient/vypis/fields.py:438` — `mark_safe(new_instance)`
  - `webclient/vypis/views.py:79` — `mark_safe(field.get_name(instance))`
- **Severity:** Medium
- **GitHub Issue:** new issue candidate — cannot verify, GitHub Issues unavailable without authentication
- **Description:** Three places in `vypis/` apply `mark_safe()` to values derived from database instances or model properties. If these values are not properly escaped before being wrapped in `mark_safe()`, stored XSS may occur. The ident_cely values have a controlled structure, but the pattern is architecturally dangerous and requires explicit verification.
- **Recommended fix:** Audit the `get_ident_cely_link` property, the `get_name()` implementations, and the Dokument.extra_data attribute. Rewrite using `format_html()` or ensure `escape()` before `mark_safe()`.
- **Task:** T05

---

### BUG-013: restore_database.sh does not validate required environment variables before DROP DATABASE

- **Files:** `scripts/restore_database.sh`
- **Severity:** Medium
- **GitHub Issue:** new issue candidate — cannot verify, GitHub Issues unavailable without authentication
- **Description:** The script uses `${DBNAME}`, `${USED_DB_BACKUP}`, `${DB_FLAG_ROLE}` without checking whether they are set. With empty values, an unintended DROP/CREATE may occur (e.g. an empty database name) or an unclear error during pg_restore.
- **Recommended fix:** At the start of the script, verify that `DBNAME`, `USED_DB_BACKUP`, `DB_FLAG_ROLE` are non-empty; on error print usage and exit with exit 1. Add `set -e`.
- **Task:** T10

---

### BUG-014: db_connection_from_docker-web.py ignores DB_PORT from the secret

- **Files:** `scripts/db/db_connection_from_docker-web.py`
- **Severity:** Medium
- **GitHub Issue:** new issue candidate — cannot verify, GitHub Issues unavailable without authentication
- **Description:** The script reads only `DB_NAME`, `DB_PASS`, `DB_USER`, `DB_HOST` from `/run/secrets/db_conf`. The PostgreSQL connection therefore always uses the default port 5432. If the database is on a different port, the health check fails or checks a different instance.
- **Recommended fix:** Also read `DB_PORT` from the JSON (with a default of 5432) and pass it to `psycopg2.connect(..., port=db_port)`.
- **Task:** T10

---

### BUG-015: NalezPredmet.__init_ — typo in the method name (one underscore missing)

- **Files:** `webclient/nalez/models.py:116`
- **Severity:** Medium
- **GitHub Issue:** new issue candidate
- **Description:** The method is defined as `def __init_(self, ...)` with a single trailing underscore instead of `__init__` with two. Python does not call this method as a constructor, so the custom initialization (`close_active_transaction_when_finished = False`, `active_transaction = None`) is never performed. The sibling model `NalezObjekt` correctly has `__init__`. The impact depends on whether these attributes are used elsewhere (signals, transactions).
- **Recommended fix:** Rename `__init_` to `__init__`.
- **Task:** T03d

---

### BUG-016: form_fields_disabling.js — inverted condition for select/non-select elements

- **Files:** `webclient/static/js/form_fields_disabling.js:65`
- **Severity:** Medium
- **GitHub Issue:** new issue candidate
- **Description:** The condition `element.type != 'select-multiple' || element.type != 'select-one'` is logically always true (De Morgan's law — OR of negations). The branches for select and non-select form elements are thereby inverted. This manifests as incorrect enabling/disabling of fields when the parent select changes.
- **Recommended fix:** Replace the `||` operator with `&&`.
- **Task:** T07b

---

### BUG-017: coor_precision.js — wrong precision constant for JTSK (uses WGS84)

- **Files:** `webclient/static/js/coor_precision.js:31`
- **Severity:** Medium
- **GitHub Issue:** new issue candidate
- **Description:** The `amcr_static_coordinate_precision_jtsk` function uses `global_fixed_precision.wgs84` instead of `global_fixed_precision.jtsk` for a non-array input. JTSK coordinates are rounded with WGS84 precision, which leads to incorrect rounding (typically 6 decimal places for WGS84 vs 2 for JTSK).
- **Recommended fix:** On line 31, replace `global_fixed_precision.wgs84` with `global_fixed_precision.jtsk`.
- **Task:** T07b
