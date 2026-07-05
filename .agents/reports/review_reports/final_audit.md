# Final Audit - AMCR (aiscr-webamcr)

**Date:** 2026-03-13  
**Purpose:** Synthesis of the results of tasks T01–T10 of the technical repository review.  
**Source artifacts:** `.agents/analysis/*.json`, `.agents/reports/review_reports/T01.md`–`T10.md` (incl. T03c, T03d, T07b), `bugs.md`, `refactoring_backlog.md`.

---

## 1. Major Architectural Issues

- **The overgrown `core` application** — 78 Python files, 26 migrations, imported by 16+ applications. It bundles middleware, permissions, constants, signals, logging, connectors (Fedora, Redis), coordinate transformations, and management commands. Any change has a global impact. See refactoring_backlog ARCH-01.
- **The `dokument` application** — the highest fan-out (8 cross-app imports), 10 models (incl. 5 M2M through tables), 18 migrations. Contains eval() on data from the DB (SEC-ORM-004). See refactoring_backlog ARCH-02.
- **The duality of `xml_generator`** — it serves both as a library of base models (BaseAmcrModel, ModelWithMetadata) and as an XML generator; imported by 10 applications and at the same time in a circular dependency with `adb`. `record_ident_change` contains 7 isinstance branches for cascading metadata saving — architecturally critical code. See ARCH-03, CIRC-02.
- **`historie.HistorieVazby`** — an architecturally critical model; used as a OneToOne FK from Projekt, Dokument, ArcheologickyZaznam, SamostatnyNalez, Pian, ExterniZdroj, User. A central audit log with 42 change types.
- **Applications without tests** — `cron`, `notifikace_projekty`, `fedora_management`, `healthcheck`, `neidentakce`, `services`, `vypis`, `xml_generator`. For `cron` and `notifikace_projekty` these are Celery tasks without a testing net. See repository_map.json, refactoring_backlog ARCH-04.

---

## 2. Security Risks (Prioritized)

**High Priority**

- **DEBUG fallback in production** — `get_secret("DEBUG", "True")` in `production.py` means that with a missing key the application runs with DEBUG=True. See BUG-010, security_analysis.json SEC-01.

**Medium Priority**

- **Grafana / Elasticsearch / Logstash** — incorrect password injection: `GF_SECURITY_ADMIN_PASSWORD` set to a file path instead of the value; ELASTIC_PASSWORD and LOGSTASH_INTERNAL_PASSWORD to the secret name. See BUG-007, BUG-008, docker_analysis.json SEC-D02, SEC-D03.
- **sudo in the production container** — `usermod -aG sudo user` in the Dockerfile. See BUG-009, SEC-D01.
- **Missing Django security headers** — SECURE_HSTS_SECONDS, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, SECURE_CONTENT_TYPE_NOSNIFF are not in production.py. See security_analysis.json SEC-03.
- **mark_safe() with values from the DB** — in `vypis/fields.py` and `vypis/views.py` on values from models; potential XSS. See BUG-012, security_analysis.json XSS-02 through XSS-04.
- **Mailtrap credentials in a commit** — sample_secrets_mail_client.json contains seemingly real credentials. See BUG-011, SEC-02.
- **eval() in the identifier generators** — 5 places in projekt/models.py, arch_z/models.py, dokument/models.py, and ez/models.py use `eval(i)` on values from the DB. See BUG-001, orm_analysis.json SEC-ORM-001–SEC-ORM-005.

**Low / Recommendations**

- A CVE audit of the dependencies was not performed (offline environment). Recommended: `pip audit` or `safety check` in CI. See security_analysis.json known_vulnerabilities, refactoring_backlog SEC-04.

---

## 3. Circular and Problematic Dependencies

- **projekt ↔ oznameni** (High) — mutual imports at the module level: oznameni/models imports Projekt; projekt/forms, views, urls import from oznameni. Risk of ImportError on extension. See dependency_graph.json CIRC-01, refactoring_backlog CIRC-01.
- **adb ↔ xml_generator** (Medium) — adb.models imports BaseAmcrModel from xml_generator.models; xml_generator.generator imports VyskovyBod from adb.models at the module level. See dependency_graph.json CIRC-02, refactoring_backlog CIRC-02.

---

## 4. High-Complexity Modules

