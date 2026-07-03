# Final Audit - AMCR (aiscr-webamcr)

**Datum:** 2026-03-13  
**Účel:** Syntéza výsledků úloh T01–T10 technického review repozitáře.  
**Zdrojové artefakty:** `.agents/analysis/*.json`, `.agents/reports/review_reports/T01.md`–`T10.md` (vč. T03c, T03d, T07b), `bugs.md`, `refactoring_backlog.md`.

---

## 1. Major Architectural Issues

- **Přebujelá aplikace `core`** — 78 Python souborů, 26 migrací, importována 16+ aplikacemi. Sdružuje middleware, permissions, constants, signals, logging, konektory (Fedora, Redis), koordinátové transformace a management commands. Jakákoli změna má globální dopad. Viz refactoring_backlog ARCH-01.
- **Aplikace `dokument`** — nejvyšší fan-out (8 cross-app importů), 10 modelů (vč. 5 M2M through tabulek), 18 migrací. Obsahuje eval() na datech z DB (SEC-ORM-004). Viz refactoring_backlog ARCH-02.
- **Dualita `xml_generator`** — slouží jako knihovna base modelů (BaseAmcrModel, ModelWithMetadata) i jako generátor XML; importována 10 aplikacemi a zároveň v cirkulární závislosti s `adb`. `record_ident_change` obsahuje 7 isinstance větví pro kaskádové metadata uložení — architektonicky kritický kód. Viz ARCH-03, CIRC-02.
- **`historie.HistorieVazby`** — architektonicky kritický model; používán jako OneToOne FK z Projekt, Dokument, ArcheologickyZaznam, SamostatnyNalez, Pian, ExterniZdroj, User. Centrální audit log s 42 typy změn.
- **Aplikace bez testů** — `cron`, `notifikace_projekty`, `fedora_management`, `healthcheck`, `neidentakce`, `services`, `vypis`, `xml_generator`. U `cron` a `notifikace_projekty` jde o Celery tasky bez testovací sítě. Viz repository_map.json, refactoring_backlog ARCH-04.

---

## 2. Security Risks (Prioritized)

**High Priority**

- **DEBUG fallback v produkci** — `get_secret("DEBUG", "True")` v `production.py` znamená, že při chybějícím klíči běží aplikace s DEBUG=True. Viz BUG-010, security_analysis.json SEC-01.

**Medium Priority**

- **Grafana / Elasticsearch / Logstash** — nesprávná injekce hesel: `GF_SECURITY_ADMIN_PASSWORD` nastaveno na cestu k souboru místo hodnoty; ELASTIC_PASSWORD a LOGSTASH_INTERNAL_PASSWORD na název secretu. Viz BUG-007, BUG-008, docker_analysis.json SEC-D02, SEC-D03.
- **sudo v produkčním kontejneru** — `usermod -aG sudo user` v Dockerfile. Viz BUG-009, SEC-D01.
- **Chybějící Django security headers** — SECURE_HSTS_SECONDS, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, SECURE_CONTENT_TYPE_NOSNIFF nejsou v production.py. Viz security_analysis.json SEC-03.
- **mark_safe() s hodnotami z DB** — ve `vypis/fields.py` a `vypis/views.py` na hodnotách z modelů; potenciální XSS. Viz BUG-012, security_analysis.json XSS-02 až XSS-04.
- **Mailtrap credentials v commitu** — sample_secrets_mail_client.json obsahuje zdánlivě reálné přihlašovací údaje. Viz BUG-011, SEC-02.
- **eval() v generátorech identifikátorů** — 5 míst v projekt/models.py, arch_z/models.py, dokument/models.py a ez/models.py používá `eval(i)` na hodnotách z DB. Viz BUG-001, orm_analysis.json SEC-ORM-001–SEC-ORM-005.

**Low / Recommendations**

- CVE audit závislostí nebyl proveden (offline prostředí). Doporučeno: `pip audit` nebo `safety check` v CI. Viz security_analysis.json known_vulnerabilities, refactoring_backlog SEC-04.

---

## 3. Circular and Problematic Dependencies

