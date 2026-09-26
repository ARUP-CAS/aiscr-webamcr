PAS API — příjem a zpracování záznamů samostatných nálezů
=========================================================

Tato stránka popisuje, jak AMČR zpracovává požadavky **PAS API** — rozhraní, jehož
prostřednictvím externí aplikace zakládají samostatné nálezy, aktualizují jejich evidenční
čísla a připojují k nim fotografie. Je určena vývojářům a správcům AMČR a integrátorům, kteří
potřebují rozumět chování serveru hlouběji, než jak jej popisuje veřejná reference.

.. note::

   **Referenční popis rozhraní** — endpointy, struktura importního XML, stavové kódy, limity
   a příklady volání — je veden v angličtině na webu AMCR API:
   `AMCR-PAS API <https://arup-cas.github.io/aiscr-api-home/pas-api/>`__.
   Tato stránka jej neopakuje a zaměřuje se na to, co se děje uvnitř aplikace.

Rozhraní vzniklo spolu s integrací AMČR a sbírkového systému **MUSEION** (Axiell) v rámci
projektu PRAK-25-45. MUSEION je jeho prvním a referenčním klientem, rozhraní však není na
MUSEION vázáno: je otevřené jakémukoli integrátorovi s odpovídajícím účtem a oprávněními,
například dalším sbírkovým systémům nebo aplikacím pro evidenci nálezů v terénu.

Implementace je v modulu ``webclient/api/`` (``views.py``, ``urls.py``, ``models.py``);
podrobný popis tříd a metod je v :doc:`/04_django_aplikace/04_02_moduly/api/views`.


Pořadí kontrol požadavku
------------------------

Všechny tři endpointy PAS API (``import-xml``, ``evidencni-cislo``, ``upload-foto``) sdílejí
společný základ ``PasApiBaseView``: stejnou autentizaci, přístupová pravidla i omezení četnosti.
Kontroly probíhají v tomto pořadí; požadavek, který některou nesplní, dál nepokračuje.

.. mermaid::
   :align: center

   flowchart TD
       R["Požadavek na /api/pas/..."] --> M{"access_mode = closed?"}
       M -- ano --> E503["503"]
       M -- ne --> A{"Platný Bearer token?"}
       A -- ne --> E401["401"]
       A -- ano --> P{"Přístupová pravidla<br/>IP a uživatel, access_mode"}
       P -- zamítnuto --> E403["403"]
       P -- povoleno --> T{"Omezení četnosti<br/>min. interval, rate_limits"}
       T -- překročeno --> E429a["429 + Retry-After"]
       T -- povoleno --> L["Založení záznamu ApiRequestLog"]
       L --> H["Kontrola vstupu a oprávnění k záznamu"]
       H --> Z{"Zámek záznamu?<br/>jen PATCH a fotografie"}
       Z -- nezískán --> E429b["429 bez Retry-After"]
       Z -- získán, nebo import --> O["Validace a zápis<br/>databáze a Fedora"]
       O --> S["200 / 201"]

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Vrstva
     - Chování
   * - ``dispatch`` (režim ``closed``)
     - Vrací ``503`` ještě před autentizací, aby uzavřené API nevypadalo jako chyba oprávnění.
   * - ``IsAuthenticated``
     - Token ``TokenAuthenticationBearer``; chybějící nebo neplatný token vrací ``401``.
   * - ``IpBlacklistPermission``
     - Zamítne IP adresy z aktivních pravidel ``ip_blacklist`` — **v každém režimu**.
   * - ``ApiAccessModePermission``
     - ``open`` propustí vše; ``whitelist_only`` vyžaduje alespoň jedno aktivní whitelist pravidlo.
   * - ``IpWhitelistPermission``, ``UserWhitelistPermission``
     - Uplatní se **jen v režimu** ``whitelist_only``; každá třída propustí požadavek, pokud pro
       svůj typ nemá žádné aktivní pravidlo.
   * - ``UserBlacklistPermission``
     - Zamítne uživatele z aktivních pravidel ``user_blacklist`` (porovnává se e-mail účtu).
   * - ``ApiImportThrottle``
     - Omezení četnosti; viz :ref:`pas-api-throttling`.