- **core** — fan-in 16, 78 .py files, the largest number of responsibilities (middleware, permissions, signals, logging, connectors, ident_cely, management commands). Recommended to decompose into core.permissions, core.logging, core.middleware, core.signals.
- **heslar** — fan-in 16; central controlled vocabularies, the coupling is natural, but Critical for performance (see the missing index on nazev_heslare — BUG-005).
- **xml_generator** — fan-in 10; a combination of base models and an XML generator.
- **uzivatel** — fan-in 11.
- **dokument** — fan-out 8.

See dependency_graph.json tightly_coupled_modules and architectural_issues.

---

## 5. ORM Performance Issues

- **N+1 in the check_pred_* methods** — `Projekt.check_pred_uzavrenim()` and `ArcheologickyZaznam.check_pred_odeslanim()` iterate over akce/DJ without prefetch; cascading queries. See BUG-002, orm_analysis.json NP1-002, NP1-006, refactoring_backlog ORM-02.
- **Extra SELECT in save()** — ArcheologickyZaznam and SamostatnyNalez, on every save() (pk != None), call `Model.objects.get(pk=self.pk)` to detect a change of pristupnost. The correct pattern: an initial value in __init__(). See orm_analysis.json NP1-008, NP1-012, refactoring_backlog ORM-01, BUG-004.
- **Missing indexes** — pas.SamostatnyNalez (projekt, katastr, pristupnost, stav); heslar.Heslar.nazev_heslare (used in limit_choices_to across the application). See orm_analysis.json, BUG-005, refactoring_backlog ORM-03.
- **len(queryset.all()) instead of .count()** — in Projekt.check_pred_smazanim/check_pred_navrzeni_k_zruseni. See orm_analysis.json NP1-003.
- **Deprecated .extra()** — arch_z/filters.py for ST_Z(geom). See orm_analysis.json raw_sql_usage, refactoring_backlog ORM-06.

Additional N+1 and ORM candidates (Low to Medium severity): NP1-001 (check_pred_archivaci), NP1-004 (set_pristupnost), NP1-005 (datum_oznameni property), NP1-007 (_set_connected_records_ident bulk_update), NP1-009 (User.save), NP1-010 (moje_spolupracujici_organizace), NP1-011 (Pian.pristupnost_pom), NP1-013 (Pian.get_create_org triple-hop), NP1-014 (ModelWithMetadata.record_deletion), NP1-015 (Dokument.check_pred_odeslanim — iteration over DJ without prefetch), NP1-016 (ExterniZdroj.check_pred_odeslanim — iteration over links), NP1-017 (ExterniZdrojSekvence.save — extra SELECT on get(pk=pk) for pristupnost), NP1-018 (Komponenta.check_pred_odeslanim — 3 sub-queries for finds), NP1-019 (KomponentaVazby — cascading FK without select_related), NP1-020 (Lokalita.set_snapshots — filter+iterate pattern). Complete overview: orm_analysis.json n_plus_one_candidates, missing_prefetch_candidates.

**Faulty method overriding:**

- **BUG-015: NalezPredmet.__init_ typo** — `__init_` instead of `__init__` (one underscore missing) in nalez/models.py:116. The custom initialization never runs; the variables `initial_druh` etc. remain undefined. See bugs.md BUG-015.

---

## 6. Database Risks

- **Migrations** — ~213 migrations in total; uzivatel (31), core (26), arch_z (20), dokument (19), heslar (17), historie (16) are candidates for squash. See orm_analysis.json migration_summary, refactoring_backlog ORM-07.
- **Heslar.nazev_heslare** — FK without db_index with massive use in limit_choices_to → table scans in forms. See BUG-005.
- **Raw SQL** — parameterized use in core/utils.py and arch_z/filters.py; the management command transform_to_sjtsk uses raw without parameters (internal admin). See orm_analysis.json raw_sql_usage, security_analysis.json raw_sql_usage.
- **eval() on segments of ident_cely** — projekt/models.py, arch_z/models.py, dokument/models.py, ez/models.py (5 places in total); a security and robustness risk. See BUG-001, SEC-ORM-001–SEC-ORM-005.

---

## 7. Docker Build Issues

