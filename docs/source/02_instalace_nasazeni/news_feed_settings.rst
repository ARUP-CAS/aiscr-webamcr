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
     - 1 až 64 znaků; první musí být písmeno ASCII nebo číslice,
       další mohou obsahovat také dvojtečku, podtržítko a pomlčku.
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

Současně migrace vytvoří nebo přenastaví úlohu Celery Beat ``load-news-feed``.
Nastaví volání ``cron.tasks.load_news_feed`` a interval podle TTL, zapne úlohu,
nahradí poziční argumenty prázdným seznamem a pojmenované argumenty prázdným
slovníkem, odstraní alternativní plán crontab, solar či clocked a vypne příznak
``one_off``. Toto přenastavení proběhne pouze při migraci; následné sladění plánu
zachovává níže popsaná nastavení operátora.

Načítání a cache
----------------

Přihlášení načítá novinky pouze z cache a nikdy při něm nestahuje externí obsah.
Při zahřátí aplikace spustí vstupní skript úlohu ``cron.tasks.load_news_feed``
přímo v samostatném procesu ``nohup python manage.py shell``. Po změně nastavení
ovlivňujícího stahování se úloha odešle do fronty Celery; periodická spuštění
zajišťuje databázový plánovač Celery Beat. Nová položka se zobrazí po úspěšném
dokončení úlohy. Zdroj musí vracet JSON přímo; HTTP přesměrování se nenásledují
a odpovědi 3xx se zpracují jako neúspěšné načtení.
Při chybě stahování se zobrazí dostupná čerstvá kopie; pokud chybí nebo je
prázdná, použije se poslední úspěšná neprázdná kopie stejného zdroje, pokud je
dostupná v cache. Její platnost je 30 dní od posledního
úspěšného neprázdného načtení. Platný, ale prázdný kanál tuto dobu neprodlužuje;
přihlašovací stránka i v tomto případě zobrazuje poslední neprázdnou kopii,
dokud je dostupná. Pokud taková kopie chybí nebo vypršela a čerstvá kopie je
prázdná či nedostupná, novinky se nezobrazí.

Klíče cache zahrnují nastavený prefix, jazyk a identitu normalizované URL. Změna
zdroje nebo prefixu proto nevrací obsah předchozího kanálu. Hodnota TTL pod
``600`` sekund je neplatná: administrace ji odmítne a historická neplatná hodnota
se při čtení zaloguje a nahradí výchozí hodnotou. Změna výšky bloku se projeví
v následujícím požadavku na přihlášení bez nového stahování. Změna TTL upraví expiraci cache. U intervalového plánu se perioda odvozuje jako
``TTL - 60`` sekund (nejméně ``540`` sekund); vlastní crontab, solar nebo clocked
plán má přednost. Sladění zachovává povolení úlohy a její argumenty. Neúspěšné
sladění se zkusí znovu při startu a dalším načtení novinek. Vypnutí úlohy v Beat
zastaví periodická spuštění, nikoliv zahřátí při startu ani obnovu po změně
nastavení. Nezměněný plán nevyvolá oznámení plánovači. Existující duplicitní interval Beat se znovu
použije bez chyby. Invalidace se provádí po potvrzení databázové transakce a
nemaže nesouvisející záznamy Redis.

.. warning::

   Datová migrace se spouští v rámci běžného kroku ``migrate`` při prvním nasazení
   této verze. Před nasazením v živém prostředí ověřte cílovou databázi a ponechte
   si původní administrační hodnoty i stav úlohy ``load-news-feed``: povolení,
   volanou úlohu, typ a hodnoty plánu, argumenty a příznak ``one_off``.
   Zpětná migrace tyto hodnoty automaticky neobnoví.
