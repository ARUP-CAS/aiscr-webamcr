Nasazení synchronizace RÚIAN
============================

Postup pro první nasazení přechodu katastrů na EPSG:5514 (issue #372) a pro
obnovu, když plný sync selže. Doplňuje :doc:`nasazovani` o kroky specifické
pro hesláře RÚIAN.

Pořadí migrací
--------------

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

Teprve po nich se spouští ``manage.py aktualizuj_ruian_shp``. Opačné pořadí
skončí chybou: plný sync zapisuje geometrie v EPSG:5514, které sloupce před
migrací ``0013`` nepřijmou.

Cron během plného synchu
------------------------

Plný sync trvá hodiny a **denní cron se s ním nesmí potkat**. Obojí se
serializuje advisory zámkem (``heslar.ruian_sync.zamek``), takže k tichému
souběhu dojít nemůže – ale znamená to, že jeden z nich bude odmítnut:

* běží-li plný sync, ``sync_ruian_changes`` se přeskočí s ``ERROR``
  ``lock_not_acquired``;
* běží-li cron, ``aktualizuj_ruian_shp`` skončí ``CommandError``.

Doporučený postup je cron na dobu plného synchu **zastavit** a pustit ho až
po jeho dokončení; zámek je pojistka proti omylu, ne náhrada plánování.

Hodnota ``--valid-to``
----------------------

``--valid-to`` se ukládá jako kotva ``RuianSyncRun.data_valid_to`` a cron od ní
pokračuje následujícím dnem. Musí odpovídat datu snapshotu v názvu souboru
``YYYYMMDD_ST_UZSZ.xml.zip``:

* pozdější hodnotu příkaz **odmítne** – přeskočila by denní změny a protože
  by kotva vypadala čerstvě, nespustil by se ani hlídač stáří dat;
* dřívější hodnota projde s varováním, cron jen zopakuje dny, které už ve
  snapshotu jsou.

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