Záznam ``ApiRequestLog`` zakládá až obslužná metoda endpointu. Požadavky odmítnuté v předchozích
vrstvách (``503``, ``401``, ``403`` z přístupových pravidel, ``429`` z omezení četnosti) se do něj
**nezapisují**; zachycuje je pouze aplikační log.


Import samostatného nálezu
--------------------------

``POST /api/pas/import-xml`` (``SamostatnyNalezXmlImportView``) zpracovává jeden dokument
v tomto sledu:

#. **Příjem souboru.** Chybějící pole ``file`` vrací ``400``. Hlavička ``Content-Digest`` se ověřuje
   proti SHA-512 bajtů nahraného souboru (nikoli celého multipart těla); chybějící, nevalidní
   i neshodný digest vrací u importu ``400``.
#. **Parsování.** XML se čte bez DTD, bez rozvíjení entit a bez síťového přístupu; syntaktická
   chyba vrací ``400``.
#. **Deklarace schématu.** Namespace ``amcr`` i odpovídající položka ``xsi:schemaLocation`` musí
   přesně odpovídat schématu, které aplikace podporuje (konstanty ``AMCR_NAMESPACE_URL``
   a ``AMCR_XSD_URL`` v ``xml_generator.generator``, aktuálně verze 2.2). Nastavení
   ``allowed_schema_versions`` může povolené verze dále zúžit, **nepřidá však verzi**, kterou kód
   nepodporuje — podpora nové verze schématu vyžaduje změnu kódu. Nesoulad vrací ``422``.
#. **Validace proti XSD.** Schéma se načítá ze sítě, viz :ref:`pas-api-xsd`. Chyby se vracejí
   v poli ``schema_errors`` se stavem ``422``.
#. **Kořen dokumentu.** Prázdný kořen ``amcr:amcr`` vrací ``400``, více elementů
   ``amcr:samostatny_nalez`` ``422`` a jakýkoli jiný obsah kořene rovněž ``422``. Od tohoto bodu
   má záznam ``ApiRequestLog`` stav ``processing``.
#. **Převod elementů** (``_parse_nalez_element``):

   - Hesla a organizace se určují **podle atributu** ``id``; serializer ověřuje, že identifikátor
     patří do správného hesláře (například období nelze zadat heslem druhu nálezu). Text elementu
     a atribut ``xml:lang`` se nepoužívají; ignorovaný jazyk se zaznamená do logu.
   - ``nalezce`` s ``id=":tba"``: text ve tvaru ``Příjmení, Jméno`` se nejprve hledá mezi
     existujícími osobami (shoda příjmení a jména); **teprve pokud osoba neexistuje**, připraví se
     nová a uloží se ve stejné transakci jako nález. Chybný formát vrací ``422``.
   - Geometrie musí být **bod** (WKT ``POINT``). ``geom_system`` (v XSD ``xs:string``) určuje
     zdroj: ``4326`` čte ``geom_wkt`` (pořadí délka, šířka), ``5514`` čte ``geom_sjtsk_wkt``;
     druhá reprezentace se dopočítá a zdrojová reprezentace druhého systému se ignoruje.
   - Ignorují se ``okres``, ``chranene_udaje/katastr``, ``igsn``, ``geom_updated_at``,
     ``geom_sjtsk_updated_at``, ``geom_gml``, ``geom_sjtsk_gml``, ``historie`` a ``soubor``;
     identifikátor ``ident_cely`` přiděluje systém bez ohledu na zadanou hodnotu.

#. **Projekt a oprávnění.** Neexistující projekt vrací ``404``. Oprávnění (``_has_import_permissions``)
   vyžaduje cílový stav 1–3, u badatele nejvýše stav 1, a projekt z množiny
   ``Projekt.get_pruzkum_projekty_pro_uzivatele`` — tedy průzkumný projekt dostupný danému
   uživateli. Jinak ``403``.
