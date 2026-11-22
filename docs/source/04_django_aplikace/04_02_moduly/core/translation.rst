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

.. py:function:: _reload_translation_catalogs(fingerprint)

   Znovu načte překladové katalogy procesu metodou „sestavit, pak vyměnit“.

   Před sestavením uloží obě mezipaměti, výchozí katalog a přesný stav aktivního jazyka.
   Sestaví každý jazyk (výchozí jako první) a znovu ověří metadata souborů. Změnila-li se,
   kandidáta odmítne. Jinak vynuluje výchozí katalog a obnoví aktivaci stejného jazyka nad
   novými objekty. Při chybě včetně dokončení aktivace obnoví celý původní stav a výjimku
   předá volajícímu, který ji zachytí a zapíše varování.

   :param fingerprint: Otisk očekávaných katalogů pořízený před sestavením.
   :return: ``True`` při úspěšném načtení.
   :raises Exception: Chyba sestavení nebo dokončení aktivace; původní stav se obnoví.

.. py:function:: reload_translation_catalogs_if_changed()

   Ověří, zda se změnily runtime překladové katalogy, a případně je v procesu znovu načte.

   Kontrola proběhne nejvýše jednou za ``settings.TRANSLATION_CATALOG_CHECK_INTERVAL``
   sekund (``0`` = při každém volání, ``None`` = mechanismus vypnut). Porovná otisk souborů
   ``django.mo`` s otiskem uloženým při posledním úspěšném načtení. První kontrola zkusí
   načíst přítomné katalogy i bez změny, protože proces je mohl načíst před aktualizací
   (např. Celery spuštěné souběžně s nasazením). Metadata se porovnají před sestavením i po něm;
   zjištěná změna odmítne kandidáta a zachová původní překlady. Dvojice kontrol nezaručuje
   konzistentní snímek souborů: změna tam a zpět se shodnými metadaty může uniknout.

   Chybí-li některý očekávaný ``django.mo``, nebo se katalogy nepodaří načíst, proces
   ponechá dříve načtené katalogy, zapíše jedno varování a otisk si uloží jako neúspěšný.
   Změněný otisk dovolí další pokus při běžné kontrole; shodný neúspěšný stav se zkusí
   znovu nejdřív za 300 sekund od posledního pokusu. Další selhání stejného stavu se
   nelogují. Úspěch nebo návrat k již načtenému otisku neúspěšný stav vymaže. Stejná
   prodleva platí pro chybu před zjištěním otisku. Neočekávané výjimky neuniknou do
   požadavku ani úlohy a chyba po změně překladového stavu obnoví původní objekty.

   Obnova bez změny metadat může čekat na prodlevu i na další interval kontroly;
   nečinný proces čeká až na požadavek či úlohu. Nezměněný chybný katalog tak stojí
   nejvýše jeden pokus za pět minut v každém procesu. Novému procesu bez dříve
   načteného platného katalogu tento mechanismus nezaručí existenci starého překladu.

   :return: ``True``, pokud se katalogy znovu načetly, jinak ``False``.

.. py:function:: reload_translation_catalogs_on_task_prerun(sender)

   Přijímač signálu Celery ``task_prerun``: před spuštěním úlohy ověří runtime katalogy.

   Díky tomu úlohy (např. notifikační e-maily) překládají podle aktuálních katalogů
   i ve workeru, který katalogy načetl před nasazením nebo před úpravou na serveru.
   Pomocná funkce zachytí chyby kontroly i aktivace a zachová původní překlady.
   Celery navíc zachytává výjimky přijímačů signálů; samotná výjimka přijímače
   proto automaticky neoznačuje úlohu jako neúspěšnou.

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

   Každé přejmenování je atomické samostatně; nejde o transakci nad dvojicí katalogů.
   Selže-li náhrada ``.po``, publikovaná záloha zůstane. Selže-li následná náhrada ``.mo``,
   zůstane nové ``.po``, původní ``.mo`` a záloha původního ``.po``. Při zachycené chybě
   se zbývající dočasné soubory smažou. Obnova po ukončení procesu není zaručena.

   :param po_file_path: Cesta k nahrazovanému souboru ``.po``.
   :param uploaded_file: Nahraný soubor (``UploadedFile``), jehož obsah se zapíše do ``.po``.
   :return: Cesta k vytvořené záloze ``.po``.
   :raises Exception: Chyba načtení nahraného souboru, kompilace ``.mo`` nebo zápisu na disk;
       katalog zůstane beze změny, pokud chyba nastala před přejmenováním.

.. py:function:: connect_translation_catalog_signals()

   Připojí kontrolu runtime katalogů na signál Celery ``task_prerun``.

   Volá se z ``CoreConfig.ready()``; díky ``dispatch_uid`` je opakované volání bez účinku.
