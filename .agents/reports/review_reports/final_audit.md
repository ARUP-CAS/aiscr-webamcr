# Finální audit — AMČR (aiscr-webamcr)

**Datum:** 2026-03-13  
**Účel:** Syntéza výsledků úloh T01–T10 technického review repozitáře.  
**Zdrojové artefakty:** `.agents/analysis/*.json`, `.agents/reports/review_reports/T01.md`–`T10.md`, `bugs.md`, `refactoring_backlog.md`.

---

## 1. Hlavní architektonické problémy

- **Přebujelá aplikace `core`** — 77 Python souborů, 26 migrací, importována 16+ aplikacemi. Sdružuje middleware, permissions, constants, signals, logging, konektory (Fedora, Redis), koordinátové transformace a management commands. Jakákoli změna má globální dopad. Viz refactoring_backlog ARCH-01.
- **Aplikace `dokument`** — nejvyšší fan-out (8 cross-app importů). Potenciální porušení principu jedné zodpovědnosti. Viz refactoring_backlog ARCH-02.
- **Dualita `xml_generator`** — slouží jako knihovna base modelů (BaseAmcrModel, ModelWithMetadata) i jako generátor XML; importována 10 aplikacemi a zároveň v cirkulární závislosti s `adb`. Viz ARCH-03, CIRC-02.
- **Aplikace bez testů** — `cron`, `notifikace_projekty`, `fedora_management`, `healthcheck`, `neidentakce`, `services`, `vypis`, `xml_generator`. U `cron` a `notifikace_projekty` jde o Celery tasky bez testovací sítě. Viz repository_map.json, refactoring_backlog ARCH-04.

---

## 2. Bezpečnostní rizika (prioritizovaná)

**Vysoká priorita**

- **DEBUG fallback v produkci** — `get_secret("DEBUG", "True")` v `production.py` znamená, že při chybějícím klíči běží aplikace s DEBUG=True. Viz BUG-010, security_analysis.json SEC-01.

**Střední priorita**

- **Grafana / Elasticsearch / Logstash** — nesprávná injekce hesel: `GF_SECURITY_ADMIN_PASSWORD` nastaveno na cestu k souboru místo hodnoty; ELASTIC_PASSWORD a LOGSTASH_INTERNAL_PASSWORD na název secretu. Viz BUG-007, BUG-008, docker_analysis.json SEC-D02, SEC-D03.
- **sudo v produkčním kontejneru** — `usermod -aG sudo user` v Dockerfile. Viz BUG-009, SEC-D01.
- **Chybějící Django security headers** — SECURE_HSTS_SECONDS, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, SECURE_CONTENT_TYPE_NOSNIFF nejsou v production.py. Viz security_analysis.json SEC-03.
- **mark_safe() s hodnotami z DB** — ve `vypis/fields.py` a `vypis/views.py` na hodnotách z modelů; potenciální XSS. Viz BUG-012, security_analysis.json XSS-02 až XSS-04.
- **Mailtrap credentials v commitu** — sample_secrets_mail_client.json obsahuje zdánlivě reálné přihlašovací údaje. Viz BUG-011, SEC-02.

**Nízká / doporučení**

- CVE audit závislostí nebyl proveden (offline prostředí). Doporučeno: `pip audit` nebo `safety check` v CI. Viz security_analysis.json known_vulnerabilities, refactoring_backlog SEC-04.

---

## 3. Cirkulární a problematické závislosti

- **projekt ↔ oznameni** (Vysoká) — vzájemné importy na úrovni modulů: oznameni/models importuje Projekt; projekt/forms, views, urls importují z oznameni. Riziko ImportError při rozšíření. Viz dependency_graph.json CIRC-01, refactoring_backlog CIRC-01.
- **adb ↔ xml_generator** (Střední) — adb.models importuje BaseAmcrModel z xml_generator.models; xml_generator.generator importuje VyskovyBod z adb.models na úrovni modulu. Viz dependency_graph.json CIRC-02, refactoring_backlog CIRC-02.

---

## 4. Moduly s vysokou komplexitou

- **core** — fan-in 16, největší počet zodpovědností (middleware, permissions, signals, logging, konektory, ident_cely, management commands). Doporučeno dekomponovat na core.permissions, core.logging, core.middleware, core.signals.
- **heslar** — fan-in 16; centrální číselníky, vazba přirozená, ale kritická pro výkon (viz chybějící index na nazev_heslare — BUG-005).
- **xml_generator** — fan-in 10; kombinace base modelů a generátoru XML.
- **uzivatel** — fan-in 11.
- **dokument** — fan-out 8.

