# Refactoring backlog — AMČR (aiscr-webamcr)

> Všechny záznamy jsou psány v češtině.
> Strukturální zlepšení objevená během auditu.
>
> **Poznámka k prioritě vs. závažnosti:** Sekce priorit (Vysoká / Střední / Nízká)
> odrážejí **prioritu refaktoringu** (dopad na architekturu a business logiku).
> Tato klasifikace se může lišit od **závažnosti bugu** v `bugs.md`, která odráží
> technické riziko samotného defektu. Pokud položka křížově odkazuje na BUG-XXX,
> oba údaje jsou záměrné — priorita refaktoringu a závažnost bugu mají odlišný
> hodnoticí rámec.

---

## Vysoká priorita

<!-- Architektonické problémy, bezpečnostní dluhy, ORM výkon -->

### [T02] CIRC-01: Cirkulární závislost projekt ↔ oznameni
- **Soubory:** `webclient/oznameni/models.py`, `webclient/projekt/forms.py`, `webclient/projekt/views.py`, `webclient/projekt/urls.py`
- **Popis:** Vzájemné importy na úrovni modulů mezi projekt a oznameni. Nestabilní architektura, která může způsobit ImportError při dalším rozšiřování.
- **Doporučení:** Sloučit oznameni do projekt nebo extrahovat sdílenou logiku do core.
- **Náročnost:** L

### [T02] ARCH-01: Přebujelá aplikace `core`
- **Soubory:** `webclient/core/` (77 .py souborů, 26 migrací)
- **Popis:** Core je importován 16+ aplikacemi. Obsahuje middleware, permissions, constants, signals, logging — příliš mnoho zodpovědností. Globální dopad změn.
- **Doporučení:** Dekomponovat na core.permissions, core.logging, core.middleware, core.signals.
- **Náročnost:** XL

### [T02] ARCH-02: Aplikace `dokument` — nadměrný fan-out
- **Soubory:** `webclient/dokument/`
- **Popis:** Importuje 8 jiných aplikací — nejvyšší fan-out v repozitáři. Potenciální narušení principu jedné zodpovědnosti.
- **Doporučení:** Auditovat závislosti, zvážit signály nebo services vrstvu.
- **Náročnost:** M

### [T03] ORM-01: Extra SELECT v save() metodách ArcheologickyZaznam a SamostatnyNalez
- **Soubory:** `webclient/arch_z/models.py:531`, `webclient/pas/models.py:182`
- **Popis:** Při každém volání `save()` (kde `pk != None`) se dělá extra `SELECT get(pk=self.pk)` pro zjištění změny `pristupnost`. Správné řešení je ukládání počáteční hodnoty v `__init__()` jako u `initial_stav`.
- **Doporučení:** Přidat `self._initial_pristupnost = self.pristupnost` v `__init__()`, v `save()` porovnat s `self._initial_pristupnost`.
- **Náročnost:** S

### [T03] ORM-02: N+1 v check_pred_* metodách
- **Soubory:** `webclient/projekt/models.py`, `webclient/arch_z/models.py`
- **Popis:** Metody `check_pred_uzavrenim()` a `check_pred_odeslanim()` dělají N+1 dotazy při iteraci přes akce a dokumentační jednotky. Viz BUG-002.
- **Doporučení:** Prefetch_related před voláním check metod, nebo přijmout prefetchovaná data jako parametr.
- **Náročnost:** M

### [T03] ORM-03: Chybějící indexy na pas.SamostatnyNalez
- **Soubory:** `webclient/pas/models.py`
- **Popis:** FK pole `projekt`, `katastr`, `pristupnost`, `stav` nemají `db_index=True`. Pro tabulku s tisíci záznamy jsou indexy klíčové.
- **Doporučení:** Přidat `db_index=True` nebo indexy přes migraci.
- **Náročnost:** S

## Střední priorita

<!-- Optimalizace, dekompozice modulů, Docker build -->

### [T02] CIRC-02: Cirkulární závislost adb ↔ xml_generator
- **Soubory:** `webclient/adb/models.py`, `webclient/xml_generator/generator.py`
- **Popis:** adb.models importuje BaseAmcrModel z xml_generator.models; xml_generator.generator importuje VyskovyBod z adb.models na úrovni modulu.
- **Doporučení:** Přesunout BaseAmcrModel/ModelWithMetadata do core nebo amcr_base modulu.
- **Náročnost:** M

