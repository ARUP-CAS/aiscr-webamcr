Nasazení synchronizace RÚIAN
============================

Postup pro první nasazení přechodu katastrů na EPSG:5514 (issue #372) a pro
obnovu, když plný sync selže. Doplňuje :doc:`nasazovani` o kroky specifické
pro hesláře RÚIAN.

Postup prvního nasazení
-----------------------

Webový kontejner spouští ``manage.py migrate`` sám ve vstupním skriptu
(``scripts/entrypoint.sh``), zatímco ``celery_worker`` a ``celery_beat``
startují nezávisle na něm. Při výchozím ``docker compose up`` by tak vznikla
tři okna, kdy nad databází běží kód jiné verze, než odpovídá jejímu schématu:

* **nový celery kód před dokončením** ``heslar.0013`` – čte geometrie ještě
  v EPSG:4326 jako EPSG:5514;
* **starý kód po** ``heslar.0013`` – dotazy na katastr podle bodu tiše
  nenajdou nic nebo najdou jiný katastr, protože geometrie už jsou v jiné
  soustavě;
* **jakýkoli kód během backfillu** ``pian.0008`` – trigger
  ``trg_validate_geometries`` je vypnutý, takže zapisovaná geometrie PIANu se
  nevaliduje.

Aplikace proto musí stát po celou dobu migrací:

1. Zastavit ``celery_beat``, ``celery_worker`` a webový kontejner (i starou
   verzi, pokud nasazení kontejnery nevyměňuje najednou).
2. Nasadit novou verzi a spustit **jen webový kontejner**; ten provede
   migrace. Počkat, až vstupní skript doběhne za ``migrate``.
3. Ověřit, že trigger zůstal zapnutý (viz `Trigger po migraci`_).
4. Spustit ``celery_worker``. ``celery_beat`` zatím **ne**.
5. Provést plný sync ``manage.py aktualizuj_ruian_shp`` (viz
   `Hodnota --valid-to`_).
6. Založit plánovanou úlohu denního synchu (viz `Plánování denního synchu`_)
   a teprve pak spustit ``celery_beat``.

Pořadí migrací
~~~~~~~~~~~~~~

Migrace musí projít **před** prvním plným syncem ze SHP, v tomto pořadí:

1. ``heslar.0013_ruian_geom_srid_5514`` – převede ``hranice``
   a ``definicni_bod`` u krajů, okresů a katastrů z EPSG:4326 na EPSG:5514.
   Čte i zapisuje po dávkách přes dočasnou tabulku, ale celý krok je jedna
   transakce: mezi zahozením a naplněním geometrie tabulky geometrii nemají,
   takže commit uprostřed by při pádu nechal hesláře prázdné.
2. ``pian.0008_pian_geom_sjtsk_povinny`` – dopočítá chybějící
   ``Pian.geom_sjtsk`` a teprve pak sloupec zpřísní na ``NOT NULL``. Backfill
   commituje po dávkách po 1000 řádcích a na tu dobu vypíná trigger
   ``trg_validate_geometries``; vypnutí i zapnutí jsou krátké samostatné
   transakce, aby se ``ACCESS EXCLUSIVE`` na ``pian`` nedržel po celý běh.

Plný sync zapisuje geometrie v EPSG:5514, které sloupce před migrací ``0013``
nepřijmou – opačné pořadí proto skončí chybou.

Trigger po migraci
~~~~~~~~~~~~~~~~~~

Zapnutí triggeru zpět je v ``finally``, takže ho obnoví i výjimka uprostřed
backfillu. **Nepokryje ale tvrdé ukončení procesu** (``SIGKILL``, OOM killer,
výpadek stroje): ``finally`` se pak nespustí a trigger zůstane vypnutý. Po
migraci proto ověřte, že je zapnutý:

.. code-block:: sql

   SELECT tgenabled FROM pg_trigger
   WHERE tgname = 'trg_validate_geometries' AND NOT tgisinternal;

Výsledek musí být ``O``. Hodnota ``D`` znamená vypnutý trigger. Správné
řešení je **spustit migraci znovu**: tvrdě ukončená migrace není zaznamenaná
jako hotová, takže proběhne celá, dokončí backfill a trigger na konci zapne.

Ruční zapnutí

.. code-block:: sql

   ALTER TABLE pian ENABLE TRIGGER trg_validate_geometries;

je jen **dočasná záplata, ne náhrada**. Migrace zůstane nezaznamenaná, takže ji
``entrypoint.sh`` spustí při příštím nasazení – a ta trigger na dobu backfillu
zase vypne, tentokrát nečekaně a za běhu aplikace. Po ručním zapnutí proto
migraci co nejdřív doběhněte podle postupu v `Postup prvního nasazení`_
(zastavená aplikace, pak ``migrate``).

Totéž hlídá test ``PianGeomTriggerTests.test_migrace_nechala_trigger_zapnuty``.

Hodnota ``--valid-to``
----------------------

``--valid-to`` se ukládá jako kotva ``RuianSyncRun.data_valid_to`` a cron od ní
pokračuje následujícím dnem. Uvádí se **poslední den, jehož změny SHP
snapshot obsahuje** – typicky den před stažením ``1.zip``.

Příkaz tuto hodnotu **nedokáže ověřit**, protože ji ze vstupů nejde odvodit:

* ``1.zip`` s polygony je nedatovaný – stejná URL vždy vrací aktuální stav;
* ``YYYYMMDD_ST_UZSZ.xml.zip`` dodává jen definiční body a vychází řidčeji,
  takže je běžně starší než SHP. ÚZSZ z 31. 7. spolu s ``--valid-to``
  2026-08-13 je správná kombinace, ne chyba.

Kontroluje se jen to, co ověřit jde:

* ``--valid-to`` v budoucnosti příkaz **odmítne**;
* ÚZSZ novější než ``--valid-to`` vypíše varování – definiční body by
  pocházely z pozdějšího stavu, než jaký se ukládá jako kotva;
* ÚZSZ starší o víc než 60 dnů vypíše varování – katastrům vzniklým mezitím
  mohou chybět definiční body a dopočítají se z centroidu hranice.

Hodnota pozdější, než jaký stav ``1.zip`` skutečně obsahuje, proto **projde
bez varování** a kotva přeskočí denní změny za rozdílové dny. Hlídač stáří
dat se neozve, protože kotva vypadá čerstvě. Když si nejste jistí, zadejte
raději dřívější datum: cron pak jen zopakuje dny, které už v datech jsou, což
je neškodné.

Cron během plného synchu
------------------------

Plný sync trvá hodiny a **denní cron se s ním nesmí potkat**. Obojí se
serializuje advisory zámkem (``heslar.ruian_sync.zamek``), takže k tichému
souběhu dojít nemůže – ale znamená to, že jeden z nich bude odmítnut:

* běží-li plný sync, ``sync_ruian_changes`` se přeskočí s ``ERROR``
  ``lock_not_acquired``;
* běží-li cron, ``aktualizuj_ruian_shp`` skončí ``CommandError``.

Doporučený postup je ``celery_beat`` na dobu plného synchu **zastavit** a pustit
ho až po jeho dokončení; zámek je pojistka proti omylu, ne náhrada plánování.

Plánování denního synchu
------------------------

Aplikace používá ``django_celery_beat.schedulers:DatabaseScheduler``, takže
plánované úlohy žijí v databázi a **žádný kód je nezakládá**. Úloha denního
synchu se musí vytvořit ručně v administraci (*Periodic tasks*):

* **Task:** ``cron.tasks.sync_ruian_changes``
* **Schedule:** crontab jednou denně v noci, např. ``0 4 * * *`` – ČÚZK
  publikuje změnový soubor za předchozí den během noci
* **Enabled:** ano

Bez téhle úlohy zůstanou katastry na stavu z plného synchu a **nic se
neozve**: všechny hlídače stáří dat (``dlouho_bez_dat``,
``mimo_retenci_zdroje``) běží uvnitř samotné úlohy. Po založení ověřte, že
se v ``RuianSyncRun`` druhý den objeví běh s ``triggered_by='cron'``.

Když plný sync selže
--------------------

Plný sync není atomický: upserty a mazání probíhají po prvcích a metadata se
zapisují do Fedory. Rollback databáze do stavu před během proto **neexistuje**
a obnova se dělá dopředu:

1. Zjistit z auditu, kde běh skončil – ``RuianSyncRun`` s ``status='failed'``
   nese v ``note`` důvod a v ``error`` traceback.
2. Ověřit, jestli běh zastavila předletová kontrola
   (``RuianNeuplnyZdrojError``). Pokud ano, **do dat se nesáhlo** – stačí
   opravit vstup a spustit znovu.
3. Jinak spustit ``aktualizuj_ruian_shp`` se stejnými parametry znovu. Sync je
   idempotentní: nezměněné prvky přeskočí a dokončí, co zbývá.
4. Po doběhnutí zkontrolovat v logu závěrečné kontroly
   (``_check_katastry_topology``): pokrytí, díry, překryvy a soulad ploch
   katastrů, okresů a krajů.
5. Metadata ve Fedoře, která se nestihla zapsat, dohnat příkazem
   ``manage.py generate_metadata`` pro dotčené identy; ty jsou v logu
   u hlášek ``metadata_nezapsana`` a ``rozpad_db_fedora``.

Retence zdrojových dat
----------------------

ČÚZK drží denní změnové soubory jen **3 měsíce zpět** (změřeno 8. 9. 2026:
``-92 dní`` HTTP 200, ``-93 dní`` 404). Delší výpadek denního synchu se proto
nedá dohnat stahováním – hlásí ho ``ERROR`` ``mimo_retenci_zdroje`` a jedinou
cestou zpět je plný sync ze SHP.
