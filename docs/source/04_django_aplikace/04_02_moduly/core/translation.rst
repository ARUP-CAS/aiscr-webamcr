CORE translation
================

Modul translation.

Funkce
------

.. py:function:: format_message(message_id)

   Přeloží zprávu s pojmenovanými zástupnými znaky a dosadí do ní parametry.

   Překlad drží celou větu (``{child}``, ``{field}`` …), takže pořadí slov řídí překladatel,
   ne skládání fragmentů v kódu. Chybí-li překlad (``gettext`` vrátí ID doslova), parametry se
   připojí za ID ve tvaru ``klíč=hodnota``, aby se informace ze zprávy neztratila. Překlad
   s neznámým zástupným znakem se vrátí bez dosazení místo vyvolání výjimky.

   Volající označí ID pomocí ``gettext_noop``, aby ho ``makemessages`` extrahoval.

   :param message_id: Překladové ID zprávy.
   :param params: Hodnoty pro zástupné znaky v přeložené zprávě.
   :return: Přeložená zpráva s dosazenými hodnotami.

.. py:function:: _catalog_paths()

   Vrátí cesty k runtime katalogům ``django.mo`` pro všechny jazyky z ``settings.LANGUAGES``.

   Prochází každou cestu z ``settings.LOCALE_PATHS`` a pro každý jazyk sestaví cestu
   ``<cesta>/<locale>/LC_MESSAGES/django.mo``; existenci souborů neověřuje.

   :return: Seznam absolutních nebo relativních cest tak, jak vyplývají z nastavení.

.. py:function:: _catalog_fingerprint()

   Sestaví otisk runtime katalogů z metadat souborů.

   Pro každý katalog uloží ``(st_mtime_ns, st_size, st_ino)``; inode zachytí i atomické
   nahrazení souboru přejmenováním, u kterého by změna času nemusela být rozlišitelná.
   Chybějící nebo nedostupný soubor má v otisku hodnotu ``None``.

   :return: N-tice dvojic ``(cesta, metadata)`` v pořadí podle ``_catalog_paths``.

.. py:function:: _ordered_language_codes()

   Vrátí kódy jazyků z ``settings.LANGUAGES`` s výchozím jazykem na prvním místě.

   Výchozí jazyk se sestavuje jako první, aby případné záložní katalogy dalších jazyků
   (Django je bere z výchozího jazyka) vznikly už z nově načteného katalogu.

   :return: Seznam kódů jazyků bez duplicit.

.. py:function:: _reload_translation_catalogs()

   Znovu načte překladové katalogy procesu metodou „sestavit, pak vyměnit“.

   Uloží stávající mezipaměti ``gettext._translations`` a ``trans_real._translations``,
   vyprázdní mezipaměť modulu ``gettext`` a pro každý jazyk z ``settings.LANGUAGES``
   (výchozí jako první) sestaví nový překladový objekt. Teprve když se všechny katalogy
   podaří načíst, zůstanou nové objekty v platnosti, vynuluje se ``trans_real._default``
   a je-li v aktuálním kontextu aktivní jazyk, aktivuje se znovu se stejným kódem, aby
   ukazoval na nový katalog. Při jakékoli výjimce během sestavení (např. rozepsaný,
   poškozený nebo nečitelný ``django.mo``) obnoví obě původní mezipaměti, zapíše varování
   a proces dál používá dříve načtené katalogy. Chybějící soubor výjimku nevyvolá (Django
   ho nahradí prázdným katalogem), proto ho zachytí už volající
   ``reload_translation_catalogs_if_changed`` a tuto funkci vůbec nezavolá.

   :return: ``True`` při úspěšném načtení, ``False`` když se původní katalogy ponechaly.

.. py:function:: reload_translation_catalogs_if_changed()

   Ověří, zda se změnily runtime překladové katalogy, a případně je v procesu znovu načte.

   Kontrola proběhne nejvýše jednou za ``settings.TRANSLATION_CATALOG_CHECK_INTERVAL``
   sekund (``0`` = při každém volání, ``None`` = mechanismus vypnut). Porovná otisk souborů
   ``django.mo`` s otiskem uloženým při posledním úspěšném načtení; první kontrola v procesu
   načítá vždy, protože proces mohl katalogy načíst ještě před jejich aktualizací (např.
   Celery spuštěné souběžně s nasazením). Otisk se pořizuje před načtením, takže zápis
   během načítání vyvolá při další kontrole jen jedno nadbytečné načtení, nikoli
   přehlédnutou změnu.

   Chybí-li některý očekávaný ``django.mo``, nebo se katalogy nepodaří načíst, proces
   ponechá dříve načtené katalogy, zapíše jedno varování a otisk si uloží jako neúspěšný.
   Dokud se soubory znovu nezmění, další kontroly nic nenačítají ani nelogují; jakýkoli
   další zápis (dokončení zápisu z Rosetty, obnova souboru) změní otisk a načtení se
   zkusí znovu.

   :return: ``True``, pokud se katalogy znovu načetly, jinak ``False``.