### [T02] ARCH-03: Dualita zodpovědností xml_generator
- **Soubory:** `webclient/xml_generator/`
- **Popis:** xml_generator slouží jako base-model knihovna (BaseAmcrModel) i generátor XML. Importován 10 aplikacemi.
- **Doporučení:** Rozdělit na amcr_base (base modely) a xml_generator (čistě XML generátor).
- **Náročnost:** M

### [T06] CELERY-01: Zpevnit error handling dlouhých Celery úloh
- **Soubory:** `webclient/cron/tasks.py`
- **Popis:** Úlohy `update_all_redis_snapshots`, `update_single_redis_snapshot` a `update_materialized_views` nemají centrální ošetření výjimek. Chyba uprostřed dávky (např. výpadek Redis/DB nebo problém v REFRESH MATERIALIZED VIEW) ukončí celý task bez shrnutí a bez přehledného logu o částečném úspěchu.
- **Doporučení:** Zabalit hlavní smyčky/volání do `try/except` bloků s logováním shrnutí (počet zpracovaných položek, aktuální třída/model, jméno materializovaného pohledu) a konzistentním chováním při selhání.
- **Náročnost:** S

### [T06] CELERY-02: Timeout a error handling pro externí HTTP volání
- **Soubory:** `webclient/cron/tasks.py`
- **Popis:** Úloha `call_digiarchiv_update_task` volá `requests.get(settings.DIGIARCHIV_URL)` bez explicitního `timeout` a bez `try/except`. Při výpadku nebo pomalé odpovědi služby může worker čekat neúměrně dlouho a logy neobsahují jasnou informaci o příčině.
- **Doporučení:** Přidat rozumný `timeout` a obalit volání do `try/except` s logováním chyby; volitelně nastavit retry strategii přes Celery (např. countdown/max_retries).
- **Náročnost:** S

### [T06] CELERY-03: Omezit polling vzor v check_hlidaci_pes
- **Soubory:** `webclient/notifikace_projekty/tasks.py`
- **Popis:** Task `check_hlidaci_pes` čeká v while-smyčce (`time.sleep(0.5)`) na vytvoření projektu v DB, bez horního časového limitu. Při chybné konfiguraci nebo rollbacku transakce může běžet déle, než je žádoucí, a blokovat worker.
- **Doporučení:** Preferovat plánování tasku pomocí `transaction.on_commit()` (spuštění až po potvrzení transakce) nebo přidat maximální počet iterací / časový budget s bezpečným ukončením a logem po jeho překročení.
- **Náročnost:** M

### [T02] REQ-01: Smíšené produkční a vývojové závislosti v requirements.txt
- **Soubory:** `webclient/requirements.txt`
- **Popis:** Selenium, debug-toolbar, pre-commit, coverage, sphinx aj. jsou v produkčním requirements.txt. Produkční image je zbytečně velký.
- **Doporučení:** Rozdělit na requirements.txt, requirements-dev.txt, requirements-test.txt.
- **Náročnost:** S

### [T08] DOCS-01: Oddělit requirements pro build dokumentace
- **Soubory:** `readthedocs.yaml`, `webclient/requirements.txt`
- **Popis:** Read the Docs build instaluje kompletní `webclient/requirements.txt`, který obsahuje i vývojové a testovací balíčky (Selenium, debug-toolbar, Sphinx atd.). Pro build dokumentace to není nutné a zvyšuje čas i riziko konfliktů závislostí.
- **Doporučení:** Vytvořit samostatný soubor (např. `docs/requirements.txt`) s minimální sadou balíků pro dokumentaci a v `.readthedocs.yaml` přepnout instalaci na tento soubor.
- **Náročnost:** S

### [T08] DOCS-02: Zlepšit error handling v generátoru licencí
- **Soubory:** `docs/licenses/convert_to_rst.py`
- **Popis:** Skript spouští `pip-licenses` přes `subprocess.run` a bez kontroly návratového kódu rovnou parsuje JSON výstup. Při chybě nástroje nebo nevalidním výstupu skončí tracebackem bez srozumitelné hlášky.
- **Doporučení:** Kontrolovat `returncode` a obalit `json.loads` do `try/except` s jasnou chybovou zprávou (např. chybějící `pip-licenses`), případně vracet nenulový exit kód pro jasné selhání v CI.
- **Náročnost:** S

