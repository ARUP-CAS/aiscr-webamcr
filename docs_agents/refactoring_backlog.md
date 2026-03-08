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