- **projekt ↔ oznameni** (High) — vzájemné importy na úrovni modulů: oznameni/models importuje Projekt; projekt/forms, views, urls importují z oznameni. Riziko ImportError při rozšíření. Viz dependency_graph.json CIRC-01, refactoring_backlog CIRC-01.
- **adb ↔ xml_generator** (Medium) — adb.models importuje BaseAmcrModel z xml_generator.models; xml_generator.generator importuje VyskovyBod z adb.models na úrovni modulu. Viz dependency_graph.json CIRC-02, refactoring_backlog CIRC-02.

---

## 4. High-Complexity Modules

- **core** — fan-in 16, 78 .py souborů, největší počet zodpovědností (middleware, permissions, signals, logging, konektory, ident_cely, management commands). Doporučeno dekomponovat na core.permissions, core.logging, core.middleware, core.signals.
- **heslar** — fan-in 16; centrální číselníky, vazba přirozená, ale Critical pro výkon (viz chybějící index na nazev_heslare — BUG-005).
- **xml_generator** — fan-in 10; kombinace base modelů a generátoru XML.
- **uzivatel** — fan-in 11.
- **dokument** — fan-out 8.

Viz dependency_graph.json tightly_coupled_modules a architectural_issues.

---

## 5. ORM Performance Issues

- **N+1 v check_pred_* metodách** — `Projekt.check_pred_uzavrenim()` a `ArcheologickyZaznam.check_pred_odeslanim()` iterují přes akce/DJ bez prefetch; kaskádové dotazy. Viz BUG-002, orm_analysis.json NP1-002, NP1-006, refactoring_backlog ORM-02.
- **Extra SELECT v save()** — ArcheologickyZaznam a SamostatnyNalez při každém save() (pk != None) volají `Model.objects.get(pk=self.pk)` pro zjištění změny pristupnost. Správný vzor: initial hodnota v __init__(). Viz orm_analysis.json NP1-008, NP1-012, refactoring_backlog ORM-01, BUG-004.
- **Chybějící indexy** — pas.SamostatnyNalez (projekt, katastr, pristupnost, stav); heslar.Heslar.nazev_heslare (použito v limit_choices_to napříč aplikací). Viz orm_analysis.json, BUG-005, refactoring_backlog ORM-03.
- **len(queryset.all()) místo .count()** — v Projekt.check_pred_smazanim/check_pred_navrzeni_k_zruseni. Viz orm_analysis.json NP1-003.
- **Deprecated .extra()** — arch_z/filters.py pro ST_Z(geom). Viz orm_analysis.json raw_sql_usage, refactoring_backlog ORM-06.

Další N+1 a ORM kandidáti (Low až Medium závažnost): NP1-001 (check_pred_archivaci), NP1-004 (set_pristupnost), NP1-005 (datum_oznameni property), NP1-007 (_set_connected_records_ident bulk_update), NP1-009 (User.save), NP1-010 (moje_spolupracujici_organizace), NP1-011 (Pian.pristupnost_pom), NP1-013 (Pian.get_create_org triple-hop), NP1-014 (ModelWithMetadata.record_deletion), NP1-015 (Dokument.check_pred_odeslanim — iterace DJ bez prefetch), NP1-016 (ExterniZdroj.check_pred_odeslanim — iterace vazeb), NP1-017 (ExterniZdrojSekvence.save — extra SELECT na get(pk=pk) pro pristupnost), NP1-018 (Komponenta.check_pred_odeslanim — 3 poddotazy na nálezy), NP1-019 (KomponentaVazby — kaskádové FK bez select_related), NP1-020 (Lokalita.set_snapshots — filter+iterate vzorec). Kompletní přehled: orm_analysis.json n_plus_one_candidates, missing_prefetch_candidates.

**Chybné přetížení metod:**

- **BUG-015: NalezPredmet.__init_ typo** — `__init_` místo `__init__` (chybí jedno podtržítko) v nalez/models.py:116. Custom inicializace se nikdy nespustí; proměnné `initial_druh` atd. zůstanou nedefinované. Viz bugs.md BUG-015.

---

## 6. Database Risks

