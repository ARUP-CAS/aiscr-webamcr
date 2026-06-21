# Evidované chyby — AMČR (aiscr-webamcr)

> Legacy entries remain mostly in Czech; newly touched review prose follows the canonical English-default rule with verbatim Czech preserved where exact source wording matters.
> Před přidáním nové chyby ověř existující GitHub Issues (aktuálně 113 otevřených).
>
> Stavy: `již evidováno (Issue #XXX)` | `rozšíření existujícího issue #XXX` | `nový kandidát na issue`
>
> Severity values: `Critical` | `High` | `Medium` | `Low`

---

<!-- Záznamy přidávají agenti po dokončení jednotlivých tasků -->

### BUG-001: eval() na hodnotách z databáze v generátorech identifikátorů

- **Soubory:**
  - `webclient/projekt/models.py:663` — `Projekt.set_permanent_ident_cely()`
  - `webclient/arch_z/models.py:331` — `ArcheologickyZaznam.set_lokalita_permanent_ident_cely()`
  - `webclient/arch_z/models.py:889` — `get_akce_ident()`
  - `webclient/dokument/models.py:441` — `Dokument.set_permanent_ident_cely()` *(nalezeno T03c)*
  - `webclient/ez/models.py:301` — `get_perm_ez_ident()` *(nalezeno T03c)*
- **Severity:** Medium
- **GitHub Issue:** nový kandidát na issue
- **Popis:** Všech pět míst používá `eval(i)` pro převod textového čísla (segmentu `ident_cely` z DB) na integer. Ačkoliv jsou hodnoty interně generované a jejich formát je řízen aplikací, `eval()` je inherentně nebezpečná funkce — pokud by byl formát ident_cely narušen (např. chybnou migrací dat), mohl by být spuštěn libovolný Python kód. Viz SEC-ORM-001 až SEC-ORM-005 v `orm_analysis.json`.
- **Navrhovaná oprava:** Nahradit `eval(i)` za `int(i)` na všech pěti místech. Přidat validaci formátu před konverzí (např. `i.isdigit()`).
- **Task:** T03

---

### BUG-002: N+1 dotazy v ArcheologickyZaznam.check_pred_odeslanim() a Projekt.check_pred_uzavrenim()

- **Soubory:**
  - `webclient/arch_z/models.py:240-268`
  - `webclient/projekt/models.py:561-578`
- **Severity:** Medium
- **GitHub Issue:** nový kandidát na issue
- **Popis:** `check_pred_odeslanim()` volá `self.dokumentacni_jednotky_akce.all()` dvakrát a pro každou DJ dělá dotaz na `dj.komponenty.komponenty.all()`. `check_pred_uzavrenim()` volá `self.akce_set.all()` dvakrát a pro každou akci spouští kaskádovou `check_pred_odeslanim()`. Tyto metody jsou volány při každém pokusu o posun stavu záznamu — pro projekty s více akcemi a DJ může počet dotazů dosáhnout desítek.
- **Navrhovaná oprava:** Přidat `prefetch_related` ve view metodách před voláním `check_pred_*`. Refaktorovat `check_pred_*` metody tak, aby přijímaly prefetchovaná data jako parametr.
- **Task:** T03

---

### BUG-003: Import cached_property z distlib.util místo functools

- **Soubory:** `webclient/uzivatel/models.py:28`
- **Severity:** Low
- **GitHub Issue:** nový kandidát na issue
- **Popis:** `from distlib.util import cached_property` — `distlib` je balíčkovací nástroj (součást pip), nikoliv Django nebo Python standard library. Správná implementace je `from functools import cached_property` (Python 3.8+). Import funguje, ale je nespolehlivý jako závislost a matoucí pro vývojáře.
- **Navrhovaná oprava:** `from functools import cached_property`
- **Task:** T03

---

### BUG-004: Extra SELECT v SamostatnyNalez.save() — initial_pristupnost vzor je neúplný

- **Soubor:** `webclient/pas/models.py:182-186`
- **Severity:** Medium
- **Sjednocení:** Závažnost zvýšena z Low na Medium (2026-03-13); extra SELECT se spouští při každém uložení záznamu a jde o architektonický anti-pattern — odpovídá zařazení ORM-01 do Vysoké priority v refactoring_backlog.md.
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** Model `SamostatnyNalez` má property `initial_pristupnost`, ale v metodě `save()` stále bezpodmínečně volá `SamostatnyNalez.objects.get(pk=self.pk)` při každém uložení záznamu (kde `pk is not None`). Správný vzor ukládá počáteční hodnotu v `__init__()`, čímž extra SELECT odpadá.
- **Navrhovaná oprava:** Přidat do `__init__()`: `self._initial_pristupnost = self.pristupnost`. V `save()` porovnat `self._initial_pristupnost != self.pristupnost` bez extra SELECT.
- **Task:** T03b

---

### BUG-005: Chybějící db_index na Heslar.nazev_heslare (FK globálně používané v limit_choices_to)

