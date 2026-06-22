PAS API — Endpointy pro import samostatných nálezů
===================================================

Tato sekce popisuje REST API endpointy pro programatický import a aktualizaci
samostatných nálezů v systému AMČR.

Všechny endpointy vyžadují:

- **Autentizaci** Bearer tokenem (hlavička ``Authorization: Bearer <token>``).
- **Oprávnění** závisí na konkrétním endpointu (viz detail níže); minimální podmínkou je splnění
  standardních pravidel pro zápis nálezů k projektu, včetně omezení na typ projektu průzkum.

Přihlášení a získání tokenu
---------------------------

Před voláním jakéhokoli API endpointu je nutné získat autentizační token.
Token má platnost **24 hodin**; po vypršení je nutné přihlášení zopakovat.

.. code-block:: text

    POST /api/token-auth/

**Tělo požadavku** (``application/json``):

.. code-block:: json

    {
        "username": "<uživatelské jméno>",
        "password": "<heslo>"
    }

**Odpověď** (HTTP 200):

.. code-block:: json

    {
        "token": "<váš-bearer-token>"
    }

Získaný token předávejte v hlavičce ``Authorization`` všech následujících volání:

.. code-block:: text

    Authorization: Bearer <váš-bearer-token>

**Příklad v Pythonu**:

.. code-block:: python

    import requests

    response = requests.post(
        "https://<host>/api/token-auth/",
        json={"username": "<jméno>", "password": "<heslo>"},
    )
    token = response.json()["token"]

    headers = {"Authorization": f"Bearer {token}"}

Přehled endpointů
-----------------

.. list-table::
   :header-rows: 1
   :widths: 40 10 15 35

   * - Adresa
     - Metoda
     - Vstup
     - Popis
   * - ``/api/token-auth/``
     - ``POST``
     - JSON
     - Přihlášení a získání Bearer tokenu
   * - ``/api/uzivatel-info/``
     - ``GET``
     - —
     - Vrací XML metadata přihlášeného uživatele
   * - ``/api/pas/import-xml``
     - ``POST``
     - XML soubor
     - Import nového záznamu samostatného nálezu z XML souboru ve formátu AMČR 2.2
   * - ``/api/pas/nalez/{ident_cely}/evidencni-cislo``
     - ``PATCH``
     - Query parametr
     - Aktualizace evidenčního čísla existujícího záznamu
   * - ``/api/pas/nalez/{ident_cely}/upload-foto``
     - ``POST``
     - Soubor fotografie
     - Nahrání fotografie k existujícímu záznamu

Detail endpointů
----------------

POST /api/pas/import-xml
~~~~~~~~~~~~~~~~~~~~~~~~

Vytvoří nový záznam samostatného nálezu na základě XML souboru ve formátu AMČR.
XML je validováno oproti XSD schématu a datovým pravidlům systému.
Po úspěšném importu je záznam automaticky zapsán, odeslán a potvrzen —
nález tedy vstupuje do systému přímo ve stavu **Potvrzený** (SN3).
Do historie záznamu jsou zapsány události SN-01, SN-12 a SN-23; ve všech
třech je jako poznámka uvedeno, že záznam pochází z importu z externího zdroje.

**Požadavek**

- ``Content-Type: multipart/form-data``
- Pole ``file`` — XML soubor odpovídající aktuálnímu schématu AMČR
  (např. schéma v2.2: ``https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd``).
- Dokument musí obsahovat právě jeden element ``amcr:samostatny_nalez``.
- Hlavička ``Content-Digest`` je povinná; obsahuje SHA-512 hash odesílaného souboru
  ve formátu dle RFC 9530: ``sha-512=:<base64>:``.