- **Migrace** — celkem ~213 migrací; uzivatel (31), core (26), arch_z (20), dokument (19), heslar (17), historie (16) jsou kandidáti na squash. Viz orm_analysis.json migration_summary, refactoring_backlog ORM-07.
- **Heslar.nazev_heslare** — FK bez db_index při masivním použití v limit_choices_to → table scany při formulářích. Viz BUG-005.
- **Raw SQL** — parametrizované použití v core/utils.py a arch_z/filters.py; management command transform_to_sjtsk používá raw bez parametrů (interní admin). Viz orm_analysis.json raw_sql_usage, security_analysis.json raw_sql_usage.
- **eval() na segmentech ident_cely** — projekt/models.py, arch_z/models.py, dokument/models.py, ez/models.py (celkem 5 míst); bezpečnostní a robustnostní riziko. Viz BUG-001, SEC-ORM-001–SEC-ORM-005.

---

## 7. Docker Build Issues

- **Secret injection** — Grafana (GF_SECURITY_ADMIN_PASSWORD vs __FILE), Elasticsearch a Logstash (hodnota = název secretu). Viz docker_analysis.json security_issues SEC-D02, SEC-D03, BUG-007, BUG-008.
- **Produkční kontejner** — uživatel se sudo (SEC-D01); cron daemon uvnitř kontejneru (OPT-D05); libgdal-dev v runtime; redundantní COPY v multi-stage (OPT-D01). Viz docker_analysis.json.
- **Fedora Dockerfile** — více RUN apt-get update bez clean; CMD spouští dva procesy bez PID 1 managementu (OPT-D04). Viz docker_analysis.json optimization_opportunities.
- **Verze** — ELK prod 9.3.1 vs dev 8.19.0 (major gap); memcached:latest v dev (floating tag). Viz docker_analysis.json version_inconsistencies.
- **Selenium v produkčním compose** — služba by měla být pouze v docker-compose-test.yml. Viz docker_analysis.json docker_compose_services issues DCD-07.

Další Docker compose problémy: DCD-01 (logstash bez depends_on), DCD-02 (celery -l DEBUG v produkci), DCD-06 (monitoring exponován bez izolace), DCD-08 až DCD-13 (xpack nekonzistence, floating tags, hardcoded hesla). Optimalizace: OPT-D02 (compileall duplicita), OPT-D03 (3× apt-get update). Kompletní detail: docker_analysis.json, refactoring_backlog DOCKER-*.

---

## 8. Frontend and JavaScript Risks

- **Inline skripty v base.html** — inicializace datepickerů, checkUserAuthentication (polling 60 s), jazykový přepínač; kandidáti na extrakci do samostatných JS souborů. Viz frontend_analysis.json template_inline_scripts.extraction_candidates, refactoring_backlog FRONT-01.
- **Vlastní JS bez minifikace/bundleru** — mapa a helpery servírovány jako více souborů; větší počet requestů a velikost. Celkem 24 custom JS souborů (~5 600 řádků) analyzováno. Viz frontend_analysis.json build_pipeline, refactoring_backlog FRONT-02.
- **Mapové skripty — crash při prázdných vrstvách** (High) — `poi_sugest.getLayers()[0]._latlng` v mapa_arch_z.js, mapa_pas.js, mapa_projekty.js a dalších: crash pokud vrstva nemá geometrii. Přístup `coordinates[0][0]` bez kontroly délky pole. Viz frontend_analysis.json custom_javascript.issues.
- **XHR bez onerror** (High) — žádný z mapových skriptů (mapa_arch_z.js, mapa_pas.js, mapa_projekty.js, mapa_doc.js, mapa_oznameni.js) nemá `xhr.onerror` handler; síťová chyba je tiše ignorována. Viz refactoring_backlog FRONT-03.
- **JSON.parse bez try/catch** (Medium) — mapa_arch_z.js, mapa_pas.js, dz.js, mapa_oznameni.js parsují serverové odpovědi bez ochrany; poškozená odpověď rozbije celý skript. Viz refactoring_backlog FRONT-04.
- **BUG-016: Invertovaná podmínka** (Medium) — form_fields_disabling.js řádek 64: `||` místo `&&`; podmínka pro disable formulářových polí je vždy pravdivá. Viz bugs.md BUG-016.
- **BUG-017: Chybná přesnost souřadnic** (Medium) — coor_precision.js řádek 31: JTSK přesnost používá konstantu pro WGS84 (6 des. míst místo 2). Viz bugs.md BUG-017.
- **dz.js — Leaflet API nesoulad** (High) — volání `clearLayers()` na `L.geoJSON` objekt, ale správná metoda je na FeatureGroup/LayerGroup. `addData()` po `clearLayers()` může nefungovat dle očekávání.
- **Implicitní globální proměnné** — map_functions, mapa_pins.js a většina mapových skriptů deklarují proměnné bez `var`/`let`/`const`; hrozí konflikty jmen při společném načtení. Viz refactoring_backlog FRONT-06.
- **Duplicitní pin-factory vzor** — mapa_pins.js opakuje ~30 řádkový blok pro každou kategorii pinů; kandidát na generické řešení tovární funkcí. Viz refactoring_backlog FRONT-05.
- **Drobné chyby** — mapa_basic_functions.js: nedefinovaná proměnná v getLocation(); ajax_functions.js: GET bez ošetření síťových chyb. Viz frontend_analysis.json custom_javascript.issues.
- **CDN/SRI** — Google Tag Manager bez SRI; u first-party nástrojů zdokumentováno jako přijatelné. Viz frontend_analysis.json cdn_sri_issues.

