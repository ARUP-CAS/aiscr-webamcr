API views
=========

Definice views.

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
          - ``active`` *(volitelný, výchozí ``true``)* — ``false`` pravidlo dočasně deaktivuje

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
            jednotky: ``ms`` (milisekunda), ``s`` (sekunda), ``m`` (minuta),
            ``h`` (hodina), ``d`` (den);
            např. ``"5/ms"``, ``"10/m"``, ``"100/h"``, ``"1000/d"``
          - ``active`` *(volitelný, výchozí ``true``)* — ``false`` limit dočasně deaktivuje

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
          Pokud nastavení chybí, použije se výchozí prázdný seznam ``[]``.

          Příklad::

              ["10.0.1.0/24", "proxy"]

      ``record_lock_params`` (``item_id="record_lock_params"``)
          Parametry Redis zámku záznamu. Objekt s klíči:

          - ``retry_delay`` *(volitelný, výchozí ``0.5``)* — čekací interval v sekundách
            mezi pokusy o získání zámku; musí být kladné číslo (``float``)
          - ``max_retries`` *(volitelný, výchozí ``10``)* — maximální počet pokusů;
            musí být kladné celé číslo (``int``)

          Pokud nastavení chybí, použijí se výchozí hodnoty.

          Příklad::

              {"retry_delay": 1.0, "max_retries": 5}

      ``cache_ttl`` (``item_id="cache_ttl"``)
          TTL (v sekundách) pro ukládání ostatních nastavení PAS API do cache.
          Musí být kladné celé číslo. Výchozí hodnota je ``3600``.

          Příklad::

              60

      ``record_lock_ttl`` (``item_id="record_lock_ttl"``)
          TTL (v sekundách) pro Redis zámek záznamu. Musí být kladné celé číslo.
          Výchozí hodnota je ``300`` (5 minut).

          Příklad::

              600

      ``schema_fetch_timeout`` (``item_id="schema_fetch_timeout"``)
          Časový limit (v sekundách) pro stahování XSD schémat ze sítě.
          Musí být kladné celé číslo. Výchozí hodnota je ``10``.

          Příklad::

              30

      ``schema_cache_ttl`` (``item_id="schema_cache_ttl"``)
          TTL (v sekundách) pro Redis cache XSD schémat. Musí být kladné celé číslo.
          Výchozí hodnota je ``3600`` (60 minut).

          Příklad::

              7200

      ``min_request_intervals`` (``item_id="min_request_intervals"``)
          Minimální interval mezi po sobě jdoucími požadavky pro globální throttling.
          Objekt s volitelnými klíči:

          - ``user_ms`` *(volitelný, výchozí ``0``)* — minimální interval v milisekundách
            pro téhož uživatele; hodnota ``0`` limit deaktivuje
          - ``ip_ms`` *(volitelný, výchozí ``0``)* — minimální interval v milisekundách
            pro tutéž IP adresu; hodnota ``0`` limit deaktivuje

          Pokud nastavení chybí, jsou oba limity deaktivovány (hodnota ``0``).

          Příklad::

              {"user_ms": 500, "ip_ms": 200}

      Změny v administraci se projeví do hodnoty ``cache_ttl`` (výchozí ``3600`` sekund); změny provedené přes Django admin se projeví okamžitě díky invalidaci cache signálem ``post_save``.

      :param item_id: Identifikátor záznamu — ``"access_rules"``, ``"rate_limits"``, ``"access_mode"``,
          ``"trusted_proxies"``, ``"record_lock_params"``, ``"cache_ttl"``, ``"record_lock_ttl"``,
          ``"schema_fetch_timeout"``, ``"schema_cache_ttl"`` nebo ``"min_request_intervals"``.

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
      validuje JSON hodnotu příslušným validátorem. Podporovaná ``item_id``:
      ``"access_rules"``, ``"rate_limits"``, ``"access_mode"``, ``"trusted_proxies"``,
      ``"record_lock_params"``.

      :param instance: Ukládaný záznam ``CustomAdminSettings``.

      :raises ValidationError: Pokud ``item_id`` není podporováno nebo JSON/struktura hodnoty nejsou validní.
      :return: ``True`` pokud je záznam validní nebo se na něj validace nevztahuje.

   .. py:method:: get_rate_limits()

      Vrátí limity počtu požadavků z cache nebo ``CustomAdminSettings``.

      Každý limit je slovník s klíči ``scope``, ``rate`` a volitelně ``active`` (výchozí ``True``).
      Pro scope ``user`` a ``ip`` je navíc povinný klíč ``value``.

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
      ``[]``.

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

   .. py:method:: get_record_lock_params()

      Vrátí parametry Redis zámku záznamu z cache nebo ``CustomAdminSettings``.

      Pokud nastavení ``record_lock_params`` neexistuje, vrátí výchozí hodnoty
      ``(_RECORD_LOCK_DEFAULT_RETRY_DELAY, _RECORD_LOCK_DEFAULT_MAX_RETRIES)``.

      :raises ValidationError: Pokud nastavení má neplatnou strukturu.
      :return: Dvojice ``(retry_delay, max_retries)``.

   .. py:method:: validate_record_lock_params()

      Ověří strukturu a obsah nastavení ``record_lock_params``.

      Očekávaný formát je objekt s nepovinnými klíči ``retry_delay`` (kladné ``float``)
      a ``max_retries`` (kladné celé číslo ``int``).

      :param raw_params: Naparsovaná JSON hodnota nastavení ``record_lock_params``.

      :raises ValidationError: Pokud struktura nebo hodnoty neodpovídají očekávání.
      :return: ``True`` pokud je nastavení validní.

   .. py:method:: validate_allowed_schema_versions()

      Ověří strukturu a obsah nastavení ``allowed_schema_versions``.

      Očekávaný formát je neprázdný seznam čísel (``float`` nebo ``int``),
      například ``[2.2]`` nebo ``[2.2, 2.3]``. Záporné nebo nulové hodnoty nejsou povoleny.

      :param raw_versions: Naparsovaná JSON hodnota nastavení ``allowed_schema_versions``.

      :raises ValidationError: Pokud hodnota není neprázdný seznam kladných čísel.
      :return: ``True`` pokud je nastavení validní.

   .. py:method:: get_allowed_schema_versions()

      Vrátí seznam povolených verzí AMČR XSD schématu z cache nebo ``CustomAdminSettings``.

      Pokud nastavení ``allowed_schema_versions`` neexistuje, vrátí ``None`` (povoleny jsou
      všechny verze, které projdou ostatními kontrolami). Pokud nastavení existuje, vrátí
      seznam hodnot jako ``float``.

      :return: Seznam povolených verzí nebo ``None``, pokud nastavení není nakonfigurováno.

   .. py:method:: validate_positive_int_setting()

      Ověří, že hodnota nastavení je kladné celé číslo.

      Používá se pro nastavení ``cache_ttl``, ``record_lock_ttl``, ``schema_fetch_timeout``
      a ``schema_cache_ttl``.

      :param value: Naparsovaná JSON hodnota nastavení.
      :param item_id: Identifikátor nastavení použitý v chybové zprávě.

      :raises ValidationError: Pokud hodnota není kladné celé číslo.
      :return: ``True`` pokud je hodnota validní.

   .. py:method:: validate_min_request_intervals()

      Ověří strukturu a obsah nastavení ``min_request_intervals``.

      Očekávaný formát je objekt s nepovinnými klíči ``user_ms`` (nezáporné celé číslo)
      a ``ip_ms`` (nezáporné celé číslo). Hodnota ``0`` limit deaktivuje.

      :param raw: Naparsovaná JSON hodnota nastavení ``min_request_intervals``.

      :raises ValidationError: Pokud struktura nebo hodnoty neodpovídají očekávání.
      :return: ``True`` pokud je nastavení validní.

   .. py:method:: get_cache_ttl()

      Vrátí TTL (v sekundách) pro ukládání nastavení PAS API do cache.

      Hodnota se načítá z ``CustomAdminSettings`` (``pas_api/cache_ttl``) a kešuje se
      po dobu výchozího TTL (``_DEFAULT_CACHE_TTL``). Pokud nastavení neexistuje, vrátí výchozí
      hodnotu ``_DEFAULT_CACHE_TTL`` (``3600`` sekund).

      :return: TTL v sekundách.

   .. py:method:: get_record_lock_ttl()

      Vrátí TTL (v sekundách) pro Redis zámek záznamu.

      Hodnota se načítá z ``CustomAdminSettings`` (``pas_api/record_lock_ttl``) a kešuje se.
      Pokud nastavení neexistuje, vrátí výchozí hodnotu ``_RECORD_LOCK_DEFAULT_TTL`` (``300`` sekund).

      :return: TTL zámku záznamu v sekundách.

   .. py:method:: get_schema_fetch_timeout()

      Vrátí časový limit (v sekundách) pro stahování XSD schémat ze sítě.

      Hodnota se načítá z ``CustomAdminSettings`` (``pas_api/schema_fetch_timeout``) a kešuje se.
      Pokud nastavení neexistuje, vrátí výchozí hodnotu ``_AMCR_SCHEMA_DEFAULT_FETCH_TIMEOUT`` (``10`` sekund).

      :return: Časový limit v sekundách.

   .. py:method:: get_schema_cache_ttl()

      Vrátí TTL (v sekundách) pro Redis cache XSD schémat.

      Hodnota se načítá z ``CustomAdminSettings`` (``pas_api/schema_cache_ttl``) a kešuje se.
      Pokud nastavení neexistuje, vrátí výchozí hodnotu ``_AMCR_SCHEMA_DEFAULT_CACHE_TTL`` (``3600`` sekund).

      :return: TTL cache schémat v sekundách.

   .. py:method:: get_min_request_intervals()

      Vrátí minimální intervaly (v ms) mezi požadavky pro throttling per-user a per-IP.

      Hodnota se načítá z ``CustomAdminSettings`` (``pas_api/min_request_intervals``) a kešuje se.
      Pokud nastavení neexistuje, vrátí ``(0, 0)`` (oba limity deaktivovány).

      :return: Dvojice ``(user_ms, ip_ms)``.

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

   Pravidla jsou načítána z databáze (s cache) a vyhodnocují se nezávisle podle scope:
   ``user``, ``ip`` a ``record``. Požadavek je povolen pouze tehdy, pokud projde všemi
   relevantními limity pro dané volání.

   Scope ``record`` používá ``ident_cely`` z URL jako stabilní identifikátor konkrétního
   záznamu. To je záměrné: jeden limit se tak sdílí mezi různými endpointy a akcemi nad
   týmž ``SamostatnyNalez`` a nelze jej obejít střídáním například PATCH a upload endpointu.

   **Metody:**

   .. py:method:: allow_request()

      Rozhodne, zda je požadavek povolen na základě nakonfigurovaných limitů.

      :param request: HTTP požadavek.
      :param view: Pohled zpracovávající požadavek.

      :return: ``True`` pokud nebyl překročen žádný relevantní limit, jinak ``False``.

   .. py:method:: _check_limit()

      Zkontroluje a aktualizuje počítadlo požadavků v cache pro daný klíč a rate.

      Implementace používá fixní časové okno s atomickými operacemi ``cache.add()``
      a ``cache.incr()``. Oproti původnímu ukládání seznamu timestampů tím odpadá
      read-modify-write race condition při souběžných požadavcích.

      :param cache_key: Klíč pro uložení počítadla v cache.
      :param rate: Řetězec limitu ve formátu ``počet/jednotka``.
      :param request: HTTP požadavek (použit pro logování).

      :return: ``True`` pokud limit nebyl překročen, jinak ``False``.

   .. py:method:: _check_min_interval()

      Ověří, že od posledního požadavku ve stejném scope uplynula minimální doba.

      Limit je globální (aplikuje se na všechny uživatele resp. IP) a konfiguruje se
      přes ``CustomAdminSettings`` (``pas_api/min_request_intervals``). V Redis je uložena časová značka
      posledního povoleného požadavku. Pokud žádná hodnota není uložena (typicky první požadavek
      po startu nebo po vypršení TTL), je limit považován za splněný a aktuální čas se uloží.

      :param cache_key: Klíč v cache (Redis).
      :param min_interval_ms: Minimální interval mezi požadavky v milisekundách.
      :param scope: Logický rozsah limitu (``"user"`` nebo ``"ip"``) — použito v logu.
      :param identifier: Identifikátor (uživatel / IP) — použito v logu.

      :return: ``True`` pokud limit nebyl porušen (a nový časový bod byl uložen), jinak ``False``.

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


