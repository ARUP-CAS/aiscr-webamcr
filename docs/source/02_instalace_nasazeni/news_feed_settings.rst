Nastavení novinek na přihlašovací stránce
=========================================

Novinky na přihlašovací stránce se nastavují v administraci
``CustomAdminSettings`` ve skupině ``news_feed``. Všechny hodnoty jsou uloženy
jako text; jazyky jsou JSON pole. Při běžném čtení se databáze nemění. Chybějící,
neplatná nebo duplicitní hodnota se zaznamená do logu a použije se výchozí hodnota.

.. list-table:: Nastavení skupiny ``news_feed``
   :header-rows: 1

   * - Identifikátor
     - Výchozí hodnota
     - Formát a jednotka
   * - ``news_feed_block_height``
     - ``300``
     - Kladné celé číslo, výška sbaleného bloku v pixelech.
   * - ``news_feed_base_url``
     - ``https://arup-cas.github.io/aiscr-news/feed/amcr``
     - HTTPS adresář kanálu na důvěryhodném hostiteli ``arup-cas.github.io``; bez koncového lomítka.
   * - ``news_feed_languages``
     - ``["cs", "en"]``
     - Neprázdné JSON pole jedinečných jazykových kódů podporovaných aplikací.
   * - ``news_feed_cache_ttl``
     - ``3600``
     - Celé číslo nejméně ``600`` sekund; platnost čerstvé kopie v cache.
   * - ``news_feed_cache_key_prefix``
     - ``news_feed``
     - 1 až 64 písmen, číslic, dvojteček, podtržítek nebo pomlček.
   * - ``news_feed_timeout``
     - ``10``
     - Kladné konečné číslo v sekundách; timeout HTTP požadavku.
   * - ``news_feed_warning_rate_limit``
     - ``3600``
     - Kladné celé číslo v sekundách; minimální odstup opakovaného varování pro položku.

Inicializace
------------


Záznamy se vytvoří jednou datovou migrací při prvním spuštění ``manage.py migrate``
s touto verzí aplikace. Migrace doplní pouze chybějící položky; již uložené hodnoty,
včetně výšky bloku a URL zdroje, zachová. Pokud existující URL zdroje neodpovídá
novému výchozímu kanálu, migrace vypíše upozornění k ruční kontrole. Další nasazení
migraci znovu nespustí a běžný deployment nevyžaduje žádný inicializační příkaz.
Po vytvoření lze hodnoty spravovat v administraci ``CustomAdminSettings``.

Načítání a cache
----------------

Přihlášení načítá novinky pouze z cache a nikdy při něm nestahuje externí obsah.
Úlohu ``cron.tasks.load_news_feed`` spouští Celery asynchronně při zahřátí aplikace,
po změně nastavení ovlivňujícího stahování a periodicky. Nová položka se zobrazí po
úspěšném dokončení úlohy. Při chybě stahování zůstává dostupná poslední úspěšná
kopie stejného zdroje.

Klíče cache zahrnují nastavený prefix, jazyk a identitu normalizované URL. Změna
zdroje nebo prefixu proto nevrací obsah předchozího kanálu. Hodnota TTL pod
``600`` sekund je neplatná: administrace ji odmítne a historická neplatná hodnota
se při čtení zaloguje a nahradí výchozí hodnotou. Změna výšky bloku se projeví
v následujícím požadavku na přihlášení bez nového stahování. Změna TTL upraví
expiraci cache i periodický interval na ``TTL - 60`` sekund (nejméně ``540``
sekund). Změny se řadí podle aktuální uložené hodnoty; neúspěšné sladění se
zkusí znovu při startu aplikace. Existující duplicitní interval Beat se znovu
použije bez chyby. Invalidace se provádí po potvrzení databázové transakce a
nemaže nesouvisející záznamy Redis.

.. warning::

   Datová migrace se spouští v rámci běžného kroku ``migrate`` při prvním nasazení
   této verze. Před nasazením v živém prostředí ověřte cílovou databázi a ponechte
   si původní administrační hodnoty pro případ návratu.