#. **Zápis v transakci.** V databázové transakci spojené s Fedora transakcí se uloží případná nová
   osoba, data projdou serializerem, přidělí se ``ident_cely`` (``get_sn_ident``) a uplatní se
   pravidla podle cílového stavu:

   - od stavu 2 je povinná geometrie;
   - stav 3 navíc vyžaduje ``evidencni_cislo``, ``predano`` s hodnotou ``true``
     a ``predano_organizace`` (pravidla převzatá z ``pas.forms.PotvrditNalezForm``);
   - katastr se určí z bodu WGS 84 (u S-JTSK po transformaci); bod mimo všechna katastrální
     území vrací ``422``;
   - pro stavy 2 a 3 proběhnou kontroly ``check_pred_odeslanim``, pro stav 3 též
     ``check_pred_potvrzenim`` — obě **s vynechanou kontrolou souborů**, protože fotografie se
     nahrávají samostatným endpointem.

   Nakonec se záznam uloží a vytvoří se záznamy historie (viz :ref:`pas-api-stavy`).
#. **Ověření zápisu ve Fedoře.** Po potvrzení databázové transakce se metadata záznamu načtou zpět
   z Fedory v rámci téže Fedora transakce a transakce se uzavře. Pokud čtení selže, Fedora
   transakce se vrátí a endpoint vrátí ``500`` — **záznam v databázi však už existuje**. Proto
   veřejná reference klientům ukládá, aby po chybě ``500`` nebo vypršení spojení ověřili výsledek
   dříve, než import zopakují.