- **Soubor:** `webclient/heslar/models.py:22-23`
- **Severity:** Medium
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** Pole `Heslar.nazev_heslare` je FK na `HeslarNazev` bez `db_index=True`. Toto pole je filtrováno v `limit_choices_to` v desítkách FK polí napříč celou aplikací (proj, pas, arch_z, uzivatel, dokument, adb, heslar atd.). Absence indexu způsobuje table scan na tabulce `heslar` pro každý formulářový dotaz.
- **Navrhovaná oprava:** Přidat `db_index=True` do FK definice `nazev_heslare` v `heslar/models.py`. Alternativně přidat explicitní `models.Index(fields=["nazev_heslare"])` v `Meta.indexes`.
- **Task:** T03b

---

### BUG-006: get_vyskovy_bod() volá .count() dvakrát na stejném querysetu

- **Soubor:** `webclient/adb/models.py:163-171`
- **Severity:** Low
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** Funkce `get_vyskovy_bod()` volá `vyskove_body.count()` dvakrát — jednou pro test na 0 a jednou pro test na maximum — každé volání spouští samostatný SQL COUNT dotaz.
- **Navrhovaná oprava:** Uložit výsledek `count = vyskove_body.count()` jednou a porovnat `count == 0` a `count <= MAXIMAL_VYSKOVY_BOD + offset`.
- **Task:** T03b

---

### BUG-007: GF_SECURITY_ADMIN_PASSWORD nastaveno na cestu k souboru místo hesla

- **Soubory:**
  - `docker-compose.yml:149`
  - `docker-compose-test.yml:169`
  - `git_docker-compose.yml:144`
- **Severity:** Medium
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** Grafana `GF_SECURITY_ADMIN_PASSWORD=/run/secrets/grafana_admin_password` nastavuje admin heslo na literální string (cestu k souboru), nikoli na obsah Docker secretu. Grafná nepodporuje automatické čtení Docker secrets přes `GF_SECURITY_ADMIN_PASSWORD`; správný formát je `GF_SECURITY_ADMIN_PASSWORD__FILE`. Důsledek: Grafana admin heslo je literální string `/run/secrets/grafana_admin_password`.
- **Navrhovaná oprava:** Nahradit `GF_SECURITY_ADMIN_PASSWORD=...` za `GF_SECURITY_ADMIN_PASSWORD__FILE=/run/secrets/grafana_admin_password` ve všech třech souborech.
- **Task:** T04

---

### BUG-008: ELASTIC_PASSWORD a LOGSTASH_INTERNAL_PASSWORD nastaveny na názvy secretů

- **Soubory:**
  - `docker-compose.yml:180-181,201`
  - `git_docker-compose.yml:172-173,194`
- **Severity:** Medium
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** Elasticsearch `ELASTIC_PASSWORD=elastic_pass` a Logstash `LOGSTASH_INTERNAL_PASSWORD=logstash_elastic_pass` mají jako hodnotu název Docker secretu (řetězec), nikoli jeho obsah. Elasticsearch ani Logstash Docker images nepodporují `_FILE` variantu pro tyto proměnné. Výsledek: Elasticsearch bootstrap heslo je nastaveno na literál `"elastic_pass"` namísto skutečné hodnoty ze secretu.
- **Navrhovaná oprava:** Použít entrypoint wrapper skript: `export ELASTIC_PASSWORD=$(cat /run/secrets/elastic_pass)` před spuštěním Elasticsearch / Logstash.
- **Task:** T04

---

### BUG-009: sudo přístup aplikačního uživatele v produkčním kontejneru

- **Soubor:** `Dockerfile:99`
- **Severity:** Medium
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** `usermod -aG sudo user` přidává produkčního aplikačního uživatele do skupiny `sudo`. Pokud dojde k RCE exploitaci aplikace (např. přes eval() — viz BUG-001), útočník může eskalovat oprávnění na root uvnitř kontejneru.
- **Navrhovaná oprava:** Odebrat `usermod -aG sudo user`. Pro nutné privilegované operace (crontab setup) nastavit specifická NOPASSWD pravidla v `/etc/sudoers`.
- **Task:** T04

---

### BUG-010: Nebezpečný fallback pro DEBUG v production.py

- **Soubor:** `webclient/webclient/settings/production.py:3`
- **Severity:** High
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** `DEBUG = get_secret("DEBUG", "True") == "True"` — výchozí fallback je řetězec `"True"`. Pokud klíč `DEBUG` chybí v secrets souboru, produkční instance se spustí s `DEBUG=True`. To vystavuje úplné Python tracebacky, settings hodnoty a deaktivuje bezpečnostní kontroly Django.
- **Navrhovaná oprava:** Změnit fallback na `"False"`: `DEBUG = get_secret("DEBUG", "False") == "True"`
- **Task:** T05

---

### BUG-011: Mailtrap credentials v commitu

- **Soubor:** `webclient/webclient/settings/sample_secrets_mail_client.json`
- **Severity:** Medium
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** Soubor obsahuje zdánlivě reálné Mailtrap sandbox credentials (`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`). Kdokoliv s přístupem k repozitáři může použít tyto credentials k přihlášení do Mailtrap a číst zachycené testovací e-maily.
- **Navrhovaná oprava:** Ověřit zda jsou credentials aktivní, pokud ano rotovat. Nahradit v souboru za zjevné placeholder hodnoty (např. `"PLACEHOLDER_USER"`, `"PLACEHOLDER_PASSWORD"`).
- **Task:** T05