- **Secret injection** — Grafana (GF_SECURITY_ADMIN_PASSWORD vs __FILE), Elasticsearch and Logstash (value = secret name). See docker_analysis.json security_issues SEC-D02, SEC-D03, BUG-007, BUG-008.
- **Production container** — user with sudo (SEC-D01); cron daemon inside the container (OPT-D05); libgdal-dev in runtime; redundant COPY in multi-stage (OPT-D01). See docker_analysis.json.
- **Fedora Dockerfile** — multiple RUN apt-get update without clean; CMD runs two processes without PID 1 management (OPT-D04). See docker_analysis.json optimization_opportunities.
- **Versions** — ELK prod 9.3.1 vs dev 8.19.0 (major gap); memcached:latest in dev (floating tag). See docker_analysis.json version_inconsistencies.
- **Selenium in the production compose** — the service should be only in docker-compose-test.yml. See docker_analysis.json docker_compose_services issues DCD-07.

Additional Docker compose problems: DCD-01 (logstash without depends_on), DCD-02 (celery -l DEBUG in production), DCD-06 (monitoring exposed without isolation), DCD-08 through DCD-13 (xpack inconsistency, floating tags, hardcoded passwords). Optimizations: OPT-D02 (compileall duplication), OPT-D03 (3× apt-get update). Complete detail: docker_analysis.json, refactoring_backlog DOCKER-*.

---

## 8. Frontend and JavaScript Risks

- **Inline scripts in base.html** — datepicker initialization, checkUserAuthentication (60 s polling), the language switcher; candidates for extraction into separate JS files. See frontend_analysis.json template_inline_scripts.extraction_candidates, refactoring_backlog FRONT-01.
- **Custom JS without minification/bundler** — the map and helpers are served as multiple files; a larger number of requests and size. In total, 24 custom JS files (~5,600 lines) analyzed. See frontend_analysis.json build_pipeline, refactoring_backlog FRONT-02.
- **Map scripts — crash on empty layers** (High) — `poi_sugest.getLayers()[0]._latlng` in mapa_arch_z.js, mapa_pas.js, mapa_projekty.js, and others: a crash if the layer has no geometry. The access `coordinates[0][0]` without an array-length check. See frontend_analysis.json custom_javascript.issues.
- **XHR without onerror** (High) — none of the map scripts (mapa_arch_z.js, mapa_pas.js, mapa_projekty.js, mapa_doc.js, mapa_oznameni.js) has an `xhr.onerror` handler; a network error is silently ignored. See refactoring_backlog FRONT-03.
- **JSON.parse without try/catch** (Medium) — mapa_arch_z.js, mapa_pas.js, dz.js, mapa_oznameni.js parse server responses without protection; a corrupted response breaks the whole script. See refactoring_backlog FRONT-04.
- **BUG-016: Inverted condition** (Medium) — form_fields_disabling.js line 64: `||` instead of `&&`; the condition for disabling form fields is always true. See bugs.md BUG-016.
- **BUG-017: Wrong coordinate precision** (Medium) — coor_precision.js line 31: the JTSK precision uses the constant for WGS84 (6 decimal places instead of 2). See bugs.md BUG-017.
- **dz.js — Leaflet API mismatch** (High) — a call to `clearLayers()` on an `L.geoJSON` object, but the correct method is on FeatureGroup/LayerGroup. `addData()` after `clearLayers()` may not work as expected.
- **Implicit global variables** — map_functions, mapa_pins.js, and most map scripts declare variables without `var`/`let`/`const`; name conflicts are possible when loaded together. See refactoring_backlog FRONT-06.
- **Duplicated pin-factory pattern** — mapa_pins.js repeats a ~30-line block for each pin category; a candidate for a generic solution via a factory function. See refactoring_backlog FRONT-05.
- **Minor bugs** — mapa_basic_functions.js: an undefined variable in getLocation(); ajax_functions.js: GET without handling of network errors. See frontend_analysis.json custom_javascript.issues.
- **CDN/SRI** — Google Tag Manager without SRI; for first-party tools documented as acceptable. See frontend_analysis.json cdn_sri_issues.

---

## 9. Celery and Asynchronous Risks

- **Missing error handling** — update_all_redis_snapshots, update_single_redis_snapshot, update_materialized_views without a central try/except; an error in the middle of a batch terminates the task without a summary. See celery_analysis.json error_handling_issues, refactoring_backlog CELERY-01.
- **call_digiarchiv_update_task** — requests.get() without a timeout and without try/except; if the service is down, the worker may hang. See celery_analysis.json timeout_issues, refactoring_backlog CELERY-02.
- **check_hlidaci_pes** — polling (sleep 0.5 s) for the creation of a project in the DB without an upper time limit; on a rollback or a misconfiguration it may run for a long time. See celery_analysis.json race_condition_candidates, timeout_issues, refactoring_backlog CELERY-03.