**Struktura elementu ``amcr:samostatny_nalez``**

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Element
     - Typ
     - Poznámka
   * - ``amcr:ident_cely``
     - ``xs:string``
     - Vždy ``:tba`` — systém jej přidělí automaticky podle platných pravidel.
   * - ``amcr:projekt``
     - ``xs:string``
     - Identifikátor projektu; ověřuje se oprávnění přihlášeného uživatele a odvozuje se ``amcr:ident_cely``.
   * - ``amcr:hloubka``
     - ``xs:integer``
     - Hloubka nálezu v centimetrech.
   * - ``amcr:okolnosti``
     - ``xs:string``
     - Hodnota z číselníku; atribut ``id`` obsahuje kód hesláře.
   * - ``amcr:obdobi``
     - ``xs:string``
     - Hodnota z číselníku; atribut ``id`` obsahuje kód hesláře.
   * - ``amcr:presna_datace``
     - ``xs:string``
     - Textový upřesňující popis datace; volitelné.
   * - ``amcr:druh_nalezu``
     - ``xs:string``
     - Hodnota z číselníku; atribut ``id`` obsahuje kód hesláře.
   * - ``amcr:specifikace``
     - ``xs:string``
     - Hodnota z číselníku; atribut ``id`` obsahuje kód hesláře.
   * - ``amcr:pocet``
     - ``xs:string``
     - Počet nálezových položek; volitelné.
   * - ``amcr:poznamka``
     - ``xs:string``
     - Volná textová poznámka; volitelné.
   * - ``amcr:nalezce``
     - ``xs:string``
     - Atribut ``id`` obsahuje identifikátor osoby z hesláře. Pokud osoba v hesláři neexistuje,
       uvede se ``id=":tba"`` a tělo elementu obsahuje jméno ve formátu ``Příjmení, Jméno`` —
       osoba bude automaticky vytvořena jako nová položka hesláře.
   * - ``amcr:datum_nalezu``
     - ``xs:date``
     - Datum nálezu ve formátu ``YYYY-MM-DD``.
   * - ``amcr:predano``
     - ``xs:boolean``
     - Příznak předání nálezu.
   * - ``amcr:predano_organizace``
     - ``xs:string``
     - Atribut ``id`` obsahuje ``ident_cely`` organizace (např. ``ORG-000123``).
   * - ``amcr:geom_system``
     - ``xs:integer``
     - EPSG kód souřadnicového systému: ``4326`` (WGS 84) nebo ``5514`` (S-JTSK).
   * - ``amcr:pristupnost``
     - ``xs:string``
     - Hodnota z číselníku; atribut ``id`` obsahuje kód hesláře.
   * - ``amcr:chranene_udaje/amcr:lokalizace``
     - ``xs:string``
     - Textový popis lokalizace nálezu.
   * - ``amcr:chranene_udaje/amcr:geom_wkt``
     - ``xs:string``
     - Použije se, pokud ``amcr:geom_system`` je ``4326``; atribut ``EPSG`` obsahuje kód souřadnicového systému.
   * - ``amcr:chranene_udaje/amcr:geom_sjtsk_wkt``
     - ``xs:string``
     - Použije se, pokud ``amcr:geom_system`` je ``5514``; atribut ``EPSG`` obsahuje kód souřadnicového systému.

U elementů s atributem ``xml:lang`` se očekává hodnota ``cs``.

Elementy odkazující na heslář (``okolnosti``, ``obdobi``, ``druh_nalezu``, ``specifikace``,
``pristupnost``) a na organizaci (``predano_organizace``) se uvádějí celé včetně textové hodnoty, protože
XML musí projít validací schématu. Pro import se využívá atribut ``id``; systém ověřuje, že zadaná
hodnota ``id`` patří do správného typu hesláře (např. nelze do pole ``obdobi`` uvést kód hesláře
pro druh nálezu). Textový obsah elementu se při importu ignoruje.

Některé elementy systém stanoví nebo generuje automaticky a v importu se ignorují nebo nejsou povoleny:

- ``amcr:okres``, ``amcr:katastr`` — určí systém automaticky podle souřadnic; v importu nejsou povoleny.
  Při ``geom_system=4326`` se katastr odvozuje z ``geom_wkt``, při ``geom_system=5514`` se ``geom_sjtsk_wkt``
  nejprve transformuje do WGS-84 a katastr se odvozuje z výsledku.
  Pokud souřadnice nespadají do žádného katastru (např. bod mimo území ČR), import selže s HTTP 422.
- ``amcr:stav`` — musí být jedna z povolených hodnot (1, 2, 3); určuje cílový stav záznamu po importu.
- ``amcr:evidencni_cislo`` — lze uvést v importu; systém hodnotu přijme a uloží.
- ``amcr:historie``, ``amcr:soubor`` — pouze pro export.