---

### BUG-012: mark_safe() s hodnotami z databáze ve vypis/fields.py

- **Soubory:**
  - `webclient/vypis/fields.py:363` — `mark_safe(value.get_ident_cely_link)`
  - `webclient/vypis/fields.py:438` — `mark_safe(new_instance)`
  - `webclient/vypis/views.py:79` — `mark_safe(field.get_name(instance))`
- **Severity:** Medium
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** Tři místa v `vypis/` aplikují `mark_safe()` na hodnoty odvozené z databázových instancí nebo model properties. Pokud tyto hodnoty nejsou správně escapovány před zabalením do `mark_safe()`, může dojít ke stored XSS. Ident_cely hodnoty mají řízenou strukturu, ale vzor je architektonicky nebezpečný a vyžaduje explicitní ověření.
- **Navrhovaná oprava:** Auditovat `get_ident_cely_link` property, `get_name()` implementace a Dokument.extra_data atribut. Přepsat na `format_html()` nebo zajistit `escape()` před `mark_safe()`.
- **Task:** T05

---

### BUG-013: restore_database.sh neověřuje povinné proměnné prostředí před DROP DATABASE

- **Soubory:** `scripts/restore_database.sh`
- **Severity:** Medium
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** Skript používá `${DBNAME}`, `${USED_DB_BACKUP}`, `${DB_FLAG_ROLE}` bez kontroly, zda jsou nastaveny. Při prázdných hodnotách může dojít k nechtěnému DROP/CREATE (např. prázdné jméno databáze) nebo k nejasné chybě při pg_restore.
- **Navrhovaná oprava:** Na začátku skriptu ověřit, že `DBNAME`, `USED_DB_BACKUP`, `DB_FLAG_ROLE` jsou neprázdné; při chybě vypsat usage a ukončit s exit 1. Přidat `set -e`.
- **Task:** T10

---

### BUG-014: db_connection_from_docker-web.py ignoruje DB_PORT ze secretu

- **Soubory:** `scripts/db/db_connection_from_docker-web.py`
- **Severity:** Medium
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** Skript načte z `/run/secrets/db_conf` pouze `DB_NAME`, `DB_PASS`, `DB_USER`, `DB_HOST`. Připojení k PostgreSQL tedy vždy používá výchozí port 5432. Pokud je databáze na jiném portu, health check selže nebo kontroluje jinou instanci.
- **Navrhovaná oprava:** Načíst z JSON i `DB_PORT` (s výchozí hodnotou 5432) a předat do `psycopg2.connect(..., port=db_port)`.
- **Task:** T10

---

### BUG-015: NalezPredmet.__init_ — překlep v názvu metody (chybí jedno podtržítko)

- **Soubory:** `webclient/nalez/models.py:116`
- **Severity:** Medium
- **GitHub Issue:** nový kandidát na issue
- **Popis:** Metoda je definována jako `def __init_(self, ...)` s jedním podtržítkem na konci místo `__init__` se dvěma. Python tuto metodu nevolá jako konstruktor, takže vlastní inicializace (`close_active_transaction_when_finished = False`, `active_transaction = None`) se nikdy neprovede. Sesterský model `NalezObjekt` má správně `__init__`. Dopady závisí na tom, zda tyto atributy jsou používány jinde (signály, transakce).
- **Navrhovaná oprava:** Přejmenovat `__init_` na `__init__`.
- **Task:** T03d

---

### BUG-016: form_fields_disabling.js — invertovaná podmínka pro select/non-select prvky

- **Soubory:** `webclient/static/js/form_fields_disabling.js:65`
- **Severity:** Medium
- **GitHub Issue:** nový kandidát na issue
- **Popis:** Podmínka `element.type != 'select-multiple' || element.type != 'select-one'` je logicky vždy pravdivá (de Morganův zákon — OR s negacemi). Větve pro select a non-select formulářové prvky jsou tím invertovány. Projeví se nesprávným povolováním/zakazováním polí při změně nadřazeného selectu.
- **Navrhovaná oprava:** Nahradit `||` operátor za `&&`.
- **Task:** T07b

---

### BUG-017: coor_precision.js — chybná konstanta přesnosti pro JTSK (používá WGS84)

- **Soubory:** `webclient/static/js/coor_precision.js:31`
- **Severity:** Medium
- **GitHub Issue:** nový kandidát na issue
- **Popis:** Funkce `amcr_static_coordinate_precision_jtsk` pro ne-array vstup používá `global_fixed_precision.wgs84` místo `global_fixed_precision.jtsk`. JTSK souřadnice jsou zaokrouhlovány s přesností WGS84, což vede k nesprávnému zaokrouhlení (typicky 6 desetinných míst pro WGS84 vs 2 pro JTSK).
- **Navrhovaná oprava:** Na řádku 31 nahradit `global_fixed_precision.wgs84` za `global_fixed_precision.jtsk`.
- **Task:** T07b