---

## 9. Celery and Asynchronous Risks

- **Chybějící error handling** — update_all_redis_snapshots, update_single_redis_snapshot, update_materialized_views bez centrálního try/except; chyba uprostřed dávky ukončí task bez shrnutí. Viz celery_analysis.json error_handling_issues, refactoring_backlog CELERY-01.
- **call_digiarchiv_update_task** — requests.get() bez timeoutu a bez try/except; při výpadku služby může worker viset. Viz celery_analysis.json timeout_issues, refactoring_backlog CELERY-02.
- **check_hlidaci_pes** — polling (sleep 0.5 s) na vytvoření projektu v DB bez horního časového limitu; při rollbacku nebo chybné konfiguraci může běžet dlouho. Viz celery_analysis.json race_condition_candidates, timeout_issues, refactoring_backlog CELERY-03.

Beat schedule je v DB (django_celery_beat); z kódu nelze vyčíst konkrétní rozvrhy.

---

## 10. Documentation Generator Issues

- **Read the Docs** — instaluje plné webclient/requirements.txt (včetně Selenium, debug-toolbar); prodlužuje build a zvyšuje riziko konfliktů. Viz documentation_analysis.json sphinx_docs.issues, refactoring_backlog DOCS-01.
- **docs/licenses/convert_to_rst.py** — žádná kontrola returncode subprocessu ani try/except kolem json.loads; při chybě pip-licenses nečitelný traceback. Viz documentation_analysis.json documentation_generators issues, refactoring_backlog DOCS-02.
- **Selenium docstringy** — generátor očekává sekce Steps a Expected; chybějící sekce vedou k neúplné dokumentaci bez selhání. Doporučeno: CI kontrola úplnosti. Viz documentation_analysis.json coverage_gaps, refactoring_backlog DOCS-03.

generate_module_docs.py a generate_selenium_test_docs.py nemají v analýze zaznamenané závažné problémy.

---

## 11. CI/CD Gaps

- **Dependabot** — chybí .github/dependabot.yml pro sledování závislostí. Viz cicd_analysis.json security_scanning, refactoring_backlog CI-01.
- **CodeQL** — není samostatný workflow pro statickou analýzu Python kódu; pouze Trivy/SARIF z publish_images. Viz cicd_analysis.json issues.
- **Workflow timeouts** — run-tests 180 min, pre_commit 15 min, deployment 60 min — nastaveny; žádný workflow bez timeoutu.
- **Pre-commit** — instaluje plné requirements.txt; při budoucím nárůstu času může být vhodné oddělit minimální requirements pro lint. Viz cicd_analysis.json issues.

Pozitiva: Docker Scout na PR do dev; publish_images s cosign, SLSA, Trivy, SARIF upload; pre-commit včetně generování modulové a Selenium dokumentace.

---

## 12. Major Technical Debt (Top 10)