**Šablona vstupního XML**

Prvky označené v ukázce XML jako komentáře jsou při importu zcela ignorovány,
i pokud jsou v dokumentu přítomny.

.. code-block:: xml

    <?xml version="1.0" encoding="utf-8" ?>
    <amcr:amcr xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:amcr="https://api.aiscr.cz/schema/amcr/2.2/" xmlns:gml="http://www.opengis.net/gml/3.2" xsi:schemaLocation="https://api.aiscr.cz/schema/amcr/2.2/ https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd http://www.opengis.net/gml/3.2 http://schemas.opengis.net/gml/3.2.1/gml.xsd">
      <amcr:samostatny_nalez>
        <amcr:ident_cely>:tba</amcr:ident_cely>
        <amcr:evidencni_cislo>xs:string</amcr:evidencni_cislo>
        <!-- <amcr:igsn>xs:string</amcr:igsn> -->
        <amcr:projekt id="xs:string">xs:string</amcr:projekt> <!-- kontrola autorizace -->
        <!-- <amcr:okres id="xs:string" xml:lang="cs">xs:string</amcr:okres> --> <!-- stanoví se podle souřadnic automaticky -->
        <amcr:hloubka>xs:integer</amcr:hloubka>
        <amcr:okolnosti id="xs:string" xml:lang="cs">xs:string</amcr:okolnosti>
        <amcr:obdobi id="xs:string" xml:lang="cs">xs:string</amcr:obdobi>
        <amcr:presna_datace>xs:string</amcr:presna_datace>
        <amcr:druh_nalezu id="xs:string" xml:lang="cs">xs:string</amcr:druh_nalezu>
        <amcr:specifikace id="xs:string" xml:lang="cs">xs:string</amcr:specifikace>
        <amcr:pocet>xs:string</amcr:pocet>
        <amcr:poznamka>xs:string</amcr:poznamka>
        <amcr:nalezce id="xs:string">xs:string, xs:string</amcr:nalezce>
        <amcr:datum_nalezu>xs:date</amcr:datum_nalezu>
        <amcr:stav>xs:integer</amcr:stav>
        <amcr:predano>xs:boolean</amcr:predano>
        <amcr:predano_organizace id="xs:string" xml:lang="cs">xs:string</amcr:predano_organizace>
        <amcr:geom_system>xs:integer</amcr:geom_system>
        <amcr:pristupnost id="xs:string" xml:lang="cs">xs:string</amcr:pristupnost>
        <amcr:chranene_udaje>
          <!-- <amcr:katastr id="xs:string" xml:lang="cs">xs:string</amcr:katastr> --> <!-- stanoví se podle souřadnic automaticky -->
          <amcr:lokalizace>xs:string</amcr:lokalizace>
          <!-- <amcr:geom_gml><gml:*></amcr:geom_gml> -->
          <amcr:geom_wkt EPSG="xs:integer">xs:string</amcr:geom_wkt> <!-- použije se, pokud amcr:geom_system je 4326 -->
          <!-- <amcr:geom_sjtsk_gml><gml:*></amcr:geom_sjtsk_gml> -->
          <amcr:geom_sjtsk_wkt EPSG="xs:integer">xs:string</amcr:geom_sjtsk_wkt> <!-- použije se, pokud amcr:geom_system je 5514 -->
        </amcr:chranene_udaje>
        <!-- <amcr:historie><amcr:*></amcr:historie> -->
        <!-- <amcr:soubor><amcr:*></amcr:soubor> -->
      </amcr:samostatny_nalez>
    </amcr:amcr>

**Odpovědi**

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - HTTP kód
     - Popis
   * - ``201``
     - Záznam byl úspěšně vytvořen; tělo obsahuje XML metadata nového záznamu.
       Hlavička ``Location`` obsahuje PURL nového záznamu (konfigurovatelné přes secret ``OAI_PURL``).
   * - ``400``
     - Chybí soubor ``file``, neplatná syntaxe XML nebo neplatná hlavička ``Content-Digest``.
   * - ``401`` / ``403``
     - Chybí nebo neplatný token, nebo nedostatečné oprávnění.
   * - ``404``
     - Projekt zadaný v XML nebyl nalezen.
   * - ``422``
     - XML neodpovídá XSD schématu, obsahuje neplatná datová pole, chybí geometrie nebo souřadnice nespadají do žádného katastru.
   * - ``429``
     - Překročen povolený počet požadavků; zkuste to znovu za chvíli.
   * - ``503``
     - API je dočasně nedostupné.