#. **Odpověď.** ``201`` s XML metadaty, hlavičkou ``X-Record-ID`` (přidělený ``ident_cely``)
   a ``Location`` (``OAI_PURL`` + ``ident_cely``, výchozí ``https://api.aiscr.cz/id/``).

Import nepoužívá zámek záznamu: každé úspěšné volání zakládá nový záznam. Opakovaný import téhož
nálezu proto vytvoří duplicitu.


.. _pas-api-stavy:

Stavy a historie záznamu
------------------------

Import zakládá záznam přímo v cílovém stavu 1, 2 nebo 3 a zapíše do historie všechny přechody,
které by v aplikaci vedly do tohoto stavu. Každý z nich nese poznámku, že záznam pochází
z importu z externího zdroje. Stav 4 (archivovaný) přes API nastavit nelze; archivaci provádějí
archiváři AMČR a nález k ní musí mít nahrané fotografie.

.. mermaid::
   :align: center

   stateDiagram-v2
       direction LR
       state "1 zapsaný" as SN1
       state "2 odeslaný" as SN2
       state "3 potvrzený" as SN3
       state "4 archivovaný" as SN4
       [*] --> SN1: import stav 1 — SN01
       [*] --> SN2: import stav 2 — SN01, SN12
       [*] --> SN3: import stav 3 — SN01, SN12, SN23
       SN1 --> SN2: odeslání — SN12
       SN2 --> SN3: potvrzení — SN23
       SN3 --> SN4: archivace v AMČR — SN34

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Kód
     - Kdy vzniká přes API
   * - ``SN01``, ``SN12``, ``SN23``
     - Při importu, podle cílového stavu (``_create_import_history_records``).
   * - ``SN-UPD``
     - Při aktualizaci evidenčního čísla; poznámka obsahuje původní a novou hodnotu.
   * - ``SN34``
     - Tichá rearchivace, když se evidenční číslo nebo fotografie mění u archivovaného záznamu.


Aktualizace evidenčního čísla
-----------------------------

``PATCH /api/pas/nalez/{ident_cely}/evidencni-cislo`` (``SamostatnyNalezEvidencniCisloPatchView``):

#. Chybějící query parametr ``evidencni_cislo`` vrací ``400``. Hodnota se ořízne o okrajové
   mezery; prázdná nebo delší než 255 znaků (limit rozhraní, model pole nemá) vrací ``422``.
#. Neexistující záznam vrací ``404``. Oprávnění vyžaduje ``pas_edit`` pro daný záznam
   s ``skip_status=True`` (tedy v libovolném stavu včetně archivovaného) **a** hlavní roli
   archeolog nebo vyšší; badatel oprávnění nemá. Jinak ``403``.
#. Hodnota shodná s aktuálním evidenčním číslem vrací ``422``.
#. Získání :ref:`zámku záznamu <pas-api-zamek>`; při neúspěchu ``429``.
#. Uložení hodnoty, záznam ``SN-UPD`` do historie; u archivovaného záznamu navíc ``SN34``
   a aktualizace metadat IGSN.
#. ``200`` s XML metadaty a hlavičkami ``X-Record-ID`` a ``Location``.


Nahrání fotografie
------------------

``POST /api/pas/nalez/{ident_cely}/upload-foto`` (``SamostatnyNalezFotografieUploadView``):

#. Neexistující záznam ``404``. Oprávnění ``soubor_nahrat_pas``: archeolog a vyšší role
   s ``skip_status=True`` (libovolný stav včetně archivovaného), badatel podle standardních
   pravidel AMČR (typicky vlastní nález ve stavu 1). Jinak ``403``.
#. Právě jeden soubor v poli ``file``; chybějící nebo více souborů vrací ``400``.
#. Velikost nejvýše ``MAX_PAS_API_FOTOGRAFIE_FILE_SIZE_BYTES`` (250 MiB); šifrovaný soubor nebo
   nepodporovaný MIME typ ``422``.
#. ``Content-Digest`` nad bajty souboru; chybějící nebo nevalidní hlavička ``400``, **neshoda
   digestu zde vrací** ``422``.
#. Antivirová kontrola: nalezený virus ``422``, nedokončená kontrola ``500``.
#. Získání :ref:`zámku záznamu <pas-api-zamek>`; při neúspěchu ``429``.
#. Přípona se odvodí z MIME typu a soubor se přejmenuje podle pravidel pro soubory nálezů
   (``get_finds_soubor_name``); neúspěch vrací ``422``. U formátů JPEG, PNG a TIFF se
   **odstraní GPS metadata**.
#. Uložení do Fedory; u archivovaného záznamu ``SN34`` a aktualizace IGSN.
#. ``201`` s aktualizovanými XML metadaty záznamu.


.. _pas-api-zamek:

Zámek záznamu
-------------

Zámek chrání PATCH a nahrání fotografie nad týmž ``ident_cely`` před souběžnými změnami. Import jej
nepoužívá.

- Klíč v Redis cache má tvar ``pas_api_record_lock_<ident_cely>``; hodnota ``1`` znamená zamčeno,
  ``0`` uvolněno.
- ``_acquire_record_lock`` zkouší zámek získat nejvýše ``max_retries``-krát s prodlevou
  ``retry_delay`` (nastavení ``record_lock_params``). Kdo zámek nezíská, dostane ``429``
  s polem ``detail`` a **bez** hlavičky ``Retry-After``.
- Zámek vyprší nejpozději po ``record_lock_ttl`` sekundách, takže záznam nezůstane zamčený, pokud
  pracovní proces spadne.

.. warning::

   Zámek poskytuje **serializaci „best effort“**, nikoli striktní záruku. První získání klíče je
   atomické (``cache.add``), ale opětovné převzetí uvolněného klíče (hodnota ``0``) probíhá čtením
   a zápisem, které atomické nejsou; vlákna serializuje ``threading.Lock`` jen v rámci jednoho
   pracovního procesu. Dva procesy tak mohou výjimečně získat zámek současně. Testy souběhu
   v ``test_record_lock_cache.py`` začínají se smazaným klíčem, a pokrývají tedy jen atomické
   první získání.


.. _pas-api-throttling:

Omezení četnosti
----------------

``ApiImportThrottle`` platí pro všechny tři endpointy a vyhodnocuje dva mechanismy; požadavek
projde, jen pokud splní oba:

- **Minimální interval** (``min_request_intervals``) mezi požadavky téhož uživatele a téže IP
  adresy. Porovnává se časová značka posledního povoleného požadavku, takže interval 100 ms
  znamená rozestup, nikoli povolení k dávce deseti požadavků za sekundu.
- **Limity** ``rate_limits`` s pevným časovým oknem pro rozsahy ``user``, ``ip`` a ``record``.
  Rozsah ``record`` je klíčován ``ident_cely`` z URL a sdílí se mezi endpointy, takže jej nelze
  obejít střídáním PATCH a nahrání fotografie.

Překročení vrací ``429``; čekací doba z ``wait()`` se promítne do hlavičky ``Retry-After``.
Poškozený limit (nečitelná hodnota ``rate``) se vyhodnotí jako překročený (**fail closed**)
a odpověď pak ``Retry-After`` nenese. Uživatel se identifikuje e-mailem účtu, IP adresa podle
``get_client_ip`` (viz ``trusted_proxies`` níže).


.. _pas-api-xsd:

Načítání XSD schématu
---------------------

``_get_amcr_schema`` stahuje XSD deklarované v ``xsi:schemaLocation`` a všechna schémata, která
importuje (W3C ``xml.xsd``, GML). Síťové čtení je povoleno jen pro URL z pevného allowlistu
(``_ALLOWED_SCHEMA_URL_PATTERNS``, ``_ALLOWED_XML_XSD_URLS``); jiné URL import odmítne s ``422``.
Chrání to server před podvržením schématu a před požadavky na libovolné adresy (SSRF).

- Bajty XSD se ukládají do paměti procesu a do Redis (``schema_cache_ttl``); zkompilované schéma
  si proces drží po dobu ``schema_cache_ttl``. Paměťová kopie bajtů nemá expiraci, takže
  **změna publikovaného XSD se v pracovním procesu projeví až po jeho restartu**.
- Místní kopie schémat se záměrně nebalí. Pokud je zdroj schématu nedostupný (časový limit
  ``schema_fetch_timeout``), import vrací ``422``. Dostupnost ``api.aiscr.cz/schema/`` je proto
  provozní podmínkou importu.


Konfigurace
-----------

Chování PAS API řídí záznamy modelu ``CustomAdminSettings`` ve skupině ``pas_api``, spravované
v administraci Django. Hodnota ``value`` je JSON. Při uložení záznam validuje
``CustomAdminSettings.clean()`` (``validate_custom_admin_setting``) a signály ``post_save``
a ``post_delete`` vymažou cache, takže změna platí **okamžitě**. Jinak se hodnoty drží v cache
po dobu ``cache_ttl``.

.. list-table::
   :header-rows: 1
   :widths: 22 30 18 30

   * - ``item_id``
     - Formát
     - Bez záznamu
     - Poznámka
   * - ``access_mode``
     - ``"open"``, ``"whitelist_only"``, ``"closed"``
     - ``open``
     - ``closed`` vrací ``503``; ``whitelist_only`` bez aktivního whitelist pravidla zamítne vše.
   * - ``access_rules``
     - seznam ``{rule_type, value, active}``; typy ``ip_blacklist``, ``ip_whitelist``,
       ``user_blacklist``, ``user_whitelist``
     - žádná pravidla
     - IP jako adresa nebo CIDR (IPv4 i IPv6), případně rozsah ``od-do`` (jen IPv4); uživatel
       e-mailem. ``active`` výchozí ``true``.
   * - ``trusted_proxies``
     - seznam CIDR, IP nebo DNS názvů
     - ``[]``
     - Hlavička ``X-Forwarded-For`` se čte jen tehdy, je-li ``REMOTE_ADDR`` důvěryhodný;
       zprava doleva se vrátí první nedůvěryhodná adresa.
   * - ``rate_limits``
     - seznam ``{scope, value, rate, active}``; ``rate`` ve tvaru ``počet/jednotka``
       s jednotkami ``ms``, ``s``, ``m``, ``h``, ``d``
     - žádné limity
     - ``value`` je povinné pro ``user`` a ``ip``.
   * - ``min_request_intervals``
     - ``{"user_ms": …, "ip_ms": …}``
     - vypnuto
     - Hodnota ``0`` daný limit vypíná.
   * - ``record_lock_params``
     - ``{"retry_delay": …, "max_retries": …}``
     - 0,5 s, 10 pokusů
     -
   * - ``record_lock_ttl``
     - celé číslo (s)
     - 300
     -
   * - ``allowed_schema_versions``
     - seznam čísel, např. ``[2.2]``
     - bez omezení
     - Jen zužuje verze podporované kódem.
   * - ``cache_ttl``
     - celé číslo (s)
     - 3600
     - Platnost cache nastavení.
   * - ``schema_fetch_timeout``
     - celé číslo (s)
     - 10
     -
   * - ``schema_cache_ttl``
     - celé číslo (s)
     - 3600
     -

Provozní upozornění
~~~~~~~~~~~~~~~~~~~

- **Vzorová pravidla** ``access_rules`` s hodnotami ``0.0.0.0/0`` nebo ukázkovým e-mailem slouží
  jako šablona. Při potřebě omezení je nahraďte skutečnými hodnotami, nepřepínejte jen
  ``active``: aktivní ``ip_blacklist`` s ``0.0.0.0/0`` zablokuje všechny klienty IPv4 v každém
  režimu, a v režimu ``whitelist_only`` by aktivní vzorové ``user_whitelist`` pravidlo propustilo
  jen neexistující účet.
- **Nastavení** ``trusted_proxies`` musí odpovídat skutečné síťové topologii. Není-li reverzní
  proxy důvěryhodná, považuje se za klienta její adresa — IP pravidla i omezení četnosti podle IP
  pak sdílí všichni klienti společně.
- **Bez záznamu** ``min_request_intervals`` není minimální interval aktivní vůbec.


Auditní záznam ``ApiRequestLog``
--------------------------------

Každý požadavek, který dojde do obslužné metody endpointu, zanechá záznam ``ApiRequestLog``
(``webclient/api/models.py``), dostupný v administraci Django:

- ``request_target`` — ``samostatny_nalez_xml_import``, ``samostatny_nalez_evidencni_cislo_patch``
  nebo ``samostatny_nalez_fotografie_upload``;
- ``status`` — ``received``, ``processing``, ``success``, ``failure``;
- ``user``, ``client_ip``, ``received_at``, ``finished_at``, ``filename``, ``file_size``;
- ``ident_cely`` a vazba ``samostatny_nalez`` u úspěšných operací; ``errors`` s tělem chybové odpovědi.

Záznamy slouží k dohledání jednotlivých operací a zároveň jako ukazatel využívání integrace na
straně zápisu: počty operací podle cíle a výsledku. Neobsahují požadavky odmítnuté před
obslužnou metodou (viz `Pořadí kontrol požadavku`_).


Mapování slovníků
-----------------

Předpokladem exportu je, že klient spáruje své slovníky s hesláři AMČR. Hesláře poskytuje od
počátku OAI-PMH API v sadách ``heslo:*``; postup pro integrátory popisuje veřejná reference
v části `Vocabulary mapping <https://arup-cas.github.io/aiscr-api-home/pas-api/#vocabulary-mapping>`__.
Import pak hesla určuje výhradně podle jejich identifikátorů (viz převod elementů výše).


Testy
-----

Testy PAS API jsou v ``webclient/api/tests/``: ``test_api.py`` (endpointy), ``test_api_permissions.py``
(přístupová pravidla, omezení četnosti a validace nastavení), ``test_record_lock_cache.py`` (zámek
záznamu) a ``test_models.py``. Vzorové importní dokumenty jsou v ``webclient/api/tests/data/``;
například ``minimal_nalez_stav1_no_geom.xml`` je nejmenší dokument, který import přijme.


Související dokumentace
-----------------------

- `AMCR-PAS API <https://arup-cas.github.io/aiscr-api-home/pas-api/>`__ — veřejná reference rozhraní (anglicky).
- :doc:`export_structure` — struktura XML podle schématu AMČR.
- :doc:`/04_django_aplikace/04_02_moduly/api/views` — referenční popis modulu ``api.views``.
- `Příručky systému MUSEION <https://doc.axiell.cz/prirucky/>`__ — dokumentace referenčního
  klienta, včetně příručky integrace s AMČR a popisu služby ``NalezyAmcrService``.