.. py:class:: PasApiBaseView

   Základní pohled sdílený všemi PAS API endpointy.

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
      :param http_status: HTTP stavový kód odpovědi.

      :return: Chybová HTTP odpověď se zadaným tělem a stavovým kódem.

   .. py:method:: _has_edit_permissions()

      Ověří, zda má uživatel oprávnění editovat zadaný samostatný nález.

      :param user: Uživatel provádějící požadavek.
      :param ident_cely: Identifikátor záznamu samostatného nálezu.

      :return: Vrací ``True`` pokud má uživatel oprávnění ``pas_edit`` pro daný záznam.

   .. py:method:: _update_igsn_if_archived()

      Pokud je záznam ve stavu SN4 (archivovaný), aktualizuje jeho IGSN metadata.

      :param instance: Aktualizovaný záznam samostatného nálezu.

      :raises DoiWriteError: Pokud aktualizace IGSN selže.

   .. py:method:: _acquire_record_lock()

      Pokusí se získat zámek záznamu v Redis.

      Kombinuje in-process ``threading.Lock`` (``_record_lock_thread_lock``) pro serializaci
      vláken v rámci jednoho Django workeru s atomickým ``cache.add`` pro koordinaci
      mezi více procesy. Pokud klíč neexistuje nebo má hodnotu ``0`` (uvolněno), zámek je
      získán nastavením hodnoty na ``1``. Pokud je klíč ``1`` (zamčeno jiným workerem),
      čeká ``_RECORD_LOCK_RETRY_DELAY`` sekund a zkusí znovu, nejvýše
      ``_RECORD_LOCK_MAX_RETRIES``-krát.

      :param ident_cely: Identifikátor záznamu, jehož zámek se má získat.

      :return: Dvojice ``(úspěch, ttl)`` — TTL se předává do :meth:`_release_record_lock`,
          aby se zamezilo opakovanému čtení z cache při uvolňování zámku.

   .. py:method:: _release_record_lock()

      Uvolní zámek záznamu nastavením Redis hodnoty na ``0``.

      :param ident_cely: Identifikátor záznamu, jehož zámek se má uvolnit.
      :param ttl: TTL v sekundách — hodnota vrácená z :meth:`_acquire_record_lock`;
          předává se přímo, aby se zamezilo zbytečnému čtení z cache.

   .. py:method:: _verify_content_digest()

      Ověří integritu souboru pomocí hlavičky ``Content-Digest`` (RFC 9530).

      Očekávaný formát hlavičky: ``sha-512=:<base64>:``
      Pokud hlavička chybí nebo neodpovídá skutečnému SHA-512 obsahu souboru,
      vrátí chybovou zprávu.

      :param request: HTTP požadavek obsahující hlavičku ``Content-Digest``.
      :param uploaded_file: Nahraný soubor; po zavolání je pozice čtení na začátku.
      :param mismatch_status: Stavový kód použitý při neodpovídajícím SHA-512 hashi.

      :return: Dvojice ``(zpráva, status)`` nebo ``None`` pokud je digest v pořádku.

   .. py:method:: _success()

      Označí log záznam jako úspěšný, zaloguje výsledek a vrátí XML odpověď s metadaty.

      Tato metoda vrací surové XML bajty přes ``HttpResponse`` místo DRF ``Response``,
      aby nedošlo k zásahu rendererů DRF do XML výstupu. Chybové odpovědi v téže view
      jsou vytvářeny metodou ``_fail()``, která používá DRF ``Response`` pro standardní
      serializaci strukturovaného JSON těla.

      :param log_entry: Záznam logu API požadavku.
      :param instance: Uložený záznam samostatného nálezu.
      :param metadata: XML metadata vrácená Fedora repozitářem.
      :param notes: Seznam poznámek o ignorovaných atributech ``xml:lang``.

      :return: HTTP odpověď s XML metadaty a stavovým kódem 200.


