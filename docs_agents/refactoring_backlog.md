# Refactoring backlog — AMČR (aiscr-webamcr)

> Všechny záznamy jsou psány v češtině.
> Strukturální zlepšení objevená během auditu.

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

### [T02] REQ-01: Smíšené produkční a vývojové závislosti v requirements.txt
- **Soubory:** `webclient/requirements.txt`
- **Popis:** Selenium, debug-toolbar, pre-commit, coverage, sphinx aj. jsou v produkčním requirements.txt. Produkční image je zbytečně velký.
- **Doporučení:** Rozdělit na requirements.txt, requirements-dev.txt, requirements-test.txt.
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

### [T02] DOCKER-DEP-01: logstash bez depends_on elasticsearch
- **Soubory:** `docker-compose.yml`
- **Popis:** logstash service nemá depends_on: elasticsearch — potenciální race condition při souběžném startu.
- **Doporučení:** Přidat depends_on: [elasticsearch] do logstash service.
- **Náročnost:** S

### [T02] REQ-02: sphinxcontrib-mermaid bez specifikace verze
- **Soubory:** `webclient/requirements.txt`
- **Popis:** Balíček sphinxcontrib-mermaid je bez pevné verze — nedeterministické buildy.
- **Doporučení:** Přidat konkrétní verzi.
- **Náročnost:** S

### [T02] ARCH-04: cron a notifikace_projekty bez testů
- **Soubory:** `webclient/cron/`, `webclient/notifikace_projekty/`
- **Popis:** Obě aplikace nemají žádné testy, přestože cron importuje 6 jiných aplikací.
- **Doporučení:** Přidat unit testy pro Celery tasky.
- **Náročnost:** M