The beat schedule is in the DB (django_celery_beat); the specific schedules cannot be read from the code.

---

## 10. Documentation Generator Issues

- **Read the Docs** — installs the full webclient/requirements.txt (including Selenium, debug-toolbar); it lengthens the build and increases the risk of conflicts. See documentation_analysis.json sphinx_docs.issues, refactoring_backlog DOCS-01.
- **docs/licenses/convert_to_rst.py** — no check of the subprocess returncode or try/except around json.loads; on a pip-licenses error, an unreadable traceback. See documentation_analysis.json documentation_generators issues, refactoring_backlog DOCS-02.
- **Selenium docstrings** — the generator expects Steps and Expected sections; missing sections lead to incomplete documentation without failing. Recommended: a CI completeness check. See documentation_analysis.json coverage_gaps, refactoring_backlog DOCS-03.

generate_module_docs.py and generate_selenium_test_docs.py have no serious problems recorded in the analysis.

---

## 11. CI/CD Gaps

- **Dependabot** — .github/dependabot.yml is missing for dependency tracking. See cicd_analysis.json security_scanning, refactoring_backlog CI-01.
- **CodeQL** — there is no separate workflow for static analysis of the Python code; only Trivy/SARIF from publish_images. See cicd_analysis.json issues.
- **Workflow timeouts** — run-tests 180 min, pre_commit 15 min, deployment 60 min — set; no workflow without a timeout.
- **Pre-commit** — installs the full requirements.txt; with a future increase in time it may be worth separating a minimal requirements set for lint. See cicd_analysis.json issues.

Positives: Docker Scout on PR to dev; publish_images with cosign, SLSA, Trivy, SARIF upload; pre-commit including generation of module and Selenium documentation.

---

## 12. Major Technical Debt (Top 10)

| # | Item | Source | Justification |
|---|--------|-------|------------|
| 1 | DEBUG fallback "True" in production.py | BUG-010, SEC-01 | With a missing secret, production runs with DEBUG=True — a critical security risk. |
| 2 | eval() on data from the DB in the identifier generators (5 places) | BUG-001, SEC-ORM-001–005 | Arbitrary code execution; extended from 3 to 5 places (+ dokument, ez). |
| 3 | Circular dependency projekt ↔ oznameni | CIRC-01 | Unstable architecture, risk of ImportError on extension. |
| 4 | N+1 in the check_pred_* methods (20 candidates) | BUG-002, ORM-02, NP1-* | Dozens of queries on every attempt to change state; extended from 14 to 20 candidates. |
| 5 | The overgrown core application (78 .py, 16+ dependent) | ARCH-01 | Global impact of changes, difficult maintenance and testing. |
| 6 | Secret injection Grafana/Elasticsearch/Logstash | BUG-007, BUG-008, SEC-D02/D03 | Passwords are not correctly loaded from Docker secrets. |
| 7 | sudo in the production Docker image | BUG-009, SEC-D01 | Privilege escalation on an exploit. |
| 8 | Missing db_index on Heslar.nazev_heslare | BUG-005 | Table scans on every form with limit_choices_to on the heslář. |
| 9 | Map scripts — crash + missing error handling | BUG-016, BUG-017, FRONT-03–06 | 7 high issues; XHR without onerror, crash on empty layers, JSON.parse without protection. |
| 10 | Celery tasks without error handling (Redis snapshots, materialized views) | CELERY-01 | Failure in the middle of a batch without a summary and without retry. |

---

## 13. Prioritized Refactoring Plan

**First wave (security and critical operation)**

- Fix the DEBUG fallback to "False" in production.py (S).
- Fix the secret injection for Grafana (GF_*__FILE), Elasticsearch, and Logstash (entrypoint wrapper) (S).
- Replace eval() in the identifier generators with safe parsing (5 places: projekt, arch_z, dokument, ez) (S). See BUG-001.
- Remove sudo from the production user in the Dockerfile (S).
- Add Django security headers and include `manage.py check --deploy` in CI (S).
- restore_database.sh: set -e and validation of DBNAME, USED_DB_BACKUP, DB_FLAG_ROLE (S).