Viz dependency_graph.json tightly_coupled_modules a architectural_issues.

---

## 5. ORM výkonové problémy

- **N+1 v check_pred_* metodách** — `Projekt.check_pred_uzavrenim()` a `ArcheologickyZaznam.check_pred_odeslanim()` iterují přes akce/DJ bez prefetch; kaskádové dotazy. Viz BUG-002, orm_analysis.json NP1-002, NP1-006, refactoring_backlog ORM-02.
- **Extra SELECT v save()** — ArcheologickyZaznam a SamostatnyNalez při každém save() (pk != None) volají `Model.objects.get(pk=self.pk)` pro zjištění změny pristupnost. Správný vzor: initial hodnota v __init__(). Viz orm_analysis.json NP1-008, NP1-012, refactoring_backlog ORM-01, BUG-004.
- **Chybějící indexy** — pas.SamostatnyNalez (projekt, katastr, pristupnost, stav); heslar.Heslar.nazev_heslare (použito v limit_choices_to napříč aplikací). Viz orm_analysis.json, BUG-005, refactoring_backlog ORM-03.
- **len(queryset.all()) místo .count()** — v Projekt.check_pred_smazanim/check_pred_navrzeni_k_zruseni. Viz orm_analysis.json NP1-003.
- **Deprecated .extra()** — arch_z/filters.py pro ST_Z(geom). Viz orm_analysis.json raw_sql_usage, refactoring_backlog ORM-06.

Kompletní přehled: orm_analysis.json n_plus_one_candidates, missing_prefetch_candidates.

---

## 6. Databázová rizika

- **Migrace** — celkem ~152 migrací; uzivatel (31), core (26), arch_z (20), dokument (19) jsou kandidáti na squash. Viz orm_analysis.json migration_summary, refactoring_backlog ORM-07.
- **Heslar.nazev_heslare** — FK bez db_index při masivním použití v limit_choices_to → table scany při formulářích. Viz BUG-005.
- **Raw SQL** — parametrizované použití v core/utils.py a arch_z/filters.py; management command transform_to_sjtsk používá raw bez parametrů (interní admin). Viz orm_analysis.json raw_sql_usage, security_analysis.json raw_sql_usage.
- **eval() na segmentech ident_cely** — projekt/models.py, arch_z/models.py; bezpečnostní a robustnostní riziko. Viz BUG-001.

---

## 7. Docker build problémy

- **Secret injection** — Grafana (GF_SECURITY_ADMIN_PASSWORD vs __FILE), Elasticsearch a Logstash (hodnota = název secretu). Viz docker_analysis.json security_issues SEC-D02, SEC-D03, BUG-007, BUG-008.
- **Produkční kontejner** — uživatel se sudo (SEC-D01); cron daemon uvnitř kontejneru (OPT-D05); libgdal-dev v runtime; redundantní COPY v multi-stage (OPT-D01). Viz docker_analysis.json.
- **Fedora Dockerfile** — více RUN apt-get update bez clean; CMD spouští dva procesy bez PID 1 managementu (OPT-D04). Viz docker_analysis.json optimization_opportunities.
- **Verze** — ELK prod 9.3.1 vs dev 8.19.0 (major gap); memcached:latest v dev (floating tag). Viz docker_analysis.json version_inconsistencies.
- **Selenium v produkčním compose** — služba by měla být pouze v docker-compose-test.yml. Viz docker_analysis.json docker_compose_services issues DCD-07.

Detail: docker_analysis.json, refactoring_backlog DOCKER-*.

---

## 8. Frontend a JavaScript rizika

- **Inline skripty v base.html** — inicializace datepickerů, checkUserAuthentication (polling 60 s), jazykový přepínač; kandidáti na extrakci do samostatných JS souborů. Viz frontend_analysis.json template_inline_scripts.extraction_candidates, refactoring_backlog FRONT-01.
- **Vlastní JS bez minifikace/bundleru** — mapa a helpery servírovány jako více souborů; větší počet requestů a velikost. Viz frontend_analysis.json build_pipeline, refactoring_backlog FRONT-02.
- **Drobné chyby** — mapa_basic_functions.js: nedefinovaná proměnná v getLocation(); ajax_functions.js: GET bez ošetření síťových chyb. Viz frontend_analysis.json custom_javascript.issues.
- **CDN/SRI** — Google Tag Manager bez SRI; u first-party nástrojů zdokumentováno jako přijatelné. Viz frontend_analysis.json cdn_sri_issues.

---

## 9. Celery a asynchronní rizika