.. py:class:: SamostatnyNalezXmlBaseView

   Základní pohled pro XML import záznamu samostatného nálezu.

   **Metody:**

   .. py:method:: _validation_status()

      Určí HTTP stavový kód odpovědi na základě typů validačních chyb.

      :param errors: Seznam validačních chyb importu.

      :return: HTTP stavový kód odpovídající nejzávažnějšímu typu chyby.

   .. py:method:: _validate_declared_schema_version()

      Ověří, že XML deklaruje podporovanou verzi AMČR schématu.

      Pokud je předán parametr ``allowed_versions``, zkontroluje navíc, zda verze schématu
      v dokumentu patří mezi povolené verze nakonfigurované v nastavení ``allowed_schema_versions``.

      :param doc: Naparsovaný XML dokument.
      :param allowed_versions: Seznam povolených verzí schématu nebo ``None`` (bez omezení).

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

   .. py:method:: _parse_point_wkt()

      Ověří, že text XML elementu obsahuje platné WKT geometrie typu ``Point``.

      :param elem: XML element obsahující WKT text.
      :param field_name: Název pole pro chybovou zprávu (``"geom_wkt"`` nebo ``"geom_sjtsk_wkt"``).

      :return: WKT řetězec geometrie.

      :raises ImportValidationException: Pokud je WKT syntakticky neplatné, prázdné nebo není typu ``Point``.

   .. py:method:: _parse_nalez_element()

      Převede element ``amcr:samostatny_nalez`` na slovník pro deserializaci.

      Elementy typu ``refType`` a ``vocabType`` se mapují pomocí atributu ``id``,
      který nese ``ident_cely`` odkazovaného záznamu. Geometrie se určují vždy
      z jednoho zdrojového elementu podle ``geom_system``:

      - ``geom_system=4326`` — zdrojem je ``geom_wkt``; ``geom_sjtsk`` se vypočítá
        konverzí do S-JTSK, element ``geom_sjtsk_wkt`` se ignoruje.
      - ``geom_system=5514`` — zdrojem je ``geom_sjtsk_wkt``; ``geom`` se vypočítá
        konverzí do WGS-84, element ``geom_wkt`` se ignoruje.

      ``stav`` — musí být jedna z povolených hodnot (1, 2, 3); určuje cílový stav záznamu po importu.

      Následující elementy jsou v XML povoleny, ale při importu se ignorují:

      - ``igsn`` — přiděluje se automaticky po archivaci záznamu.
      - ``okres`` — stanoví se automaticky podle souřadnic.
      - ``katastr`` (v ``chranene_udaje``) — stanoví se automaticky podle souřadnic.
      - ``geom_gml`` (v ``chranene_udaje``) — geometrie se přebírá z ``geom_wkt``.
      - ``geom_sjtsk_gml`` (v ``chranene_udaje``) — geometrie se přebírá z ``geom_sjtsk_wkt``.
      - ``geom_sjtsk_wkt`` (v ``chranene_udaje``) — ignoruje se, pokud ``geom_system=4326``.
      - ``geom_wkt`` (v ``chranene_udaje``) — ignoruje se, pokud ``geom_system=5514``.
      - ``historie`` — generuje se automaticky systémem.
      - ``soubor`` — soubory se nahrávají samostatným endpointem.

      :param elem: Element ``amcr:samostatny_nalez`` z importovaného XML dokumentu.
      :param user: Uživatel provádějící import.

      :return: Dvojice ``(data, nova_osoba)`` připravená pro import.

   .. py:method:: _parse_geom_fields()

      Načte a převede geometrie podle ``geom_system``.

      Při ``geom_system="4326"`` se jako zdroj použije ``geom_wkt`` a výsledek se
      konvertuje do S-JTSK (5514). Element ``geom_sjtsk_wkt`` se ignoruje.
      Při ``geom_system="5514"`` se jako zdroj použije ``geom_sjtsk_wkt`` a výsledek
      se konvertuje do WGS-84 (4326). Element ``geom_wkt`` se ignoruje.

      :param chranene: Element ``amcr:chranene_udaje``.
      :param geom_system: Hodnota elementu ``geom_system`` z importovaného dokumentu.

      :return: Dvojice ``(geom_wgs84, geom_sjtsk)`` nebo ``None`` pro každou hodnotu,
          která nebyla nalezena nebo nebyla poskytnuta.

      :raises ImportValidationException: Pokud konverze souřadnic selže.

   .. py:method:: _parse_nalezce()

      Zpracuje element ``nalezce`` a vrátí ``ident_cely`` osoby pro import.

      Pokud má element atribut ``id=":tba"``, nejprve se prohledá databáze podle
      ``prijmeni`` a ``jmeno``. Pokud osoba existuje, použije se její ``ident_cely``.
      Teprve pokud záznam neexistuje, vytvoří se nová osoba z textu ve formátu
      ``"Příjmení, Jméno"``. Nová osoba se zde pouze připraví, ale uloží se až
      v transakci společně s ``SamostatnyNalez``.
      Vytvoření nové osoby tímto importním tokem nevyžaduje samostatné oprávnění.

      :param elem: Element ``amcr:samostatny_nalez``.
      :param user: Uživatel provádějící import.

      :return: Dvojice ``(ident_cely_osoby, nova_osoba)``.


