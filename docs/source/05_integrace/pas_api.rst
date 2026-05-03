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
   * - ``/pas/api/import-xml``
     - ``POST``
     - XML soubor
     - Import nového záznamu samostatného nálezu z XML souboru ve formátu AMČR 2.2
   * - ``/pas/api/nalez/{ident_cely}/evidencni-cislo``
     - ``PATCH``
     - Query parametr
     - Aktualizace evidenčního čísla existujícího záznamu
   * - ``/pas/api/nalez/{ident_cely}/upload-foto``
     - ``POST``
     - Soubor fotografie
     - Nahrání fotografie k existujícímu záznamu

Detail endpointů
----------------

POST /pas/api/import-xml
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
     - Buď konkrétní identifikátor (záznam s ním nesmí v systému existovat), nebo ``:tba`` — v takovém případě jej systém přidělí automaticky podle platných pravidel.
   * - ``amcr:projekt``
     - ``xs:string``
     - Identifikátor projektu; ověřuje se oprávnění přihlášeného uživatele.
   * - ``amcr:hloubka``
     - ``xs:integer``
     - Hloubka nálezu v centimetrech; volitelné.
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
       osoba bude automaticky vytvořena jako nová položka hesláře. Vytvoření nové osoby vyžaduje
       oprávnění ``model_edit``.
   * - ``amcr:datum_nalezu``
     - ``xs:date``
     - Datum nálezu ve formátu ``YYYY-MM-DD``; volitelné.
   * - ``amcr:predano``
     - ``xs:boolean``
     - Příznak předání nálezu; volitelné.
   * - ``amcr:predano_organizace``
     - ``xs:string``
     - Atribut ``id`` obsahuje ``ident_cely`` organizace (např. ``ORG-000123``).
   * - ``amcr:geom_system``
     - ``xs:integer``
     - Kód souřadnicového systému: ``4326`` (WGS 84) nebo ``5514`` (S-JTSK).
   * - ``amcr:pristupnost``
     - ``xs:string``
     - Hodnota z číselníku; atribut ``id`` obsahuje kód hesláře.
   * - ``amcr:chranene_udaje/amcr:lokalizace``
     - ``xs:string``
     - Textový popis lokalizace nálezu; volitelné.
   * - ``amcr:chranene_udaje/amcr:geom_wkt``
     - ``xs:string``
     - Použije se, pokud ``amcr:geom_system`` je ``4326``; atribut ``EPSG`` obsahuje kód souřadnicového systému.
   * - ``amcr:chranene_udaje/amcr:geom_sjtsk_wkt``
     - ``xs:string``
     - Použije se, pokud ``amcr:geom_system`` je ``5514``; atribut ``EPSG`` obsahuje kód souřadnicového systému.

U elementů s atributem ``xml:lang`` se očekává hodnota ``cs``; atribut lze vynechat.

Elementy odkazující na heslář (``okolnosti``, ``obdobi``, ``druh_nalezu``, ``specifikace``,
``pristupnost``) a na organizaci (``predano_organizace``) se uvádějí celé včetně textové hodnoty, protože
XML musí projít validací schématu. Pro import se využívá atribut ``id``; systém ověřuje, že zadaná
hodnota ``id`` patří do správného typu hesláře (např. nelze do pole ``obdobi`` uvést kód hesláře
pro druh nálezu). Textový obsah elementu se při importu ignoruje.

Elementy ``amcr:stav``, ``amcr:historie`` a ``amcr:soubor`` jsou v importu zakázány nebo
se stanoví automaticky:

- ``amcr:okres``, ``amcr:katastr`` — určí systém automaticky podle souřadnic; v importu nejsou povoleny.
  Při ``geom_system=4326`` se katastr odvozuje z ``geom_wkt``, při ``geom_system=5514`` se ``geom_sjtsk_wkt``
  nejprve transformuje do WGS-84 a katastr se odvozuje z výsledku.
  Pokud souřadnice nespadají do žádného katastru (např. bod mimo území ČR), import selže s HTTP 422.
- ``amcr:stav`` — přiděluje systém; v importu není povolen.
- ``amcr:igsn``, ``amcr:evidencni_cislo`` — lze uvést v importu; systém hodnoty přijme a uloží.
- ``amcr:historie``, ``amcr:soubor`` — pouze pro export.

Prvky označené v XSD ukázce jako komentáře jsou při importu zcela ignorovány,
i pokud jsou v dokumentu přítomny.

**Odpovědi**

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - HTTP kód
     - Popis
   * - ``200``
     - Záznam byl úspěšně vytvořen; tělo obsahuje XML metadata nového záznamu.
       (Endpoint vrací ``200`` i při vytvoření záznamu, nikoliv ``201``.)
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

PATCH /pas/api/nalez/{ident_cely}/evidencni-cislo
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
- ``evidencni_cislo`` (query parametr, povinný) — nová hodnota; max. 255 znaků, nesmí být prázdná.

Příklad::

    PATCH /pas/api/nalez/M-202400001-N00001/evidencni-cislo?evidencni_cislo=EC-2024-001

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
     - Prázdná hodnota, příliš dlouhá hodnota (> 255 znaků) nebo hodnota shodná s aktuální.

POST /pas/api/nalez/{ident_cely}/upload-foto
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Nahraje fotografii k existujícímu záznamu samostatného nálezu a připojí ji k němu.
Soubor je přijat jako binární příloha, ověřen proti poskytnutému SHA-512 digestu
a zkontrolován na povolený formát. Operaci lze provést na záznamu v libovolném stavu
včetně archivovaného; v takovém případě je v historii záznamu zaznamenána tichá rearchivace.
Vyžaduje roli Archeolog nebo vyšší; badatel není oprávněn.

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
   * - ``200``
     - Fotografie byla nahrána; tělo obsahuje XML metadata aktualizovaného záznamu.
   * - ``400``
     - Chybí soubor ``file`` nebo neplatná hlavička ``Content-Digest``.
   * - ``401`` / ``403``
     - Chybí nebo neplatný token, nebo nedostatečné oprávnění.
   * - ``404``
     - Záznam se zadaným ``ident_cely`` nebyl nalezen.
   * - ``422``
     - Nepodporovaný formát souboru nebo soubor je příliš velký.