| # | Položka | Zdroj | Odůvodnění |
|---|--------|-------|------------|
| 1 | DEBUG fallback "True" v production.py | BUG-010, SEC-01 | Při chybějícím secretu běží produkce s DEBUG=True — kritické bezpečnostní riziko. |
| 2 | eval() na datech z DB v generátorech identifikátorů (5 míst) | BUG-001, SEC-ORM-001–005 | Arbitrary code execution; rozšířeno ze 3 na 5 míst (+ dokument, ez). |
| 3 | Cirkulární závislost projekt ↔ oznameni | CIRC-01 | Nestabilní architektura, riziko ImportError při rozšíření. |
| 4 | N+1 v check_pred_* metodách (20 kandidátů) | BUG-002, ORM-02, NP1-* | Desítky dotazů při každém pokusu o změnu stavu; rozšířeno z 14 na 20 kandidátů. |
| 5 | Přebujelá aplikace core (78 .py, 16+ závislých) | ARCH-01 | Globální dopad změn, obtížná údržba a testování. |
| 6 | Secret injection Grafana/Elasticsearch/Logstash | BUG-007, BUG-008, SEC-D02/D03 | Hesla nejsou z Docker secrets správně načtena. |
| 7 | sudo v produkčním Docker image | BUG-009, SEC-D01 | Eskalace oprávnění při exploitaci. |
| 8 | Chybějící db_index na Heslar.nazev_heslare | BUG-005 | Table scany při každém formuláři s limit_choices_to na hesláři. |
| 9 | Mapové skripty — crash + chybějící error handling | BUG-016, BUG-017, FRONT-03–06 | 7 vysokých issues; XHR bez onerror, crash na prázdných vrstvách, JSON.parse bez ochrany. |
| 10 | Celery tasky bez error handlingu (Redis snapshots, materialized views) | CELERY-01 | Selhání uprostřed dávky bez shrnutí a bez retry. |

---

## 13. Prioritized Refactoring Plan

**První vlna (bezpečnost a kritický provoz)**

- Opravit DEBUG fallback na "False" v production.py (S).
- Opravit secret injection pro Grafana (GF_*__FILE), Elasticsearch a Logstash (entrypoint wrapper) (S).
- Nahradit eval() v generátorech identifikátorů bezpečným parsováním (5 míst: projekt, arch_z, dokument, ez) (S). Viz BUG-001.
- Odebrat sudo z produkčního uživatele v Dockerfile (S).
- Přidat Django security headers a zařadit `manage.py check --deploy` do CI (S).
- restore_database.sh: set -e a validace DBNAME, USED_DB_BACKUP, DB_FLAG_ROLE (S).

**Druhá vlna (architektura a ORM)**

- Rozhodnout o rozbití cirkulární závislosti projekt ↔ oznameni (sloučit nebo extrahovat do core) (L).
- Prefetch v místech volání check_pred_uzavrenim/check_pred_odeslanim; případně refaktor check metod na přijímání prefetchovaných dat (M). Nově zahrnuje i Dokument.check_pred_odeslanim (NP1-015), ExterniZdroj.check_pred_odeslanim (NP1-016), Komponenta.check_pred_odeslanim (NP1-018).
- Doplnit initial_pristupnost v __init__() a odstranit extra SELECT v save() u ArcheologickyZaznam, SamostatnyNalez a ExterniZdrojSekvence (S). Viz NP1-017.
- Opravit NalezPredmet.__init_ typo (chybí podtržítko) — custom inicializace se nespustí (S). Viz BUG-015.
- Přidat db_index na Heslar.nazev_heslare a na pas.SamostatnyNalez (projekt, katastr, pristupnost, stav) (S).

**Třetí vlna (Celery, skripty, frontend, CI)**

- Error handling a shrnutí v update_all_redis_snapshots, update_materialized_views, update_single_redis_snapshot (S).
- Timeout a try/except pro call_digiarchiv_update_task; omezení pollingu v check_hlidaci_pes (S/M).
- set -e v deploy a maintenance skriptech; common.sh pro sdílené funkce (S/M).
- db_connection_from_docker-web.py: čtení DB_PORT ze secretu (S). Viz BUG-014.
- Dependabot + volitelně CodeQL pro Python (S).
- Přidat XHR onerror handlery do mapových skriptů (S). Viz FRONT-03.
- Přidat try/catch kolem JSON.parse v mapových skriptech a dz.js (S). Viz FRONT-04.
- Opravit invertovanou podmínku v form_fields_disabling.js (S). Viz BUG-016.
- Opravit přesnostní konstantu JTSK v coor_precision.js (S). Viz BUG-017.

**Čtvrtá vlna (dlouhodobé)**