### [T10] SCRIPTS-01: Sjednotit fail-fast chování a wrappery v deploy skriptech
- **Soubory:** `scripts/prod_deploy.sh`, `scripts/dev_deploy.sh`, `scripts/test_deploy.sh`, `scripts/git_prod_deploy.sh`
- **Popis:** Deploy skripty používají vlastní wrapper er() pro logování a propagaci chyb, ale globálně nepoužívají `set -e`/`set -u`. Chyby v příkazech mimo er() se mohou projevit až zprostředkovaně (např. v následných krocích nebo pouze v logu).
- **Doporučení:** Přidat `set -e` (případně `set -u`) a přezkoumat, které příkazy mají být obaleny er() a které mohou selhat „měkce“. Zároveň sjednotit strukturu helper funkcí v jednotlivých skriptech, aby byly jednoduše udržovatelné.
- **Náročnost:** S

### [T08] DOCS-03: Vynutit úplnost docstringů pro Selenium testy
- **Soubory:** `docs/generate_selenium_test_docs.py`
- **Popis:** Generátor Selenium dokumentace počítá s tím, že všechny testy mají docstring a povinné sekce `Steps` a `Expected`. Chybějící sekce vede k neúplné dokumentaci bez jasného upozornění.
- **Doporučení:** Doplnit kontrolu a souhrnný report chybějících sekcí/docstringů a při běhu v CI (např. v pre-commit hooku) možnost selhat build, pokud nejsou splněna minimální dokumentační pravidla.
- **Náročnost:** M

### [T09] CI-01: Přidat Dependabot a lehký CodeQL workflow
- **Soubory:** `.github/` (nové workflow a konfigurace)
- **Popis:** Aktuální pipeline používá Docker Scout a Trivy pro skenování Docker image, ale nemá samostatnou kontrolu Python závislostí (Dependabot) ani statickou analýzu kódu (CodeQL). Riziko, že zranitelné knihovny v kódu projdou bez upozornění, je vyšší.
- **Doporučení:** Přidat `.github/dependabot.yml` pro Python a GitHub Actions a jednoduchý CodeQL workflow pro Python (např. běh na push/PR do větve `dev`), aby doplnil image-level scanning.
- **Náročnost:** S

### [T10] SCRIPTS-01: Přidat set -e do deploy a maintenance skriptů
- **Soubory:** `scripts/prod_deploy.sh`, `scripts/dev_deploy.sh`, `scripts/test_deploy.sh`, `scripts/git_prod_deploy.sh`, `scripts/restore_database.sh`, `scripts/build_prod_image.sh`, `scripts/ci_deployment/deploy_server.sh`, `scripts/ci_deployment/deploy_test_server.sh`
- **Popis:** Většina skriptů nemá `set -e`; selhání příkazu mimo wrapper `er()` může být přehlédnuto. `restore_database.sh` provádí DROP/CREATE databáze bez zastavení při chybě.
- **Doporučení:** Na začátek každého skriptu přidat `set -e` (a volitelně `set -o pipefail`); u interaktivních bloků zvážit dočasné vypnutí. V `restore_database.sh` navíc ověřit povinné proměnné prostředí před spuštěním.
- **Náročnost:** S

### [T10] SCRIPTS-02: Extrahovat společné funkce deploy skriptů do scripts/common.sh
- **Soubory:** `scripts/prod_deploy.sh`, `scripts/dev_deploy.sh`, `scripts/test_deploy.sh`, `scripts/git_prod_deploy.sh`
- **Popis:** Funkce `ask_continue`, `echo_dec`, `er()`, `check_create_network`, `check_stack_exists`, `check_file_exist` se opakují ve čtyřech skriptech; údržba a konzistence jsou ztížené.
- **Doporučení:** Vytvořit `scripts/common.sh` se sdílenými funkcemi a v deploy skriptech načítat pomocí `source "$(dirname "$0")/common.sh"` (nebo relativní cestou od kořene repozitáře).
- **Náročnost:** M

### [T10] SCRIPTS-03: Opravit db_connection_from_docker-web.py — použít DB_PORT ze secretu
- **Soubory:** `scripts/db/db_connection_from_docker-web.py`
- **Popis:** Skript načte z JSON secretu `DB_NAME`, `DB_PASS`, `DB_USER`, `DB_HOST`, ale ne `DB_PORT`; připojení k DB tedy vždy používá výchozí port 5432. Při nestandardním portu je health check nesprávný.
- **Doporučení:** Přidat načtení `DB_PORT` (s výchozí hodnotou 5432) a předat `port=...` do `psycopg2.connect()`. Viz BUG-014.
- **Náročnost:** S

## Nízká priorita

<!-- Kosmetické úpravy, dokumentace, minor code quality -->

