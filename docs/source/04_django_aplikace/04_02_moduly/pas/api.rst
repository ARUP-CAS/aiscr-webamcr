PAS api
=======

Modul api.

Třídy
------

.. py:class:: PasApiPermissionMixin

   Sdílené helpery pro permission a throttle logiku PAS XML API.

   **Metody:**

   .. py:method:: _resolve_trusted_networks()

      Přeloží seznam IP adres, CIDR rozsahů nebo DNS názvů na seznam ``ipaddress.IPv4Network`` objektů.

      Výsledky jsou uloženy v cache po dobu ``_trusted_proxy_resolve_ttl`` sekund. Pro Docker service
      jméno (např. ``"proxy"``) se IP adresa zjišťuje přes DNS pomocí ``socket.getaddrinfo``.

      :param entries: Seznam CIDR řetězců, IP adres nebo DNS názvů.

      :return: Seznam ``ipaddress.IPv4Network`` (nebo ``IPv6Network``) objektů.

   .. py:method:: load_json_setting()

      Načte JSON hodnotu z ``CustomAdminSettings`` pro skupinu ``pas_api``.

      Nastavení se konfiguruje v Django administraci přes model ``CustomAdminSettings``
      (skupina ``pas_api``). Každý záznam musí mít pole ``value`` obsahující platný JSON.

      Podporované záznamy:

      ``access_rules`` (``item_id="access_rules"``)
          Seznam pravidel přístupu. Každé pravidlo je objekt s klíči:

          - ``rule_type`` *(povinný)* — typ pravidla; povolené hodnoty:
            ``"ip_blacklist"``, ``"ip_whitelist"``, ``"user_blacklist"``, ``"user_whitelist"``
          - ``value`` *(povinný)* — IP adresa, IP rozsah (např. ``"192.168.1.1-192.168.1.5"``),
            CIDR rozsah (např. ``"192.168.1.0/24"``) nebo uživatelské jméno podle ``rule_type``
          - ``active`` *(volitelný, výchozí* ``true``*)* — ``false`` pravidlo dočasně deaktivuje

          Příklad::

              [
                {"rule_type": "ip_blacklist", "value": "1.2.3.4"},
                {"rule_type": "ip_whitelist", "value": "10.0.0.0/8"},
                {"rule_type": "user_blacklist", "value": "jan.novak", "active": false}
              ]

      ``rate_limits`` (``item_id="rate_limits"``)
          Seznam limitů počtu požadavků. Každý limit je objekt s klíči:

          - ``scope`` *(povinný)* — rozsah pravidla; povolené hodnoty: ``"user"``, ``"ip"``
          - ``value`` *(povinný)* — uživatelské jméno nebo IP adresa, IP rozsah,
            CIDR rozsah
          - ``rate`` *(povinný)* — limit ve formátu ``"počet/jednotka"``;
            jednotky: ``s`` (sekunda), ``m`` (minuta), ``h`` (hodina), ``d`` (den);
            např. ``"10/m"``, ``"100/h"``, ``"1000/d"``
          - ``active`` *(volitelný, výchozí* ``true``*)* — ``false`` limit dočasně deaktivuje

          Příklad::

              [
                {"scope": "user", "value": "jan.novak", "rate": "10/m"},
                {"scope": "ip", "value": "203.0.113.0/24", "rate": "50/h"}
              ]

      ``access_mode`` (``item_id="access_mode"``)
          Režim globální dostupnosti API. Podporované hodnoty:

          - ``"open"`` — API je otevřené; whitelist pravidla se neaplikují
          - ``"whitelist_only"`` — API je dostupné pouze přes whitelist pravidla
          - ``"closed"`` — API je úplně uzavřené

          Příklad::

              "whitelist_only"

      ``trusted_proxies`` (``item_id="trusted_proxies"``)
          Seznam důvěryhodných proxy serverů stojících před aplikací.
          Každá položka je CIDR řetězec, IP adresa nebo DNS název (např. Docker service jméno).
          Používá se pro správné určení IP adresy klienta z hlavičky ``X-Forwarded-For``.
          Pokud nastavení chybí, použije se výchozí hodnota ``["10.0.1.0/24"]``.

          Příklad::

              ["10.0.1.0/24", "proxy"]

      Změny v administraci se projeví do ``30`` sekund (TTL cache).

      :param item_id: Identifikátor záznamu — ``"access_rules"``, ``"rate_limits"`` nebo ``"access_mode"``.

      :param raise_validation_error: Pokud je ``True`` (výchozí), nevalidní JSON vyhodí ``ValidationError``.

      :return: Naparsovaná JSON hodnota nebo ``[]`` při chybě či absenci záznamu.

   .. py:method:: get_access_rules()

      Vrátí přístupová pravidla API z cache nebo ``CustomAdminSettings``.

      Každé pravidlo je slovník s klíči ``rule_type``, ``value`` a volitelně ``active`` (výchozí ``True``).

      :raises ValidationError: Pokud nastavení nemá očekávanou strukturu nebo obsahuje nevalidní pravidlo.
      :return: Seznam aktivních pravidel.

   .. py:method:: validate_access_rules()

      Ověří strukturu a obsah nastavení ``access_rules``.

      :param raw_rules: Naparsovaná JSON hodnota nastavení ``access_rules``.

      :raises ValidationError: Pokud struktura nebo obsah pravidel neodpovídá očekávání.
      :return: ``True`` pokud je nastavení validní.

   .. py:method:: validate_custom_admin_setting()

      Ověří ``CustomAdminSettings`` záznam relevantní pro PAS API před uložením.

      Pokud jde o skupinu ``pas_api``, ověří platnost ``item_id`` a podle něj
      validuje JSON hodnotu příslušným validátorem.

      :param instance: Ukládaný záznam ``CustomAdminSettings``.

      :raises ValidationError: Pokud ``item_id`` není podporováno nebo JSON/struktura hodnoty nejsou validní.
      :return: ``True`` pokud je záznam validní nebo se na něj validace nevztahuje.

   .. py:method:: get_rate_limits()

      Vrátí limity počtu požadavků z cache nebo ``CustomAdminSettings``.

      Každý limit je slovník s klíči ``scope``, ``value``, ``rate`` a volitelně ``active`` (výchozí ``True``).

      :raises ValidationError: Pokud nastavení nemá očekávanou strukturu nebo obsahuje nevalidní limit.
      :return: Seznam aktivních limitů.

   .. py:method:: validate_rate_limits()

      Ověří strukturu a obsah nastavení ``rate_limits``.

      :param raw_limits: Naparsovaná JSON hodnota nastavení ``rate_limits``.

      :raises ValidationError: Pokud struktura nebo obsah limitů neodpovídá očekávání.
      :return: ``True`` pokud je nastavení validní.

   .. py:method:: get_access_mode()

      Vrátí globální režim dostupnosti PAS XML API.

      Hodnota se načítá z ``CustomAdminSettings`` (``pas_api/access_mode``) a kešuje se.
      Neplatná nebo chybějící hodnota znamená výchozí režim ``open``.

      :raises ValidationError: Pokud nastavení neobsahuje podporovanou hodnotu.
      :return: Jeden z režimů ``open``, ``whitelist_only`` nebo ``closed``.

   .. py:method:: validate_access_mode()

      Ověří hodnotu nastavení ``access_mode``.

      :param value: Naparsovaná JSON hodnota nastavení ``access_mode``.

      :raises ValidationError: Pokud hodnota není jedním z podporovaných režimů.
      :return: ``True`` pokud je hodnota validní.

   .. py:method:: get_trusted_proxies()

      Vrátí seznam důvěryhodných proxy serverů z cache nebo ``CustomAdminSettings``.

      Pokud nastavení ``trusted_proxies`` neexistuje, vrátí výchozí hodnotu
      ``["10.0.1.0/24"]``.

      :raises ValidationError: Pokud nastavení má neplatnou strukturu.
      :return: Seznam řetězců — CIDR rozsahy, IP adresy nebo DNS názvy.

   .. py:method:: validate_trusted_proxies()

      Ověří strukturu nastavení ``trusted_proxies``.

      Každá položka musí být neprázdný řetězec. Hodnoty CIDR rozsahů jsou ověřeny
      pomocí ``ipaddress.ip_network``; ostatní řetězce jsou považovány za DNS názvy
      a v administraci jsou přijaty bez DNS lookup (ten probíhá za běhu).

      :param raw_proxies: Naparsovaná JSON hodnota nastavení ``trusted_proxies``.

      :raises ValidationError: Pokud struktura nebo obsah neodpovídá očekávání.
      :return: ``True`` pokud je nastavení validní.

   .. py:method:: get_client_ip()

      Vrátí IP adresu klienta z požadavku.

      Prochází hlavičku ``X-Forwarded-For`` zprava doleva a přeskakuje IP adresy
      důvěryhodných proxy serverů (z nastavení ``pas_api/trusted_proxies``).
      První nedůvěryhodná IP adresa je vrácena jako adresa klienta.

      Pokud hlavička chybí nebo jsou všechny položky důvěryhodné, vrátí ``REMOTE_ADDR``.

      :param request: HTTP požadavek.

      :return: IP adresa klienta jako řetězec.

   .. py:method:: get_user_identifier()

      Vrátí identifikátor uživatele použitelný pro access-rules a rate-limity.

      Projekt používá vlastní model uživatele s ``USERNAME_FIELD = "email"``.
      Pro kompatibilitu helper preferuje ``email`` a fallbackuje na ``username``.

      :param user: Uživatel navázaný na požadavek.

      :return: Email, username nebo ``None`` pro neautentizovaného uživatele.

   .. py:method:: ip_matches()

      Porovná IP adresu klienta s konkrétní adresou, IP rozsahem nebo CIDR rozsahem.

      :param client_ip: IP adresa klienta.
      :param pattern: IP adresa, IP rozsah (např. ``192.168.1.1-192.168.1.5``)
                      nebo CIDR rozsah (např. ``192.168.1.0/24"``).

      :return: ``True`` pokud adresa odpovídá vzoru.


.. py:class:: IpBlacklistPermission

   Zamítne přístup IP adresám uvedeným v blacklistu ``CustomAdminSettings`` (``pas_api/access_rules``).

   **Metody:**

   .. py:method:: has_permission()

      Ověří, zda IP adresa klienta není na blacklistu.

      :param request: HTTP požadavek.
      :param view: Pohled zpracovávající požadavek.

      :return: ``False`` pokud je IP na blacklistu, jinak ``True``.


.. py:class:: IpWhitelistPermission

   Povolí přístup pouze IP adresám uvedeným ve whitelistu ``CustomAdminSettings`` (``pas_api/access_rules``).

   Pokud žádné aktivní whitelist pravidlo neexistuje, propustí všechny požadavky.

   **Metody:**

   .. py:method:: has_permission()

      Ověří, zda IP adresa klienta je na whitelistu (pokud je whitelist definován).

      :param request: HTTP požadavek.
      :param view: Pohled zpracovávající požadavek.

      :return: ``True`` pokud whitelist není definován nebo IP na něm je, jinak ``False``.


.. py:class:: UserBlacklistPermission

   Zamítne přístup uživatelům uvedeným v blacklistu ``CustomAdminSettings`` (``pas_api/access_rules``).

   **Metody:**

   .. py:method:: has_permission()

      Ověří, zda přihlášený uživatel není na blacklistu.

      :param request: HTTP požadavek.
      :param view: Pohled zpracovávající požadavek.

      :return: ``False`` pokud je uživatel na blacklistu, jinak ``True``.


.. py:class:: UserWhitelistPermission

   Povolí přístup pouze uživatelům uvedeným ve whitelistu ``CustomAdminSettings`` (``pas_api/access_rules``).

   Pokud žádné aktivní whitelist pravidlo neexistuje, propustí všechny požadavky.

   **Metody:**

   .. py:method:: has_permission()

      Ověří, zda přihlášený uživatel je na whitelistu (pokud je whitelist definován).

      :param request: HTTP požadavek.
      :param view: Pohled zpracovávající požadavek.

      :return: ``True`` pokud whitelist není definován nebo uživatel na něm je, jinak ``False``.


.. py:class:: ApiAccessModePermission

   Řídí globální dostupnost PAS XML API podle ``CustomAdminSettings`` (``pas_api/access_mode``).

   **Metody:**

   .. py:method:: has_permission()

      Ověří globální režim dostupnosti API.

      Režim ``open`` požadavek propustí. Režim ``closed`` vše zamítne.
      Režim ``whitelist_only`` vyžaduje alespoň jedno aktivní whitelist pravidlo.

      :param request: HTTP požadavek.
      :param view: Pohled zpracovávající požadavek.

      :return: ``True`` pokud režim přístup dovoluje, jinak ``False``.


.. py:class:: ApiImportThrottle

   Throttle pro API import samostatného nálezu řízený záznamy ``CustomAdminSettings`` (``pas_api/rate_limits``).

   Pravidla jsou načítána z databáze (s cache) a aplikována v pořadí:
   nejdříve pravidlo pro konkrétního uživatele, pak pro IP adresu.
   Pokud žádné pravidlo neexistuje, požadavek je povolen.

   **Metody:**

   .. py:method:: allow_request()

      Rozhodne, zda je požadavek povolen na základě nakonfigurovaných limitů.

      :param request: HTTP požadavek.
      :param view: Pohled zpracovávající požadavek.

      :return: ``True`` pokud limit nebyl překročen nebo neexistuje, jinak ``False``.

   .. py:method:: _check_limit()

      Zkontroluje a aktualizuje počítadlo požadavků v cache pro daný klíč a rate.

      :param cache_key: Klíč pro uložení počítadla v cache.
      :param rate: Řetězec limitu ve formátu ``počet/jednotka``.
      :param request: HTTP požadavek (použit pro logování).

      :return: ``True`` pokud limit nebyl překročen, jinak ``False``.

   .. py:method:: wait()

      Vrátí počet sekund do dalšího povoleného požadavku.

      :return: Počet sekund nebo ``None``.


.. py:class:: ImportErrorType

   Typ chyby při importu XML samostatného nálezu.


.. py:class:: ImportValidationIssue

   Strukturovaná chyba vzniklá při importu XML samostatného nálezu.

   **Metody:**

   .. py:method:: to_dict()

      Převede chybu na slovník pro API odpověď.

      :return: Slovníková reprezentace chyby.


.. py:class:: ImportValidationException

   Validační chyba importu nesoucí již vytvořené ``ImportValidationIssue`` instance.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: from_serializer_errors()

      Vytvoří výjimku importu z chyb serializeru.

      :param errors: Chyby vrácené serializerem.
      :param line: Řádek zdrojového XML elementu.
      :param column: Sloupec zdrojového XML elementu.

      :return: Výjimka s naplněnými ``ImportValidationIssue`` instancemi.

   .. py:method:: _serializer_error_to_error_type()

      Určí typ importní chyby podle chyby serializeru.

      :param field_name: Název pole serializeru, na kterém chyba vznikla.
      :param field_error: Jedna chyba serializeru.

      :return: Typ importní chyby.


.. py:class:: SamostatnyNalezXmlImportSerializer

   Serializer pro import záznamu samostatného nálezu z XML; FK pole jsou identifikována přes ident_cely.


.. py:class:: SamostatnyNalezXmlImportView

   Pohled pro import záznamu samostatného nálezu z XML souboru přes POST požadavek.

   **Metody:**

   .. py:method:: dispatch()

      Zpracuje globální režim ``closed`` ještě před DRF permission vrstvou.

      Tím je zajištěn návratový kód ``503 Service Unavailable`` bez zapojení
      permission mechaniky DRF, která by jinak vracela ``403``.

      :param request: Příchozí HTTP požadavek.
      :param args: Dodatečné poziční argumenty.
      :param kwargs: Dodatečné pojmenované argumenty.

      :return: HTTP odpověď view nebo okamžitá odpověď ``503`` při vypnutém API.

   .. py:method:: _fail()

      Označí log záznam jako neúspěšný, vytvoří a vrátí chybovou odpověď.

      :param log_entry: Záznam logu API požadavku.
      :param body: Tělo odpovědi jako slovník.
      :param status: HTTP stavový kód odpovědi.

      :return: Chybová HTTP odpověď se zadaným tělem a stavovým kódem.

   .. py:method:: _success()

      Označí log záznam jako úspěšný, zaloguje výsledek a vrátí XML odpověď s metadaty.

      :param log_entry: Záznam logu API požadavku.
      :param instance: Uložený záznam samostatného nálezu.
      :param metadata: XML metadata vrácená Fedora repozitářem.
      :param notes: Seznam poznámek o ignorovaných atributech ``xml:lang``.

      :return: HTTP odpověď s XML metadaty a stavovým kódem 200.

   .. py:method:: post()

      Importuje nový záznam samostatného nálezu z XML souboru.

      Přijímá soubor v parametru ``file`` (multipart/form-data). XML musí odpovídat
      schématu AMČR 2.2 (https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd).
      Dokument musí obsahovat právě jeden element ``amcr:samostatny_nalez``.

      :param request: HTTP požadavek obsahující XML soubor v poli ``file``.
      :param format: Formát odpovědi.

      :return: Vrací ``Response`` s metadaty vytvořeného záznamu (HTTP 200),
               nebo chybou syntaxe volání (HTTP 400), chybějícím projektem (HTTP 404),
               nevalidním XML či datovými chybami (HTTP 422).

   .. py:method:: _has_import_permissions()

      Ověří oprávnění potřebná pro import samostatného nálezu.

      :param user: Uživatel provádějící import.
      :param data: Data jednoho importovaného záznamu.

      :return: Vrací ``True`` pokud má uživatel všechna vyžadovaná oprávnění.

   .. py:method:: _create_import_history_records()

      Vytvoří historii pro importovaný záznam samostatného nálezu.

      :param instance: Vytvořený záznam samostatného nálezu.
      :param user: Uživatel, který provedl import.

   .. py:method:: _validation_status()

      Určí HTTP stavový kód odpovědi na základě typů validačních chyb.

      :param errors: Seznam validačních chyb importu.

      :return: HTTP stavový kód odpovídající nejzávažnějšímu typu chyby.

   .. py:method:: _validate_disallowed_elements()

      Ověří, že importovaný element neobsahuje nepovolené podřízené elementy.

      :param elem: Importovaný element ``amcr:samostatny_nalez``.

      :raises ImportValidationException: Pokud je nalezen nepovolený element.

   .. py:method:: _build_schema_validation_doc()

      Vytvoří kopii dokumentu upravenou pro validaci proti XSD schématu.

      Importní API nepovoluje element ``stav``, ale XSD jej vyžaduje.
      Pro validaci proto doplní chybějící ``stav`` do kopie dokumentu.

      :param doc: Původní XML dokument.

      :return: Kopie XML dokumentu určená pro schema validaci.

   .. py:method:: _validate_heslar_value_matches()

      Ověří shodu textové hodnoty XML a ``heslo`` na navázaném hesláři.

      :param validated_data: Validovaná data serializeru.
      :param elem: Importovaný XML element.

      :raises ImportValidationException: Pokud text elementu neodpovídá ``heslo``.

   .. py:method:: _verify_content_digest()

      Ověří integritu souboru pomocí hlavičky ``Content-Digest`` (RFC 9530).

      Očekávaný formát hlavičky: ``sha-512=:<base64>:``
      Pokud hlavička chybí nebo neodpovídá skutečnému SHA-512 obsahu souboru,
      vrátí chybovou zprávu.

      :param request: HTTP požadavek obsahující hlavičku ``Content-Digest``.
      :param xml_file: Nahraný soubor; po zavolání je pozice čtení na začátku.

      :return: Chybová zpráva jako řetězec, nebo None pokud je digest v pořádku.

   .. py:method:: _validate_declared_schema_version()

      Ověří, že XML deklaruje podporovanou verzi AMČR schématu.

      :param doc: Naparsovaný XML dokument.

      :return: Chybová zpráva nebo ``None``, pokud deklarace odpovídá podporované verzi.

   .. py:method:: _get_amcr_schema()

      Vrátí zkompilované XSD schéma AMČR podle URL deklarované v ``xsi:schemaLocation``.

      :param doc: Naparsovaný XML dokument s deklarovaným ``xsi:schemaLocation``.

      :return: Vrací instanci ``etree.XMLSchema`` pro validaci importovaných XML dokumentů.

   .. py:method:: _validate_schema_url_allowed()

      Ověří, že URL schématu patří mezi povolené URL prefixy.

      :param url: URL schématu nebo importovaného XSD souboru.

      :raises ImportValidationException: Pokud URL míří mimo povolené domény.

   .. py:method:: _ns()

      Vrátí tag s prefixem jmenného prostoru AMČR.

      :param tag: Název elementu bez prefixu jmenného prostoru.

      :return: Vrací řetězec ve tvaru ``{namespace}tag``.

   .. py:method:: _get_ignored_lang_notes()

      Vrátí seznam poznámek pro elementy s nepodporovaným ``xml:lang``.

      :param elem: Importovaný element ``amcr:samostatny_nalez``.

      :return: Seznam textových poznámek.

   .. py:method:: _parse_bool()

      Převede textovou hodnotu XML elementu na Python ``bool``, nebo ``None``.

      Přijímá hodnoty ``"true"`` / ``"1"`` jako ``True`` a ``"false"`` / ``"0"`` jako ``False``
      (bez ohledu na velikost písmen). Ostatní hodnoty a ``None`` vrátí ``None``.

      :param value: Textová hodnota z XML elementu.

      :return: ``True``, ``False``, nebo ``None``.

   .. py:method:: _text()

      Vrátí textový obsah prvního podřízeného elementu se zadaným tagem, nebo None.

      :param elem: Rodičovský element, ve kterém se hledá.
      :param tag: Název hledaného podřízeného elementu (bez jmenného prostoru).

      :return: Textový obsah elementu nebo None, pokud element neexistuje nebo je prázdný.

   .. py:method:: _id_attr()

      Vrátí hodnotu atributu ``id`` prvního podřízeného elementu se zadaným tagem.

      Používá se pro elementy typu ``refType`` a ``vocabType``, kde atribut ``id``
      nese ``ident_cely`` odkazovaného záznamu.

      :param elem: Rodičovský element, ve kterém se hledá.
      :param tag: Název hledaného podřízeného elementu (bez jmenného prostoru).

      :return: Hodnota atributu ``id`` nebo None, pokud element nebo atribut neexistuje.

   .. py:method:: _parse_nalezce()

      Zpracuje element ``nalezce`` a vrátí ``ident_cely`` osoby pro import.

      Pokud má element atribut ``id=":tba"``, vytvoří se nová osoba z textu
      ve formátu ``"Příjmení, Jméno"``. Nová osoba se zde pouze připraví,
      ale uloží se až v transakci společně s ``SamostatnyNalez``.

      :param elem: Element ``amcr:samostatny_nalez``.
      :param user: Uživatel provádějící import.

      :return: Dvojice ``(ident_cely_osoby, nova_osoba)``.

   .. py:method:: _parse_nalez_element()

      Převede element ``amcr:samostatny_nalez`` na slovník pro deserializaci.

      Elementy typu ``refType`` a ``vocabType`` se mapují pomocí atributu ``id``,
      který nese ``ident_cely`` odkazovaného záznamu. Geometrie jsou předány
      jako WKT řetězce z elementů ``geom_wkt`` a ``geom_sjtsk_wkt``.

      :param elem: Element ``amcr:samostatny_nalez`` z importovaného XML dokumentu.
      :param user: Uživatel provádějící import.

      :return: Dvojice ``(data, nova_osoba)`` připravená pro import.


Funkce
------

.. py:function:: _invalidate_api_cache(sender, instance)

   Vymaže cache pravidel API po změně záznamu ``CustomAdminSettings`` skupiny ``pas_api``.

.. py:function:: _strip_namespace(tag)

   Vrátí název XML tagu bez namespace prefixu.

   :param tag: XML tag včetně namespace (např. ``{http://example.com}element``).

   :return: Název tagu bez namespace (např. ``element``).

.. py:function:: _parse_rate(rate)

   Naparsuje řetězec limitu ve formátu ``počet/jednotka`` na počet a délku okna v sekundách.

   Podporované jednotky: ``s`` (sekunda), ``m`` (minuta), ``h`` (hodina), ``d`` (den).

   :param rate: Řetězec ve formátu ``10/m``, ``100/h`` apod.

   :return: Dvojice ``(počet, okno_v_sekundách)`` nebo ``None`` při chybě parsování.