**Second wave (architecture and ORM)**

- Decide on breaking the circular dependency projekt ↔ oznameni (merge or extract into core) (L).
- Prefetch at the call sites of check_pred_uzavrenim/check_pred_odeslanim; possibly refactor the check methods to accept prefetched data (M). Now also includes Dokument.check_pred_odeslanim (NP1-015), ExterniZdroj.check_pred_odeslanim (NP1-016), Komponenta.check_pred_odeslanim (NP1-018).
- Add initial_pristupnost in __init__() and remove the extra SELECT in save() for ArcheologickyZaznam, SamostatnyNalez, and ExterniZdrojSekvence (S). See NP1-017.
- Fix the NalezPredmet.__init_ typo (missing underscore) — the custom initialization does not run (S). See BUG-015.
- Add db_index to Heslar.nazev_heslare and to pas.SamostatnyNalez (projekt, katastr, pristupnost, stav) (S).

**Third wave (Celery, scripts, frontend, CI)**

- Error handling and a summary in update_all_redis_snapshots, update_materialized_views, update_single_redis_snapshot (S).
- Timeout and try/except for call_digiarchiv_update_task; limiting the polling in check_hlidaci_pes (S/M).
- set -e in the deploy and maintenance scripts; common.sh for the shared functions (S/M).
- db_connection_from_docker-web.py: reading DB_PORT from the secret (S). See BUG-014.
- Dependabot + optionally CodeQL for Python (S).
- Add XHR onerror handlers to the map scripts (S). See FRONT-03.
- Add try/catch around JSON.parse in the map scripts and dz.js (S). See FRONT-04.
- Fix the inverted condition in form_fields_disabling.js (S). See BUG-016.
- Fix the JTSK precision constant in coor_precision.js (S). See BUG-017.

**Fourth wave (long-term)**

- Decomposition of core into smaller modules (XL).
- Splitting xml_generator into amcr_base and a generator; removing CIRC-02 (M).
- Squash migrations for uzivatel, core, arch_z, dokument, heslar, historie (M). Now 213 migrations (extended scope).
- Separating requirements (prod / dev / test / docs); DOCS requirements for Read the Docs (S).
- Extraction of inline scripts from base.html; considering a bundler for the custom JS (S/M).
- Refactor mapa_pins.js — a factory function instead of the repeated block (S). See FRONT-05.
- Elimination of the implicit global variables in the map scripts (M). See FRONT-06.

Details and effort: refactoring_backlog.md (High / Medium / Low priority).

---

## 14. Long-Term Repository Maintenance Recommendations

- **Governance** — Keep the rules in AGENTS.md and CONTRIBUTING.md as the source of truth; in case of a conflict with .agents/, adjust .agents/ and record it in review_cache or refactoring_backlog. See AGENTS.md.
- **Review cycle** — Before each session, load review_cache.json and the file hashes; mark changed files and the relevant tasks as pending; do not repeat completed tasks without a change of inputs. See review_codebase.md INITIALIZATION SEQUENCE.
- **Configuration** — A single source of limits and directories: review_config.yaml. Do not multiply vendored exclusions and the task registry elsewhere. See review_config.yaml.
- **Bug and backlog** — Before adding an entry to bugs.md, check GitHub Issues (currently 113 open); cross-reference "already tracked / extension / new candidate". Maintain the refactoring backlog in English and sort by priority (High / Medium / Low). See review_codebase.md BUG TRACKING and REFACTORING BACKLOG.
- **Workflow-evolution evidence** — Legacy prompt-evolution notes were classified and folded into review_config.yaml and the canonical aiscr-codebase-review workflow; the temporary evidence report was removed. New feedback from U05 requires explicit approval of the report-to-backlog handoff.
- **Documentation and CI** — Do not edit the generated documentation manually; run the generators per CONTRIBUTING.md. In CI, consider a completeness check of the Selenium docstrings and `manage.py check --deploy`; a CVE step (pip audit/safety) for the dependencies.
- **.agents/ structure** — Keep it per .agents/README.md: config (review_config.yaml, review_cache.json), analysis (*.json), reports (review_reports/, bugs.md, refactoring_backlog.md), and prompts.

---