### [T03] ORM-04: Nahradit eval() za int() v generátorech identifikátorů
- **Soubory:** `webclient/projekt/models.py:663`, `webclient/arch_z/models.py:331`, `webclient/arch_z/models.py:889`
- **Popis:** Tři výskyty `eval(i)` pro převod čísla z řetězce. Viz BUG-001.
- **Doporučení:** Nahradit `int(i)`, přidat validaci `i.isdigit()`.
- **Náročnost:** S

### [T03] ORM-05: Opravit import cached_property v uzivatel/models.py
- **Soubory:** `webclient/uzivatel/models.py:28`
- **Popis:** Import z `distlib.util` místo `functools`. Viz BUG-003.
- **Doporučení:** `from functools import cached_property`
- **Náročnost:** S

### [T03] ORM-06: Nahradit .extra() v arch_z/filters.py za RawSQL
- **Soubory:** `webclient/arch_z/filters.py:773-775`
- **Popis:** `.extra(where=["ST_Z(geom) >= %s"])` je deprecated od Django 4.0.
- **Doporučení:** Použít `RawSQL` nebo PostGIS funkci.
- **Náročnost:** S

### [T03] ORM-07: Squash migrací u aplikací s 20+ migracemi
- **Aplikace:** uzivatel (31), core (26), arch_z (20), dokument (19)
- **Popis:** Celkem 152 migrací — aplikace s nejvíce migracemi jsou kandidáty na `squashmigrations`.
- **Doporučení:** Postupný squash po stabilizaci schématu, začít s méně kritickými aplikacemi.
- **Náročnost:** M

### [T02/T04] DOCKER-DEP-01: logstash bez depends_on elasticsearch
- **Soubory:** `docker-compose.yml`
- **Popis:** logstash service nemá depends_on: elasticsearch — potenciální race condition při souběžném startu.
- **Doporučení:** Přidat depends_on: [elasticsearch] do logstash service.
- **Náročnost:** S

### [T04] DOCKER-01: Opravit secret injection pro Grafana, Elasticsearch, Logstash
- **Soubory:** `docker-compose.yml:149,180-181,201`, `docker-compose-test.yml:169`, `git_docker-compose.yml:144`
- **Popis:** `GF_SECURITY_ADMIN_PASSWORD`, `ELASTIC_PASSWORD`, `LOGSTASH_INTERNAL_PASSWORD` jsou nastaveny na cesty k souborům nebo názvy secretů, nikoli na jejich hodnoty. Grafana admin heslo je fakticky nefunkční.
- **Doporučení:** Grafana: použít `GF_SECURITY_ADMIN_PASSWORD__FILE`. Elasticsearch/Logstash: entrypoint wrapper skript načítající secret ze souboru.
- **Náročnost:** S
- **Závažnost:** Střední

### [T04] DOCKER-02: Celery worker v produkci loguje DEBUG
- **Soubory:** `docker-compose.yml:81`
- **Popis:** `celery -A webclient worker -l DEBUG` — nadměrné logování, potenciální expozice citlivých dat v produkci.
- **Doporučení:** Změnit na `-l INFO`.
- **Náročnost:** S
- **Závažnost:** Střední

### [T04] DOCKER-03: ELK Stack major version gap (prod 9.x vs dev 8.x)
- **Soubory:** `docker-compose.yml`, `docker-compose-dev-local-db*.yml`
- **Popis:** Produkce, test a git-deploy používají ELK 9.3.1; dev compose používají 8.19.0. Major version gap způsobuje rozdílné chování xpack.security a API.
- **Doporučení:** Synchronizovat na stejnou major verzi (doporučeno dev = prod).
- **Náročnost:** S
- **Závažnost:** Střední

### [T04] DOCKER-04: sudo přístup v produkčním kontejneru
- **Soubory:** `Dockerfile:99`
- **Popis:** `usermod -aG sudo user` — produkční aplikační uživatel je člen sudo skupiny.
- **Doporučení:** Odebrat sudo skupinu, použít specifická NOPASSWD pravidla pro nutné operace.
- **Náročnost:** S
- **Závažnost:** Střední

### [T04] DOCKER-05: Selenium v produkčním docker-compose.yml
- **Soubory:** `docker-compose.yml`
- **Popis:** Selenium service patří výhradně do testovacího prostředí.
- **Doporučení:** Odebrat ze docker-compose.yml, ponechat pouze v docker-compose-test.yml.
- **Náročnost:** S
- **Závažnost:** Nízká