.. py:class:: SamostatnyNalezXmlImportView

   Pohled pro import záznamu samostatného nálezu z XML souboru přes POST požadavek.

   **Metody:**

   .. py:method:: post()

      Importuje nový záznam samostatného nálezu z XML souboru.

      Přijímá soubor v parametru ``file`` (multipart/form-data). XML musí projít validací
      proti XSD schématu AMČR deklarovanému v dokumentu (verze 2.2 na URL
      ``https://api.aiscr.cz/schema/amcr/2.2/amcr.xsd`` nebo novější). Volitelné nastavení administrace
      ``allowed_schema_versions`` může omezit povolené číslo verze schématu v namespace
      dokumentu (viz ``PasApiPermissionMixin.get_allowed_schema_versions``).
      Dokument musí obsahovat právě jeden element ``amcr:samostatny_nalez``.

      :param request: HTTP požadavek obsahující XML soubor v poli ``file``.
      :param format: Formát odpovědi.

      :return: Vrací ``Response`` s metadaty vytvořeného záznamu (HTTP 200),
               nebo chybou syntaxe volání (HTTP 400), chybějícím projektem (HTTP 404),
               nevalidním XML či datovými chybami (HTTP 422).

   .. py:method:: _has_import_permissions()

      Ověří oprávnění potřebná pro import samostatného nálezu.

      Kontroluje dvě podmínky: stav záznamu musí odpovídat roli uživatele (badatel
      nejvýše stav 1, ostatní role nejvýše stav 3) a projekt musí být součástí
      průzkumných projektů dostupných danému uživateli dle
      :meth:`projekt.models.Projekt.get_pruzkum_projekty_pro_uzivatele`.

      :param user: Uživatel provádějící import.
      :param data: Data jednoho importovaného záznamu jako slovník; očekávají se klíče
          ``stav`` (int) a ``projekt`` (ident_cely projektu).
      :return: ``True`` pokud jsou splněny obě podmínky, jinak ``False``.

   .. py:method:: _create_import_history_records()

      Vytvoří záznamy historie pro importovaný samostatný nález.

      Vytvoří pouze záznamy odpovídající přechodům až do cílového stavu záznamu:
      stav 1 → ZAPSANI_SN, stav 2 → ZAPSANI_SN + ODESLANI_SN,
      stav 3 → ZAPSANI_SN + ODESLANI_SN + POTVRZENI_SN.

      :param instance: Vytvořený záznam samostatného nálezu.
      :param user: Uživatel, který provedl import.


.. py:class:: SamostatnyNalezEvidencniCisloPatchView

   Pohled pro aktualizaci pole ``evidencni_cislo`` záznamu samostatného nálezu přes PATCH požadavek.

   **Metody:**

   .. py:method:: _has_edit_permissions()

      Ověří, zda má uživatel oprávnění editovat evidenční číslo záznamu samostatného nálezu.

      Oprávněný je takový uživatel, který splňuje standardní pravidla pro editaci nálezu
      s těmito úpravami:

      - pro aktualizaci ev. čísla nikdy není autorizován badatel (operaci může užívat
        pouze archeolog a výše)
      - pokud je autorizován archeolog, nález může být v libovolném stavu (vč. archivovaného)

      :param user: Uživatel provádějící požadavek.
      :param ident_cely: Identifikátor záznamu samostatného nálezu.

      :return: Vrací ``True`` pokud má uživatel oprávnění ``pas_edit`` pro daný záznam
               a zároveň je jeho hlavní role Archeolog nebo vyšší.

   .. py:method:: patch()

      Aktualizuje pole ``evidencni_cislo`` záznamu samostatného nálezu.

      Přijímá ``ident_cely`` záznamu jako součást URL a novou hodnotu ``evidencni_cislo``
      jako query parametr. Parametr ``evidencni_cislo`` je povinný a jeho
      hodnota musí být neprázdná. Endpoint rozlišuje mezi chybějícím
      parametrem a přítomným parametrem s prázdnou hodnotou, aby klient
      mohl oba validační stavy zpracovat odlišně.

      Příklad volání::

          PATCH /pas/api/nalez/M-202400001-N00001/evidencni-cislo?evidencni_cislo=EC-2024-001

      :param request: HTTP požadavek s povinným query parametrem
                      ``evidencni_cislo``, který nesmí být prázdný.
      :param ident_cely: Identifikátor záznamu samostatného nálezu.
      :param format: Formát odpovědi.

      :return: Vrací XML metadata aktualizovaného záznamu (HTTP 200),
               nebo chybou syntaxe volání (HTTP 400; chybějící parametr
               ``evidencni_cislo``), chybou dat (HTTP 422; prázdná nebo příliš
               dlouhá hodnota), nenalezeným
               záznamem (HTTP 404), nedostatečnými oprávněními (HTTP 403),
               nebo interní chybou (HTTP 500).

   .. py:method:: _create_history_record()

      Vytvoří záznam historie pro aktualizaci pole ``evidencni_cislo``.

      Poznámka záznamu má formát ``<přeložený popisek>: old_value -> new_value``. Je-li záznam ve stavu
      SN4 (archivovaný), zapíše se navíc záznam ``SN34``, který obnoví datum archivace.

      :param instance: Aktualizovaný záznam samostatného nálezu.
      :param user: Uživatel, který provedl aktualizaci.
      :param old_value: Původní hodnota pole ``evidencni_cislo``.
      :param new_value: Nová hodnota pole ``evidencni_cislo``.


.. py:class:: SamostatnyNalezFotografieUploadView

   Pohled pro nahrání jedné fotografie k existujícímu samostatnému nálezu.

   **Metody:**

   .. py:method:: _has_upload_permissions()

      Ověří, zda má uživatel oprávnění nahrát fotografii k danému nálezu.

      Oprávněný je takový uživatel, který splňuje standardní pravidla pro nahrání
      souboru k samostatnému nálezu (``soubor_nahrat_pas``) s touto úpravou:

      - pro archeologa a vyšší roli je nález povolen v libovolném stavu (vč.
        archivovaného) — tj. ``skip_status=True``
      - pro badatele platí standardní pravidlo AMČR (typicky vlastní nález ve
        stavu 1) — ``skip_status`` se neuplatní

      :param user: Uživatel provádějící požadavek.
      :param ident_cely: Identifikátor záznamu samostatného nálezu.

      :return: ``True`` pokud má uživatel oprávnění ``soubor_nahrat_pas`` pro daný záznam
               podle pravidel pro svou roli.

   .. py:method:: _create_rearchive_history_record()

      Pro archivovaný nález zapíše do historie tichou reachivaci ``SN34``.

      :param instance: Aktualizovaný záznam samostatného nálezu.
      :param user: Uživatel, který provedl upload fotografie.

   .. py:method:: post()

      Nahraje fotografii k existujícímu záznamu samostatného nálezu.

      Přijímá ``ident_cely`` záznamu jako součást URL a jeden binární soubor v parametru
      ``file`` (multipart/form-data). Soubor musí projít kontrolou ``Content-Digest``,
      MIME typu a antiviru. Úspěšný upload uloží fotografii do Fedora repository,
      založí záznam ``Soubor`` navázaný na nález a vrátí aktualizovaná XML metadata z Fedory.

      :param request: HTTP požadavek obsahující fotografii v poli ``file``.
      :param ident_cely: Identifikátor aktualizovaného záznamu samostatného nálezu.
      :param format: Formát odpovědi.

      :return: Vrací XML metadata aktualizovaného záznamu (HTTP 201),
               nebo chybu syntaxe volání (HTTP 400; vč. více než jednoho souboru),
               nenalezený záznam (HTTP 404), validační chybu souboru (HTTP 422),
               nebo interní chybu (HTTP 500).


.. py:class:: MyXMLRenderer

   Override třídy pro nastavení správnych tagů.

   **Metody:**

   .. py:method:: render()

      Renders `data` into serialized XML.

      :param data: Kolekce ``data`` zpracovávaná touto funkcí.
      :param accepted_media_type: Parametr ``accepted_media_type`` slouží jako vstup pro logiku funkce ``render``.
      :param renderer_context: Kolekce ``renderer_context`` zpracovávaná touto funkcí.

      :return: Vrací proměnná ``data``.


.. py:class:: GetUserInfo

   Třída pohledu pro získaní základních info o uživately.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` pracuje se s atributy ``user``.
      :param format: Parametr ``format`` slouží jako vstup pro logiku funkce ``get``.

      :return: Vrací výsledek volání ``Response()``.

   .. py:method:: handle_exception()

      Zpracuje exception. v aplikaci.

      :param exc: Číselná hodnota ``exc`` použitá při výpočtu nebo transformaci.

      :return: Vrací výsledek volání ``handle_exception()``.

   .. py:method:: perform_content_negotiation()

      Provádí operaci perform content negotiation.

      :param request: Parametr ``request`` předává se do volání ``perform_content_negotiation()``, vstupuje do návratové hodnoty.
      :param force: Parametr ``force`` se předává do volání ``perform_content_negotiation()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: n-tici, výsledek volání ``perform_content_negotiation()``.

   .. py:method:: finalize_response()

      Provádí operaci finalize response.

      :param request: Parametr ``request`` předává se do volání ``perform_content_negotiation()``, ``finalize_response()``, pracuje se s atributy ``accepted_renderer``, ``accepted_media_type``, vstupuje do návratové hodnoty.
      :param response: Textový nebo strukturální vstup `response` používaný při sestavení nebo zpracování obsahu.
      :param args: Parametr ``args`` se předává do volání ``finalize_response()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``finalize_response()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``finalize_response()``.


.. py:class:: ObtainAuthTokenWithUpdate

   Třída pohledu pro získaní tokenu pro API.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``get_serializer()``, pracuje se s atributy ``data``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``Response()``.


Funkce
------

.. py:function:: _xsd_redis_key(url)

   Sestaví klíč pro Redis cache pro XSD schéma na zadané URL.

   Pro URL AMČR schématu (obsahující ``/schema/amcr/<verze>/``) je klíč ve tvaru
   ``xsd_schema:amcr:<verze>:<url>``, jinak ``xsd_schema:<url>``.

   :param url: URL XSD souboru.

   :return: Řetězec klíče pro Redis cache.

.. py:function:: _fetch_xsd_bytes(url)

   Načte bajty XSD schématu ze zadaného URL.

   Pořadí vyhledávání: in-process slovník → Redis → síť. Výsledek se uloží
   do obou úložišť, takže každá URL je v rámci procesu načtena nejvýše jednou.

   :param url: URL XSD souboru ke stažení.

   :return: Bajty XSD schématu.

   :raises urllib.error.URLError: Pokud se nepodaří navázat spojení s URL.
   :raises TimeoutError: Pokud vyprší časový limit požadavku.
   :raises ValueError: Pokud server vrátí prázdné tělo odpovědi.

.. py:function:: _is_valid_ip_rule_value(value)

   Ověří, zda je hodnota IP pravidla syntakticky platná adresa, CIDR prefix nebo IP rozsah.

   Podporuje IPv4 i IPv6 ve všech třech formátech:
   - jednotlivá adresa (``"192.0.2.1"``, ``"2001:db8::1"``)
   - CIDR prefix (``"192.0.2.0/24"``, ``"2001:db8::/32"``)
   - explicitní rozsah (``"192.168.1.1-192.168.1.5"``; pouze IPv4)

   :param value: Řetězec z pole ``value`` v pravidle ``access_rules`` nebo ``rate_limits``.

   :return: ``True`` pokud je hodnota syntakticky validní.

.. py:function:: _invalidate_api_cache(sender, instance)

   Vymaže cache pravidel API po změně záznamu ``CustomAdminSettings`` skupiny ``pas_api``.

.. py:function:: _strip_namespace(tag)

   Vrátí název XML tagu bez namespace prefixu.

   :param tag: XML tag včetně namespace (např. ``{http://example.com}element``).

   :return: Název tagu bez namespace (např. ``element``).

.. py:function:: _parse_rate(rate)

   Naparsuje řetězec limitu ve formátu ``počet/jednotka`` na počet a délku okna v sekundách.

   Podporované jednotky: ``ms`` (milisekunda), ``s`` (sekunda), ``m`` (minuta),
   ``h`` (hodina), ``d`` (den). Pro jednotku ``ms`` je vrácené okno typu ``float``
   (0.001 s); pro ostatní jednotky je ``int``.

   :param rate: Řetězec ve formátu ``10/m``, ``100/h`` apod.

   :return: Dvojice ``(počet, okno_v_sekundách)`` nebo ``None`` při chybě parsování.