*The final audit was created by synthesizing the outputs of tasks T01–T10 (incl. sub-tasks T03c, T03d, T07b). For detailed evidence see the listed JSON files in .agents/analysis/, the reports T01.md–T10.md (incl. T03c.md, T03d.md, T07b.md), .agents/reports/bugs.md (17 bugs), and refactoring_backlog.md.*

---

## Changelog

### 2026-03-13 — Cross-validation and incremental update

**Source:** Cross-validation (U03) + incremental update (U01–U06).

**Change detection:** 43 of 61 tracked files changed (T01: 18, T02: 7, T04: 10, T05: 8). No files deleted or newly added.

**Fixed inconsistencies:**

- ARCH-04: prefix corrected `[T02]` → `[T01]` in refactoring_backlog.md (the source of the finding is T01, not T02).
- BUG-004: severity raised from Low to Medium in bugs.md (alignment with the ORM-01 backlog priority — the extra SELECT in save() is an architectural anti-pattern).
- BUG-005 / ORM-03: kept Medium — the difference from the backlog (High priority) is intentional and documented (refactoring priority ≠ bug severity).

**Coverage gaps:**

- **T03 (ORM):** ✅ RESOLVED (T03c/T03d, 2026-03-13). All 10 missing Django applications (28 models, ~2,793 lines) were analyzed and added to `orm_analysis.json`. New findings: SEC-ORM-004, SEC-ORM-005 (2 more eval() occurrences in dokument/ez — extends BUG-001 from 3 to 5 places), NP1-015 through NP1-020 (6 new N+1 candidates), BUG-015 (typo `__init_` in nalez/NalezPredmet).
- **T07 (Frontend):** ✅ RESOLVED (T07b, 2026-03-13). Vendored exclusions updated (timer.js, datepicker-cs.js). 20 custom JS files (~3,846 lines) analyzed and added to `frontend_analysis.json`. New findings: BUG-016 (inverted condition in form_fields_disabling.js), BUG-017 (wrong precision in coor_precision.js), 4 backlog items (FRONT-03 through FRONT-06). High severity for 7 issues in the map scripts and dz.js.

**Bug verification:** All 14 original bugs (BUG-001 through BUG-014) confirmed as still present (spot-check of 7 of them, none fixed). 3 new bugs added: BUG-015, BUG-016, BUG-017.

**Architectural findings verified:** CIRC-01, CIRC-02, ARCH-01 confirmed; `core` grew to 78 .py files (from 77).

