# Evidované chyby — AMČR (aiscr-webamcr)

> Všechny záznamy jsou psány v češtině.
> Před přidáním nové chyby ověř existující GitHub Issues (aktuálně 113 otevřených).
>
> Stavy: `již evidováno (Issue #XXX)` | `rozšíření existujícího issue #XXX` | `nový kandidát na issue`
>
> Závažnosti: `Kritická` | `Vysoká` | `Střední` | `Nízká`

---

<!-- Záznamy přidávají agenti po dokončení jednotlivých tasků -->

### BUG-001: eval() na hodnotách z databáze v generátorech identifikátorů

- **Soubory:**
  - `webclient/projekt/models.py:663` — `Projekt.set_permanent_ident_cely()`
  - `webclient/arch_z/models.py:331` — `ArcheologickyZaznam.set_lokalita_permanent_ident_cely()`
  - `webclient/arch_z/models.py:889` — `get_akce_ident()`
- **Závažnost:** Střední
- **GitHub Issue:** nový kandidát na issue
- **Popis:** Všechna tři místa používají `eval(i)` pro převod textového čísla (segmentu `ident_cely` z DB) na integer. Ačkoliv jsou hodnoty interně generované a jejich formát je řízen aplikací, `eval()` je inherentně nebezpečná funkce — pokud by byl formát ident_cely narušen (např. chybnou migrací dat), mohl by být spuštěn libovolný Python kód.
- **Navrhovaná oprava:** Nahradit `eval(i)` za `int(i)` na všech třech místech. Přidat validaci formátu před konverzí (např. `i.isdigit()`).
- **Task:** T03

---

### BUG-002: N+1 dotazy v ArcheologickyZaznam.check_pred_odeslanim() a Projekt.check_pred_uzavrenim()

- **Soubory:**
  - `webclient/arch_z/models.py:240-268`
  - `webclient/projekt/models.py:561-578`
- **Závažnost:** Střední
- **GitHub Issue:** nový kandidát na issue
- **Popis:** `check_pred_odeslanim()` volá `self.dokumentacni_jednotky_akce.all()` dvakrát a pro každou DJ dělá dotaz na `dj.komponenty.komponenty.all()`. `check_pred_uzavrenim()` volá `self.akce_set.all()` dvakrát a pro každou akci spouští kaskádovou `check_pred_odeslanim()`. Tyto metody jsou volány při každém pokusu o posun stavu záznamu — pro projekty s více akcemi a DJ může počet dotazů dosáhnout desítek.
- **Navrhovaná oprava:** Přidat `prefetch_related` ve view metodách před voláním `check_pred_*`. Refaktorovat `check_pred_*` metody tak, aby přijímaly prefetchovaná data jako parametr.
- **Task:** T03

---

### BUG-003: Import cached_property z distlib.util místo functools

- **Soubory:** `webclient/uzivatel/models.py:28`
- **Závažnost:** Nízká
- **GitHub Issue:** nový kandidát na issue
- **Popis:** `from distlib.util import cached_property` — `distlib` je balíčkovací nástroj (součást pip), nikoliv Django nebo Python standard library. Správná implementace je `from functools import cached_property` (Python 3.8+). Import funguje, ale je nespolehlivý jako závislost a matoucí pro vývojáře.
- **Navrhovaná oprava:** `from functools import cached_property`
- **Task:** T03

---

### BUG-004: Extra SELECT v SamostatnyNalez.save() — initial_pristupnost vzor je neúplný

- **Soubor:** `webclient/pas/models.py:182-186`
- **Závažnost:** Nízká
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** Model `SamostatnyNalez` má property `initial_pristupnost`, ale v metodě `save()` stále bezpodmínečně volá `SamostatnyNalez.objects.get(pk=self.pk)` při každém uložení záznamu (kde `pk is not None`). Správný vzor ukládá počáteční hodnotu v `__init__()`, čímž extra SELECT odpadá.
- **Navrhovaná oprava:** Přidat do `__init__()`: `self._initial_pristupnost = self.pristupnost`. V `save()` porovnat `self._initial_pristupnost != self.pristupnost` bez extra SELECT.
- **Task:** T03b

---

### BUG-005: Chybějící db_index na Heslar.nazev_heslare (FK globálně používané v limit_choices_to)

- **Soubor:** `webclient/heslar/models.py:22-23`
- **Závažnost:** Střední
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** Pole `Heslar.nazev_heslare` je FK na `HeslarNazev` bez `db_index=True`. Toto pole je filtrováno v `limit_choices_to` v desítkách FK polí napříč celou aplikací (proj, pas, arch_z, uzivatel, dokument, adb, heslar atd.). Absence indexu způsobuje table scan na tabulce `heslar` pro každý formulářový dotaz.
- **Navrhovaná oprava:** Přidat `db_index=True` do FK definice `nazev_heslare` v `heslar/models.py`. Alternativně přidat explicitní `models.Index(fields=["nazev_heslare"])` v `Meta.indexes`.
- **Task:** T03b