- **Chybějící error handling** — update_all_redis_snapshots, update_single_redis_snapshot, update_materialized_views bez centrálního try/except; chyba uprostřed dávky ukončí task bez shrnutí. Viz celery_analysis.json error_handling_issues, refactoring_backlog CELERY-01.
- **call_digiarchiv_update_task** — requests.get() bez timeoutu a bez try/except; při výpadku služby může worker viset. Viz celery_analysis.json timeout_issues, refactoring_backlog CELERY-02.
- **check_hlidaci_pes** — polling (sleep 0.5 s) na vytvoření projektu v DB bez horního časového limitu; při rollbacku nebo chybné konfiguraci může běžet dlouho. Viz celery_analysis.json race_condition_candidates, timeout_issues, refactoring_backlog CELERY-03.

Beat schedule je v DB (django_celery_beat); z kódu nelze vyčíst konkrétní rozvrhy.

---

## 10. Problémy v dokumentačních generátorech

- **Read the Docs** — instaluje plné webclient/requirements.txt (včetně Selenium, debug-toolbar); prodlužuje build a zvyšuje riziko konfliktů. Viz documentation_analysis.json sphinx_docs.issues, refactoring_backlog DOCS-01.
- **docs/licenses/convert_to_rst.py** — žádná kontrola returncode subprocessu ani try/except kolem json.loads; při chybě pip-licenses nečitelný traceback. Viz documentation_analysis.json documentation_generators issues, refactoring_backlog DOCS-02.
- **Selenium docstringy** — generátor očekává sekce Steps a Expected; chybějící sekce vedou k neúplné dokumentaci bez selhání. Doporučeno: CI kontrola úplnosti. Viz documentation_analysis.json coverage_gaps, refactoring_backlog DOCS-03.

generate_module_docs.py a generate_selenium_test_docs.py nemají v analýze zaznamenané závažné problémy.

---

## 11. CI/CD mezery

- **Dependabot** — chybí .github/dependabot.yml pro sledování závislostí. Viz cicd_analysis.json security_scanning, refactoring_backlog CI-01.
- **CodeQL** — není samostatný workflow pro statickou analýzu Python kódu; pouze Trivy/SARIF z publish_images. Viz cicd_analysis.json issues.
- **Workflow timeouts** — run-tests 180 min, pre_commit 15 min, deployment 60 min — nastaveny; žádný workflow bez timeoutu.
- **Pre-commit** — instaluje plné requirements.txt; při budoucím nárůstu času může být vhodné oddělit minimální requirements pro lint. Viz cicd_analysis.json issues.

Pozitiva: Docker Scout na PR do dev; publish_images s cosign, SLSA, Trivy, SARIF upload; pre-commit včetně generování modulové a Selenium dokumentace.

---

## 12. Hlavní technický dluh (TOP 10)

| # | Položka | Zdroj | Odůvodnění |
|---|--------|-------|------------|
| 1 | DEBUG fallback "True" v production.py | BUG-010, SEC-01 | Při chybějícím secretu běží produkce s DEBUG=True — kritické bezpečnostní riziko. |
| 2 | Cirkulární závislost projekt ↔ oznameni | CIRC-01 | Nestabilní architektura, riziko ImportError při rozšíření. |
| 3 | N+1 v check_pred_uzavrenim / check_pred_odeslanim | BUG-002, ORM-02 | Desítky dotazů při každém pokusu o změnu stavu projektu/záznamu. |
| 4 | Přebujelá aplikace core (77 .py, 16+ závislých) | ARCH-01 | Globální dopad změn, obtížná údržba a testování. |
| 5 | Secret injection Grafana/Elasticsearch/Logstash | BUG-007, BUG-008, SEC-D02/D03 | Hesla nejsou z Docker secrets správně načtena. |
| 6 | sudo v produkčním Docker image | BUG-009, SEC-D01 | Eskalace oprávnění při exploitaci. |
| 7 | Chybějící db_index na Heslar.nazev_heslare | BUG-005 | Table scany při každém formuláři s limit_choices_to na hesláři. |
| 8 | Celery tasky bez error handlingu (Redis snapshots, materialized views) | CELERY-01 | Selhání uprostřed dávky bez shrnutí a bez retry. |
| 9 | Deploy a restore skripty bez set -e a validace env | T10-SH-01, T10-SH-03, BUG-013 | Selhání příkazu může být přehlédnuto; restore_database.sh riskantní bez kontroly DBNAME. |
| 10 | Extra SELECT v save() u ArcheologickyZaznam a SamostatnyNalez | ORM-01, BUG-004 | Zbytečné dotazy při každém uložení záznamu. |