### [T04] DOCKER-06: Fedora Dockerfile — vícenásobný apt-get update, žádný PID 1
- **Soubory:** `fedora/Dockerfile`
- **Popis:** Tři separátní RUN apt-get update příkazy bez apt-get clean zvětšují image. CMD spouští dva procesy bez process supervisora.
- **Doporučení:** Sloučit RUN bloky, přidat tini nebo entrypoint skript.
- **Náročnost:** S
- **Závažnost:** Nízká

### [T02] REQ-02: sphinxcontrib-mermaid bez specifikace verze
- **Soubory:** `webclient/requirements.txt`
- **Popis:** Balíček sphinxcontrib-mermaid je bez pevné verze — nedeterministické buildy.
- **Doporučení:** Přidat konkrétní verzi.
- **Náročnost:** S

### [T01] ARCH-04: cron a notifikace_projekty bez testů
- **Soubory:** `webclient/cron/`, `webclient/notifikace_projekty/`
- **Popis:** Obě aplikace nemají žádné testy, přestože cron importuje 6 jiných aplikací.
- **Doporučení:** Přidat unit testy pro Celery tasky.
- **Náročnost:** M

### [T05] SEC-01: Opravit DEBUG fallback v production.py
- **Soubor:** `webclient/webclient/settings/production.py:3`
- **Popis:** `get_secret("DEBUG", "True")` — fallback je "True" → DEBUG=True při chybějícím klíči. Viz BUG-010.
- **Doporučení:** Změnit fallback na "False".
- **Náročnost:** S
- **Závažnost:** Vysoká

### [T05] SEC-02: Rotace Mailtrap credentials a nahrazení placeholdery
- **Soubor:** `webclient/webclient/settings/sample_secrets_mail_client.json`
- **Popis:** Zdánlivě reálné Mailtrap sandbox credentials v commitu. Viz BUG-011.
- **Doporučení:** Ověřit, rotovat, nahradit za zjevné placeholdery.
- **Náročnost:** S
- **Závažnost:** Střední

### [T05] SEC-03: Přidat Django security headers do production.py
- **Soubor:** `webclient/webclient/settings/production.py`
- **Popis:** Chybí `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_CONTENT_TYPE_NOSNIFF`. Django security check (`manage.py check --deploy`) bude hlásit selhání.
- **Doporučení:** Přidat do production.py a přidat `manage.py check --deploy` do CI pipeline.
- **Náročnost:** S
- **Závažnost:** Střední

### [T05] SEC-XSS: Audit mark_safe() ve vypis/ aplikaci
- **Soubory:** `webclient/vypis/fields.py:363,438`, `webclient/vypis/views.py:79`
- **Popis:** Tři místa aplikují `mark_safe()` na hodnoty z DB nebo model properties. Viz BUG-012.
- **Doporučení:** Přepsat na `format_html()` nebo zajistit `escape()` před mark_safe.
- **Náročnost:** M
- **Závažnost:** Střední

### [T05] SEC-04: Přidat CVE scanning do CI pipeline
- **Soubory:** `.github/workflows/` (nový krok)
- **Popis:** Chybí automatická kontrola CVE v Python závislostech.
- **Doporučení:** Přidat `pip audit` nebo `safety check` jako CI krok.
- **Náročnost:** S
- **Závažnost:** Střední

### [T07] FRONT-01: Extrahovat větší inline skripty z base.html
- **Soubory:** `webclient/templates/base.html`
- **Popis:** Šablona `base.html` obsahuje několik větších inline skriptů (inicializace datepickerů, automatické skrývání flash zpráv, periodická kontrola autentizace, jazykový přepínač). Logika je korektní, ale hůře znovupoužitelná a méně přehledná v inline podobě.
- **Doporučení:** Přesunout tyto bloky do samostatných JS souborů ve `static/js/` (např. `datepicker-init.js`, `messages.js`, `auth_check.js`, `language_switcher.js`) a v šabloně je načítat přes `{% static %}`.
- **Náročnost:** S

### [T07] FRONT-02: Zvážit bundler/minifikaci vlastního JS
- **Soubory:** `webclient/static/js/`
- **Popis:** Vlastní JavaScript (mapové skripty, helpery, theme-toggle) je servírován jako více samostatných souborů bez bundleru a minifikace. V produkci to zvyšuje počet HTTP požadavků a velikost assetů.
- **Doporučení:** Zvážit nasazení lehkého bundleru (např. Webpack/Vite/rollup) nebo alespoň minifikačního kroku v rámci stávajícího `django-compressor` nastavení pro vlastní JS.
- **Náročnost:** M