PATCH /api/pas/nalez/{ident_cely}/evidencni-cislo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Aktualizuje pole evidenčního čísla existujícího záznamu samostatného nálezu.
Endpoint rozlišuje mezi chybějícím parametrem a parametrem s prázdnou hodnotou,
aby bylo možné oba případy na straně klienta zpracovat odlišně.
Operaci lze provést na záznamu v libovolném stavu včetně archivovaného.
Vyžaduje roli Archeolog nebo vyšší; badatel není oprávněn.

**Požadavek**

Hodnota se předává jako query parametr v URL; tělo požadavku se neposílá.

**Parametry**

- ``{ident_cely}`` (cesta) — identifikátor záznamu (např. ``M-202400001-N00001``).
- ``evidencni_cislo`` (query parametr, povinný) — nová hodnota; max. 255 znaků, nesmí být prázdná ani složená výhradně z mezer. Vedoucí a koncové mezery jsou automaticky oříznuty; vnitřní mezery jsou povoleny.

Příklad::

    PATCH /api/pas/nalez/M-202400001-N00001/evidencni-cislo?evidencni_cislo=EC-2024-001

**Odpovědi**

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - HTTP kód
     - Popis
   * - ``200``
     - Evidenční číslo bylo aktualizováno; tělo obsahuje XML metadata záznamu.
   * - ``400``
     - Chybí query parametr ``evidencni_cislo``.
   * - ``401`` / ``403``
     - Chybí nebo neplatný token, nebo nedostatečné oprávnění.
   * - ``404``
     - Záznam se zadaným ``ident_cely`` nebyl nalezen.
   * - ``422``
     - Prázdná hodnota (po oříznutí mezer), příliš dlouhá hodnota (> 255 znaků) nebo hodnota shodná s aktuální.
   * - ``429``
     - Záznam je právě zpracováván jiným požadavkem (zámek záznamu); zkuste to znovu za chvíli.

POST /api/pas/nalez/{ident_cely}/upload-foto
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Nahraje fotografii k existujícímu záznamu samostatného nálezu a připojí ji k němu.
Soubor je přijat jako binární příloha, ověřen proti poskytnutému SHA-512 digestu
a zkontrolován na povolený formát. Operaci lze provést na záznamu v libovolném stavu
včetně archivovaného; v takovém případě je v historii záznamu zaznamenána tichá rearchivace.
Badatel může nahrát fotografii ke svému nálezu podle standardních podmínek; archeolog a vyšší
role mohou nahrát fotografii k záznamu v libovolném stavu včetně archivovaného.

**Požadavek**

- ``Content-Type: multipart/form-data``
- ``{ident_cely}`` (cesta) — identifikátor záznamu samostatného nálezu.
- Pole ``file`` — soubor fotografie.
- Hlavička ``Content-Digest`` je povinná; obsahuje SHA-512 hash odesílaného souboru
  ve formátu dle RFC 9530: ``sha-512=:<base64>:``.

**Odpovědi**

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - HTTP kód
     - Popis
   * - ``201``
     - Fotografie byla nahrána; tělo obsahuje XML metadata aktualizovaného záznamu.
   * - ``400``
     - Chybí soubor ``file``, v požadavku je více než jeden soubor, chybí nebo je neplatná hlavička ``Content-Digest``.
   * - ``401`` / ``403``
     - Chybí nebo neplatný token, nebo nedostatečné oprávnění.
   * - ``404``
     - Záznam se zadaným ``ident_cely`` nebyl nalezen.
   * - ``422``
     - Nepodporovaný formát souboru, soubor je příliš velký, nesedí ``Content-Digest`` nebo je název souboru příliš dlouhý.
   * - ``429``
     - Záznam je právě zpracováván jiným požadavkem (zámek záznamu); zkuste to znovu za chvíli.