- Dekompozice core na menší moduly (XL).
- Rozdělení xml_generator na amcr_base a generátor; odstranění CIRC-02 (M).
- Squash migrací u uzivatel, core, arch_z, dokument, heslar, historie (M). Nově 213 migrací (rozšířen scope).
- Oddělení requirements (prod / dev / test / docs); DOCS requirements pro Read the Docs (S).
- Extrakce inline skriptů z base.html; zvážení bundleru pro vlastní JS (S/M).
- Refaktor mapa_pins.js — tovární funkce místo opakovaného bloku (S). Viz FRONT-05.
- Eliminace implicitních globálních proměnných v mapových skriptech (M). Viz FRONT-06.

Podrobnosti a náročnost: refactoring_backlog.md (High / Medium / Low priorita).

---

## 14. Long-Term Repository Maintenance Recommendations

- **Governance** — Pravidla v AGENTS.md a CONTRIBUTING.md ponechat jako zdroj pravdy; při rozporu s .agents/ upravit .agents/ a zaznamenat v review_cache nebo refactoring_backlog. Viz AGENTS.md.
- **Review cyklus** — Před každou session načíst review_cache.json a file hashes; označit změněné soubory a příslušné tasky jako pending; neopakovat dokončené tasky bez změny vstupů. Viz review_codebase.md INITIALIZATION SEQUENCE.
- **Konfigurace** — Jediný zdroj limitů a adresářů: review_config.yaml. Vendored exclusions a task registry nemultiplikovat jinde. Viz review_config.yaml.
- **Bug a backlog** — Před přidáním záznamu do bugs.md ověřit GitHub Issues (aktuálně 113 otevřených); křížově odkazovat „již evidováno / rozšíření / nový kandidát“. Refactoring backlog udržovat v češtině a třídit dle priority (High / Medium / Low). Viz review_codebase.md BUG TRACKING a REFACTORING BACKLOG.
- **Evidence workflow-evolution** — Starší poznámky prompt-evolution jsou zachovány v .agents/reports/workflow_evolution_legacy_evidence.md; nová zpětná vazba z U05 vyžaduje výslovné schválení předání report-to-backlog.
- **Dokumentace a CI** — Generovanou dokumentaci neupravovat ručně; spouštět generátory dle CONTRIBUTING.md. V CI zvážit kontrolu úplnosti Selenium docstringů a `manage.py check --deploy`; CVE krok (pip audit/safety) pro závislosti.
- **Struktura .agents/** — Zachovat podle .agents/README.md: config (review_config.yaml, review_cache.json), analysis (*.json), reports (review_reports/, bugs.md, refactoring_backlog.md, workflow_evolution_legacy_evidence.md) a prompts.

---

*Finální audit vznikl syntézou výstupů úloh T01–T10 (vč. sub-tasků T03c, T03d, T07b). Pro detailní evidence viz uvedené JSON soubory v .agents/analysis/, reporty T01.md–T10.md (vč. T03c.md, T03d.md, T07b.md), .agents/reports/bugs.md (17 bugů) a refactoring_backlog.md.*

---

## Changelog

### 2026-03-13 — Křížová validace a inkrementální aktualizace

**Zdroj:** Křížová validace (U03) + inkrementální aktualizace (U01–U06).

**Detekce změn:** 43 z 61 sledovaných souborů změněno (T01: 18, T02: 7, T04: 10, T05: 8). Žádné soubory smazány ani nově přidány.

**Opravené nekonzistence:**

- ARCH-04: prefix opraven `[T02]` → `[T01]` v refactoring_backlog.md (zdroj nálezu je T01, ne T02).
- BUG-004: závažnost zvýšena z Low na Medium v bugs.md (sjednocení s ORM-01 backlog prioritou — extra SELECT v save() je architektonický anti-pattern).
- BUG-005 / ORM-03: ponecháno Medium — rozdíl oproti backlogu (High priorita) je záměrný a zdokumentován (priorita refaktoringu ≠ závažnost bugu).

**Mezery v pokrytí:**

- **T03 (ORM):** ✅ VYŘEŠENO (T03c/T03d, 2026-03-13). Všech 10 chybějících Django aplikací (28 modelů, ~2 793 řádků) bylo analyzováno a přidáno do `orm_analysis.json`. Nové nálezy: SEC-ORM-004, SEC-ORM-005 (2 další eval() výskyty v dokument/ez — rozšiřuje BUG-001 ze 3 na 5 míst), NP1-015 až NP1-020 (6 nových N+1 kandidátů), BUG-015 (typo `__init_` v nalez/NalezPredmet).
- **T07 (Frontend):** ✅ VYŘEŠENO (T07b, 2026-03-13). Vendored exclusions aktualizovány (timer.js, datepicker-cs.js). 20 vlastních JS souborů (~3 846 řádků) analyzováno a přidáno do `frontend_analysis.json`. Nové nálezy: BUG-016 (invertovaná podmínka form_fields_disabling.js), BUG-017 (chybná přesnost coor_precision.js), 4 backlog položky (FRONT-03 až FRONT-06). High závažnost u 7 issues v mapových skriptech a dz.js.

**Ověření bugů:** Všech 14 původních bugů (BUG-001 až BUG-014) potvrzeno jako stále přítomné (spot-check 7 z nich, žádný opraven). Přibyly 3 nové bugy: BUG-015, BUG-016, BUG-017.

**Architektonické nálezy ověřeny:** CIRC-01, CIRC-02, ARCH-01 potvrzeny; `core` narostl na 78 .py souborů (ze 77).

**ID doplněná do finálního auditu:** SEC-ORM-001/002/003 (§2), NP1-001/004/005/007/009/010/011/013/014 (§5), DCD-01/02/06/08–13, OPT-D02/D03 (§7), SCRIPTS-01/SCRIPTS-03 (§12 TOP 10 #9).

**Prompt evolution:** 42/42 návrhů začleněno do review_codebase.md (zbývající 2 — tabulka doménových entit a core warning — doplněny v rámci této aktualizace).

### 2026-03-13 — Uzavření coverage gaps (T03c/T03d + T07b)

**Zdroj:** Cílená analýza pro uzavření mezer v pokrytí identifikovaných v předchozím changelogu.

**Detekce změn:** 0 sledovaných souborů v repozitáři změněno. Změny pouze v `.agents/` artefaktech.

**Opravené nekonzistence:**
- BUG-001: rozšířen ze 3 na 5 výskytů eval() (přidány dokument/models.py:441 a ez/models.py:301).

**Mezery v pokrytí:**
- **T03 (ORM):** ✅ UZAVŘENO. T03c analyzoval 4 kritické aplikace (dokument — 10 modelů, historie — 2 modely, ez — 4 modely, xml_generator — 2 abstraktní modely). T03d analyzoval 6 menších aplikací (komponenta — 3, lokalita — 1, nalez — 2, dj — 1, neidentakce — 2, notifikace_projekty — 1). Celkem přidáno 26 nových model entries do orm_analysis.json.
- **T07 (Frontend):** ✅ UZAVŘENO. Vendored exclusions aktualizovány (+2: timer.js, datepicker-cs.js). 20 custom JS souborů analyzováno a přidáno do frontend_analysis.json (celkem 24 souborů pokryto).
- **T10:** ✅ UZAVŘENO. Konfigurační soubory (crontab.txt, uwsgi_site.ini) zdokumentovány v `scripts_analysis.json` → `config_notes`; sledovány v `review_cache.json` s `task_id: T10`.

**Ověření bugů:** Všech 17 bugů (BUG-001 až BUG-017) potvrzeno jako přítomné. Spot-check: BUG-015 (nalez/models.py:116 `__init_`), BUG-016 (form_fields_disabling.js:64 `||` místo `&&`), BUG-017 (coor_precision.js:31 `wgs84` místo `jtsk`), SEC-ORM-004 (dokument/models.py:441 `eval(i)`), SEC-ORM-005 (ez/models.py:301 `eval(i)`) — vše ověřeno přímým čtením souborů.

**Nové nálezy:**
- BUG-015: `__init_` typo v nalez/NalezPredmet — custom init se nespustí (Medium)
- BUG-016: invertovaná podmínka `||` místo `&&` v form_fields_disabling.js (Medium)
- BUG-017: chybná přesnost JTSK používá WGS84 konstantu v coor_precision.js (Medium)
- SEC-ORM-004, SEC-ORM-005: 2 nové výskyty eval() na datech z DB (Medium)
- NP1-015 až NP1-020: 6 nových N+1 kandidátů v dokument, ez, lokalita
- FRONT-03 až FRONT-06: 4 nové backlog položky (XHR onerror, JSON.parse try/catch, pin factory, implicitní globály)

**Prompt evolution:** 57/57 návrhů začleněno. Zbývajících 6 (T01 scope, T05 credentials, T09 CI, T10 scripty) doplněno — viz changelog „Doplnění prompt evolution".

**Křížová validace:** review_tools.py all: 0 errors, 0 nových warnings. lint-artifacts: 0 chyb. id-inventory: SEC-ORM-005 nyní referencován ve final_audit.

### 2026-03-13 — Aktualizace těla auditu (§1–§14)

Předchozí dva changelogy aktualizovaly pouze sekci Changelog a řádky 215-219 (coverage gaps). Tato aktualizace promítá nálezy T03c/T03d/T07b do všech relevantních sekcí hlavního těla auditu:

- **§1:** core 77→78 .py; dokument rozšířen o model count + SEC-ORM-004; xml_generator doplněn o record_ident_change; nový bod: historie.HistorieVazby jako architektonicky kritický model.
- **§2:** eval() rozšířen ze 3 na 5 míst (+ dokument, ez); SEC-ORM-001–005.
- **§4:** core 78 .py (opraven count).
- **§5:** Přidáno NP1-015 až NP1-020 do seznamu dalších kandidátů; nový pododdíl „Chybné přetížení metod" s BUG-015.
- **§6:** Migrace ~152→~213; eval() rozšířen na 5 míst; heslar a historie přidány jako squash kandidáti.
- **§8:** Kompletně přepracováno — přidáno 9 nových bodů (crash na prázdných vrstvách, XHR bez onerror, JSON.parse, BUG-016, BUG-017, Leaflet API nesoulad, implicitní globály, pin-factory duplikace); celkový souhrn analyzovaných souborů 24 (~5 600 řádků).
- **§12 (TOP 10):** Přeuspořádáno — eval() povýšen na #2, N+1 rozšířen na 20 kandidátů (#4), mapové skripty vstupují na #9; deploy skripty a extra SELECT vypadly z TOP 10.
- **§13:** eval() fix přidán do první vlny; druhá vlna rozšířena o NP1-015/016/017/018 a BUG-015; třetí vlna rozšířena o FRONT-03/04 a BUG-016/017; čtvrtá vlna rozšířena o FRONT-05/06 a squash scope.
- **Závěrečný odstavec:** Aktualizován na 17 bugů a explicitní odkaz na T03c/T03d/T07b reporty.

### 2026-03-13 — Doplnění prompt evolution a uzavření T10

**Prompt evolution:** Zbývajících 6 návrhů z T01/T03c/T03d/T05/T07b/T09 začleněno do `review_codebase.md`. Celkový stav: 57/57 návrhů začleněno.

Konkrétní změny v `review_codebase.md`:
- **T01 scope:** `pyproject.toml` doplněn o poznámku, že v repozitáři neexistuje (T02 section, line „external libraries"). `webclient/locale` odstraněn z `review_config.yaml` → `important_directories` (adresář neexistuje).
- **T03 (ORM):** Přidána detekce `eval()` vzorů ve všech generátorech identifikátorů (nejen projekt/arch_z). Přidána kontrola `__init__` překlepů (chybějící podtržítko).
- **T05 (Security):** Přidán požadavek na zjištění verze Django frameworku z `requirements.txt` a citaci verze-specifických security defaults.
- **T07 (Frontend):** Přidána kontrola správnosti Leaflet API (clearLayers, addData na správném typu vrstvy). Přidána detekce De Morgan chyb v logických operátorech (`||` vs `&&`). Přidána poznámka o vendored souborech bez `/*!` hlavičky ale s `/**` JSDoc hlavičkou.
- **T09 (CI/CD):** Přidán požadavek na shrnutí supply-chain security capabilities (signing, SBOM, SARIF, provenance) v `security_scanning` sekci.

**T10:** Přehodnocen na ✅ UZAVŘENO — konfigurační soubory (crontab.txt, uwsgi_site.ini) jsou již zdokumentovány v `scripts_analysis.json` → `config_notes` a sledovány v `review_cache.json`.