.. py:function:: reload_translation_catalogs_on_task_prerun(sender)

   Přijímač signálu Celery ``task_prerun``: před spuštěním úlohy ověří runtime katalogy.

   Díky tomu úlohy (např. notifikační e-maily) překládají podle aktuálních katalogů
   i ve workeru, který katalogy načetl před nasazením nebo před úpravou na serveru.

   :param sender: Úloha, která se spouští (signál ji předává, kontrola ji nepoužívá).
   :param kwargs: Další argumenty signálu ``task_prerun`` (``task_id``, ``task``, ``args`` …).

.. py:function:: _prepare_temporary_file(target_path, write_content, mode_source)

   Připraví obsah pro pozdější atomickou náhradu souboru ``target_path``.

   Funkce ``write_content`` zapíše obsah do dočasného souboru ve stejném adresáři jako cíl
   (jen tak je následné přejmenování atomické). Dočasný soubor převezme práva souboru
   ``mode_source`` (výchozí je cílový soubor); když neexistuje, dostane ``0o644``. Při chybě
   se dočasný soubor smaže a výjimka se předá dál.

   :param target_path: Cesta k souboru, který se má později nahradit.
   :param write_content: Funkce, která dostane cestu dočasného souboru a zapíše do něj obsah.
   :param mode_source: Soubor, jehož práva dočasný soubor převezme; ``None`` = cílový soubor.
   :return: Cesta k připravenému dočasnému souboru.

.. py:function:: replace_file_atomically(target_path, write_content)

   Nahradí soubor v jednom kroku, aby žádný proces nenačetl rozepsaný obsah.

   Obsah připraví ``_prepare_temporary_file`` v dočasném souboru ve stejném adresáři a ten se
   pak přes ``os.replace`` přejmenuje na cílovou cestu. Při chybě se dočasný soubor smaže,
   cílový soubor zůstane beze změny a výjimka se předá dál.

   :param target_path: Cesta k nahrazovanému souboru.
   :param write_content: Funkce, která dostane cestu dočasného souboru a zapíše do něj obsah.

.. py:function:: import_translation_catalog(po_file_path, uploaded_file)

   Nahradí runtime katalog nahraným souborem a zkompiluje k němu ``.mo``.

   Import probíhá ve dvou fázích. Při přípravě se v adresáři katalogu vytvoří tři dočasné
   soubory: nahraný soubor (zapsaný jen jednou a z tohoto souboru načtený knihovnou
   ``polib``), ``.mo`` zkompilovaný z něj a kopie stávajícího ``.po`` pro zálohu. Selže-li
   cokoli z toho (včetně souboru, který ``polib`` nedokáže načíst), dočasné soubory se smažou
   a katalog ani seznam záloh se nezmění. Teprve když je vše připravené, přejmenují se
   dočasné soubory bezprostředně po sobě na zálohu ``<název>_backup_<ddmmYYYYHHMMSS>.po``
   (název rozpozná seznam záloh), na ``.po`` a na sousední ``.mo``. Běžící procesy tak nikdy
   nenačtou rozepsaný katalog a změnu převezmou při další kontrole katalogů.

   :param po_file_path: Cesta k nahrazovanému souboru ``.po``.
   :param uploaded_file: Nahraný soubor (``UploadedFile``), jehož obsah se zapíše do ``.po``.
   :return: Cesta k vytvořené záloze ``.po``.
   :raises Exception: Chyba načtení nahraného souboru, kompilace ``.mo`` nebo zápisu na disk;
       katalog zůstane beze změny, pokud chyba nastala před přejmenováním.

.. py:function:: connect_translation_catalog_signals()

   Připojí kontrolu runtime katalogů na signál Celery ``task_prerun``.

   Volá se z ``CoreConfig.ready()``; díky ``dispatch_uid`` je opakované volání bez účinku.
