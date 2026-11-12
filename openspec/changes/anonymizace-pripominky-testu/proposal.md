# Proposal

## Why

Test verze v2.0.0-alpha.2 ukázal, že příkaz `anonymizace_dat` (issue [ARUP-CAS/aiscr-webamcr#4264](https://github.com/ARUP-CAS/aiscr-webamcr/issues/4264), [připomínky testu](https://github.com/ARUP-CAS/aiscr-webamcr/issues/4264#issuecomment-6271466432)) přepisuje i veřejné texty, ponechává skutečné údaje na několika místech, používá doménu, která nezaručuje nedoručení, a hlásí úspěch, i když některá chráněná poloha zůstala skutečná. Testovací server tak může držet citlivé údaje, nebo odesílat poštu skutečným adresátům.

## What Changes

- Chráněná textová pole se přepisují jen u záznamů s přístupností vyšší než A; veřejné záznamy si ponechají skutečné texty. **BREAKING** proti dosavadnímu chování, které přepisovalo všechny záznamy.
- Výjimka z anonymizace uživatelů se místo řetězce `Anonym` v příjmení váže na napojení na osobu `OS-007414`. Administrátoři zůstávají vyloučení jako dosud.
- Anonymizovaní uživatelé přijdou o napojení na osobu i o ORCID.
- Zástupné e-maily leží v rezervované doméně nejvyšší úrovně `.invalid`; nahrazují se i e-maily krajů.
- U historie typu `KAT` (změna katastru) chráněných záznamů se odstraní poznámka, která prozrazuje skutečné katastry.
- Před prvním zápisem příkaz zjistí, které chráněné polohy nepůjde nahradit, a když nějaké najde, skončí chybou bez jediného zápisu. PIAN, pro který není poloha v původním listu ZM50, se přesune kamkoli v okresu; bodový záznam, kterému nejde najít polohu, přijde o geometrii.
- Běh, po kterém zůstala nenahrazená chráněná poloha nebo došlo k chybě, skončí nenulovým návratovým kódem a nikdy nehlásí úspěch.

## Capabilities

### New Capabilities
- `anonymizace-dat`: anonymizace kopie produkční databáze na testovacím serveru – které údaje se nahrazují, které záznamy jsou vyloučené a kdy běh blokuje navazující publikaci metadat.

### Modified Capabilities

Žádné; repozitář zatím nemá žádnou trvalou specifikaci.

Nová specifikace pokrývá chování měněné touto změnou. Zbytek chování příkazu zavedeného v [ARUP-CAS/aiscr-webamcr#4333](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4333) zůstává popsaný v dokumentaci příkazu a do specifikace se doplní samostatně.

## Impact

- Mění se chování aplikace, ne governance; žádná cesta synchronizovaná z hubu `aiscr-management` se nemění.
- Kód: `webclient/core/management/commands/anonymizace_dat.py`, `webclient/core/management/commands/utils/anonymizace.py`, `webclient/core/management/commands/utils/anonymizace_geometrie.py`, testy `webclient/core/tests/test_anonymizace.py`.
- Generovaná dokumentace `docs/source/04_django_aplikace/04_01_core/management_commands.rst` se přegeneruje hookem; postup prvního nasazení v `docs/source/02_instalace_nasazeni/ruian_sync_nasazeni.rst` dostane poznámku o pořadí syncu katastrů a anonymizace.
- Migrační postup na testovací server: blokující kontrola může zastavit migraci před `generate_metadata`, dokud se vadná data nevyřeší.
- Bez migrací databáze a bez nových závislostí.