---

### BUG-006: get_vyskovy_bod() volá .count() dvakrát na stejném querysetu

- **Soubor:** `webclient/adb/models.py:163-171`
- **Závažnost:** Nízká
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
- **Závažnost:** Střední
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** Grafana `GF_SECURITY_ADMIN_PASSWORD=/run/secrets/grafana_admin_password` nastavuje admin heslo na literální string (cestu k souboru), nikoli na obsah Docker secretu. Grafná nepodporuje automatické čtení Docker secrets přes `GF_SECURITY_ADMIN_PASSWORD`; správný formát je `GF_SECURITY_ADMIN_PASSWORD__FILE`. Důsledek: Grafana admin heslo je literální string `/run/secrets/grafana_admin_password`.
- **Navrhovaná oprava:** Nahradit `GF_SECURITY_ADMIN_PASSWORD=...` za `GF_SECURITY_ADMIN_PASSWORD__FILE=/run/secrets/grafana_admin_password` ve všech třech souborech.
- **Task:** T04

---

### BUG-008: ELASTIC_PASSWORD a LOGSTASH_INTERNAL_PASSWORD nastaveny na názvy secretů

- **Soubory:**
  - `docker-compose.yml:180-181,201`
  - `git_docker-compose.yml:172-173,194`
- **Závažnost:** Střední
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** Elasticsearch `ELASTIC_PASSWORD=elastic_pass` a Logstash `LOGSTASH_INTERNAL_PASSWORD=logstash_elastic_pass` mají jako hodnotu název Docker secretu (řetězec), nikoli jeho obsah. Elasticsearch ani Logstash Docker images nepodporují `_FILE` variantu pro tyto proměnné. Výsledek: Elasticsearch bootstrap heslo je nastaveno na literál `"elastic_pass"` namísto skutečné hodnoty ze secretu.
- **Navrhovaná oprava:** Použít entrypoint wrapper skript: `export ELASTIC_PASSWORD=$(cat /run/secrets/elastic_pass)` před spuštěním Elasticsearch / Logstash.
- **Task:** T04

---

### BUG-009: sudo přístup aplikačního uživatele v produkčním kontejneru

- **Soubor:** `Dockerfile:99`
- **Závažnost:** Střední
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** `usermod -aG sudo user` přidává produkčního aplikačního uživatele do skupiny `sudo`. Pokud dojde k RCE exploitaci aplikace (např. přes eval() — viz BUG-001), útočník může eskalovat oprávnění na root uvnitř kontejneru.
- **Navrhovaná oprava:** Odebrat `usermod -aG sudo user`. Pro nutné privilegované operace (crontab setup) nastavit specifická NOPASSWD pravidla v `/etc/sudoers`.
- **Task:** T04

---

### BUG-010: Nebezpečný fallback pro DEBUG v production.py

- **Soubor:** `webclient/webclient/settings/production.py:3`
- **Závažnost:** Vysoká
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** `DEBUG = get_secret("DEBUG", "True") == "True"` — výchozí fallback je řetězec `"True"`. Pokud klíč `DEBUG` chybí v secrets souboru, produkční instance se spustí s `DEBUG=True`. To vystavuje úplné Python tracebacky, settings hodnoty a deaktivuje bezpečnostní kontroly Django.
- **Navrhovaná oprava:** Změnit fallback na `"False"`: `DEBUG = get_secret("DEBUG", "False") == "True"`
- **Task:** T05

---

### BUG-011: Mailtrap credentials v commitu

- **Soubor:** `webclient/webclient/settings/sample_secrets_mail_client.json`
- **Závažnost:** Střední
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
- **Závažnost:** Střední
- **GitHub Issue:** nový kandidát na issue — nelze ověřit, GitHub Issues nedostupné bez autentizace
- **Popis:** Tři místa v `vypis/` aplikují `mark_safe()` na hodnoty odvozené z databázových instancí nebo model properties. Pokud tyto hodnoty nejsou správně escapovány před zabalením do `mark_safe()`, může dojít ke stored XSS. Ident_cely hodnoty mají řízenou strukturu, ale vzor je architektonicky nebezpečný a vyžaduje explicitní ověření.
- **Navrhovaná oprava:** Auditovat `get_ident_cely_link` property, `get_name()` implementace a Dokument.extra_data atribut. Přepsat na `format_html()` nebo zajistit `escape()` před `mark_safe()`.
- **Task:** T05