**IDs added to the final audit:** SEC-ORM-001/002/003 (§2), NP1-001/004/005/007/009/010/011/013/014 (§5), DCD-01/02/06/08–13, OPT-D02/D03 (§7), SCRIPTS-01/SCRIPTS-03 (§12 TOP 10 #9).

**Prompt evolution:** 42/42 proposals incorporated into review_codebase.md (the remaining 2 — the domain entity table and the core warning — added as part of this update).

### 2026-03-13 — Closing coverage gaps (T03c/T03d + T07b)

**Source:** Targeted analysis to close the coverage gaps identified in the previous changelog.

**Change detection:** 0 tracked files in the repository changed. Changes only in the `.agents/` artifacts.

**Fixed inconsistencies:**
- BUG-001: extended from 3 to 5 eval() occurrences (added dokument/models.py:441 and ez/models.py:301).

**Coverage gaps:**
- **T03 (ORM):** ✅ CLOSED. T03c analyzed 4 critical applications (dokument — 10 models, historie — 2 models, ez — 4 models, xml_generator — 2 abstract models). T03d analyzed 6 smaller applications (komponenta — 3, lokalita — 1, nalez — 2, dj — 1, neidentakce — 2, notifikace_projekty — 1). A total of 26 new model entries added to orm_analysis.json.
- **T07 (Frontend):** ✅ CLOSED. Vendored exclusions updated (+2: timer.js, datepicker-cs.js). 20 custom JS files analyzed and added to frontend_analysis.json (24 files covered in total).
- **T10:** ✅ CLOSED. Configuration files (crontab.txt, uwsgi_site.ini) documented in `scripts_analysis.json` → `config_notes`; tracked in `review_cache.json` with `task_id: T10`.

**Bug verification:** All 17 bugs (BUG-001 through BUG-017) confirmed as present. Spot-check: BUG-015 (nalez/models.py:116 `__init_`), BUG-016 (form_fields_disabling.js:64 `||` instead of `&&`), BUG-017 (coor_precision.js:31 `wgs84` instead of `jtsk`), SEC-ORM-004 (dokument/models.py:441 `eval(i)`), SEC-ORM-005 (ez/models.py:301 `eval(i)`) — all verified by directly reading the files.

**New findings:**
- BUG-015: `__init_` typo in nalez/NalezPredmet — the custom init does not run (Medium)
- BUG-016: inverted condition `||` instead of `&&` in form_fields_disabling.js (Medium)
- BUG-017: wrong JTSK precision uses the WGS84 constant in coor_precision.js (Medium)
- SEC-ORM-004, SEC-ORM-005: 2 new eval() occurrences on data from the DB (Medium)
- NP1-015 through NP1-020: 6 new N+1 candidates in dokument, ez, lokalita
- FRONT-03 through FRONT-06: 4 new backlog items (XHR onerror, JSON.parse try/catch, pin factory, implicit globals)

**Prompt evolution:** 57/57 proposals incorporated. The remaining 6 (T01 scope, T05 credentials, T09 CI, T10 scripts) added — see the changelog "Prompt evolution addition".

**Cross-validation:** review_tools.py all: 0 errors, 0 new warnings. lint-artifacts: 0 errors. id-inventory: SEC-ORM-005 is now referenced in the final_audit.

### 2026-03-13 — Update of the audit body (§1–§14)

The previous two changelogs updated only the Changelog section and lines 215-219 (coverage gaps). This update reflects the T03c/T03d/T07b findings into all relevant sections of the main audit body:

- **§1:** core 77→78 .py; dokument extended with model count + SEC-ORM-004; xml_generator supplemented with record_ident_change; new point: historie.HistorieVazby as an architecturally critical model.
- **§2:** eval() extended from 3 to 5 places (+ dokument, ez); SEC-ORM-001–005.
- **§4:** core 78 .py (corrected count).
- **§5:** Added NP1-015 through NP1-020 to the list of further candidates; a new subsection "Faulty method overriding" with BUG-015.
- **§6:** Migrations ~152→~213; eval() extended to 5 places; heslar and historie added as squash candidates.
- **§8:** Completely reworked — added 9 new points (crash on empty layers, XHR without onerror, JSON.parse, BUG-016, BUG-017, Leaflet API mismatch, implicit globals, pin-factory duplication); overall summary of analyzed files 24 (~5,600 lines).
- **§12 (TOP 10):** Rearranged — eval() promoted to #2, N+1 extended to 20 candidates (#4), the map scripts enter at #9; the deploy scripts and the extra SELECT dropped out of the TOP 10.
- **§13:** eval() fix added to the first wave; the second wave extended with NP1-015/016/017/018 and BUG-015; the third wave extended with FRONT-03/04 and BUG-016/017; the fourth wave extended with FRONT-05/06 and the squash scope.
- **Final paragraph:** Updated to 17 bugs and an explicit reference to the T03c/T03d/T07b reports.

### 2026-03-13 — Prompt evolution addition and closing of T10

**Prompt evolution:** The remaining 6 proposals from T01/T03c/T03d/T05/T07b/T09 incorporated into `review_codebase.md`. Overall state: 57/57 proposals incorporated.

Specific changes in `review_codebase.md`:
- **T01 scope:** `pyproject.toml` supplemented with a note that it does not exist in the repository (T02 section, line "external libraries"). `webclient/locale` removed from `review_config.yaml` → `important_directories` (the directory does not exist).
- **T03 (ORM):** Added detection of `eval()` patterns in all identifier generators (not only projekt/arch_z). Added a check for `__init__` typos (missing underscore).
- **T05 (Security):** Added a requirement to determine the Django framework version from `requirements.txt` and to cite version-specific security defaults.
- **T07 (Frontend):** Added a check of Leaflet API correctness (clearLayers, addData on the correct layer type). Added detection of De Morgan errors in logical operators (`||` vs `&&`). Added a note about vendored files without a `/*!` header but with a `/**` JSDoc header.
- **T09 (CI/CD):** Added a requirement to summarize the supply-chain security capabilities (signing, SBOM, SARIF, provenance) in the `security_scanning` section.

**T10:** Reassessed to ✅ CLOSED — the configuration files (crontab.txt, uwsgi_site.ini) are already documented in `scripts_analysis.json` → `config_notes` and tracked in `review_cache.json`.