---

## 13. Prioritizovaný plán refaktoringu

**První vlna (bezpečnost a kritický provoz)**

- Opravit DEBUG fallback na "False" v production.py (S).
- Opravit secret injection pro Grafana (GF_*__FILE), Elasticsearch a Logstash (entrypoint wrapper) (S).
- Odebrat sudo z produkčního uživatele v Dockerfile (S).
- Přidat Django security headers a zařadit `manage.py check --deploy` do CI (S).
- restore_database.sh: set -e a validace DBNAME, USED_DB_BACKUP, DB_FLAG_ROLE (S).

**Druhá vlna (architektura a ORM)**

- Rozhodnout o rozbití cirkulární závislosti projekt ↔ oznameni (sloučit nebo extrahovat do core) (L).
- Prefetch v místech volání check_pred_uzavrenim/check_pred_odeslanim; případně refaktor check metod na přijímání prefetchovaných dat (M).
- Doplnit initial_pristupnost v __init__() a odstranit extra SELECT v save() u ArcheologickyZaznam a SamostatnyNalez (S).
- Přidat db_index na Heslar.nazev_heslare a na pas.SamostatnyNalez (projekt, katastr, pristupnost, stav) (S).

**Třetí vlna (Celery, skripty, CI)**

- Error handling a shrnutí v update_all_redis_snapshots, update_materialized_views, update_single_redis_snapshot (S).
- Timeout a try/except pro call_digiarchiv_update_task; omezení pollingu v check_hlidaci_pes (S/M).
- set -e v deploy a maintenance skriptech; common.sh pro sdílené funkce (S/M).
- db_connection_from_docker-web.py: čtení DB_PORT ze secretu (S). Viz BUG-014.
- Dependabot + volitelně CodeQL pro Python (S).

**Čtvrtá vlna (dlouhodobé)**

- Dekompozice core na menší moduly (XL).
- Rozdělení xml_generator na amcr_base a generátor; odstranění CIRC-02 (M).
- Squash migrací u uzivatel, core, arch_z, dokument (M).
- Oddělení requirements (prod / dev / test / docs); DOCS requirements pro Read the Docs (S).
- Extrakce inline skriptů z base.html; zvážení bundleru pro vlastní JS (S/M).

Podrobnosti a náročnost: refactoring_backlog.md (Vysoká / Střední / Nízká priorita).

---

## 14. Doporučení pro dlouhodobou správu repozitáře

- **Governance** — Pravidla v AGENTS.md a CONTRIBUTING.md ponechat jako zdroj pravdy; při rozporu s .agents/ upravit .agents/ a zaznamenat v review_cache nebo refactoring_backlog. Viz AGENTS.md.
- **Review cyklus** — Před každou session načíst review_cache.json a file hashes; označit změněné soubory a příslušné tasky jako pending; neopakovat dokončené tasky bez změny vstupů. Viz review_codebase.md INITIALIZATION SEQUENCE.
- **Konfigurace** — Jediný zdroj limitů a adresářů: review_config.yaml. Vendored exclusions a task registry nemultiplikovat jinde. Viz review_config.yaml.
- **Bug a backlog** — Před přidáním záznamu do bugs.md ověřit GitHub Issues (aktuálně 113 otevřených); křížově odkazovat „již evidováno / rozšíření / nový kandidát“. Refactoring backlog udržovat v češtině a třídit dle priority (Vysoká / Střední / Nízká). Viz review_codebase.md BUG TRACKING a REFACTORING BACKLOG.
- **Prompt evolution** — Návrhy z reportů ukládat do .agents/prompts/prompt_evolution/<task_id>_prompt_update.md; aplikaci změn do review_codebase.md provádět ručně. Viz review_codebase.md PROMPT EVOLUTION.
- **Dokumentace a CI** — Generovanou dokumentaci neupravovat ručně; spouštět generátory dle CONTRIBUTING.md. V CI zvážit kontrolu úplnosti Selenium docstringů a `manage.py check --deploy`; CVE krok (pip audit/safety) pro závislosti.
- **Struktura .agents/** — Zachovat podle .agents/README.md: config (review_config.yaml, review_cache.json), analysis (*.json), reports (review_reports/, bugs.md, refactoring_backlog.md), prompts a prompt_evolution.

---

*Finální audit vznikl syntézou výstupů úloh T01–T10. Pro detailní evidence viz uvedené JSON soubory v .agents/analysis/, reporty T01.md–T10.md a .agents/reports/bugs.md a refactoring_backlog.md.*
