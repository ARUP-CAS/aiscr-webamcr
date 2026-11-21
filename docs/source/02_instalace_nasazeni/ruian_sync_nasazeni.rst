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

* **nový celery kód před dokončením** ``heslar.0014`` – čte geometrie ještě
  v EPSG:4326 jako EPSG:5514;
* **starý kód po** ``heslar.0014`` – dotazy na katastr podle bodu tiše
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

1. ``heslar.0014_ruian_geom_srid_5514`` – převede ``hranice``
   a ``definicni_bod`` u krajů, okresů a katastrů z EPSG:4326 na EPSG:5514.
   Čte i zapisuje po dávkách přes dočasnou tabulku, ale celý krok je jedna
   transakce: mezi zahozením a naplněním geometrie tabulky geometrii nemají,
   takže commit uprostřed by při pádu nechal hesláře prázdné.
2. ``pian.0008_pian_geom_sjtsk_povinny`` – dopočítá chybějící
   ``Pian.geom_sjtsk`` a teprve pak sloupec zpřísní na ``NOT NULL``. Backfill
   commituje po dávkách po 1000 řádcích a na tu dobu vypíná trigger
   ``trg_validate_geometries``; vypnutí i zapnutí jsou krátké samostatné
   transakce, aby se ``ACCESS EXCLUSIVE`` na ``pian`` nedržel po celý běh.

Plný sync zapisuje geometrie v EPSG:5514, které sloupce před migrací ``0014``
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
pokračuje následujícím dnem. Je to **poslední den, jehož změny SHP snapshot
jistě obsahuje** – den před vygenerováním ``1.zip``.

U ``1.zip`` staženého přímo od ČÚZK se ``--valid-to`` **nezadává**: příkaz
ho odvodí sám a vypíše (``kotva bude …``). Odvození věří časům souborů
v archivu – **archiv přebalený nebo získaný odjinud** může nést pozdější časy,
než odpovídá jeho obsahu, a kotva by pak přeskočila dny, které neobsahuje.
``--valid-to`` proto zadejte ručně:

* u přebaleného archivu nebo archivu neznámého původu;
* u rozbaleného adresáře (tam je povinné);
* když chcete kotvu záměrně dřívější.

``1.zip`` má stálou URL a nedatovaný název, datum vygenerování ale nesou časy
souborů uvnitř archivu (např. ``1/OKRESY_P.shp`` 2026-11-10 20:27). ČÚZK
archiv generuje večer, ale změny ze změnového souboru téhož dne v něm ještě
nejsou (ověřeno na archivu z 12. 10. 2026: obsahoval změny z 1.–10. 10.,
změny z ``20261012_ST_ZKSH`` ne), proto platí den předtím. Archiv vygenerovaný 13. 8. tedy připouští
``--valid-to`` nejvýš 2026-08-12. ``YYYYMMDD_ST_UZSZ.xml.zip`` dodává jen
definiční body a vychází řidčeji, takže je běžně starší než SHP – ÚZSZ
z 31. 7. spolu s ``--valid-to`` 2026-08-12 je správná kombinace.

Příkaz kontroluje:

* ``--valid-to`` v budoucnosti **odmítne**;
* ``--valid-to`` pozdější než den před vygenerováním ``1.zip`` **odmítne**.
  U rozbaleného adresáře datum zjistit nejde (časy souborů určilo rozbalení),
  příkaz u zadané hodnoty jen upozorní a bez ní skončí chybou;
* kotvu, po které by denní sync navazoval změnovým souborem starším než
  retence ČÚZK (92 dnů), **odmítne** – zadanou ručně, odvozenou i u
  rozbaleného adresáře. Takový soubor už na serveru není a kotva by se nikdy
  neposunula; hlídač stáří dat v cronu by to nezachytil, protože sleduje
  nejnovější kotvu;
* ÚZSZ novější než ``--valid-to`` vypíše varování – definiční body by
  pocházely z pozdějšího stavu, než jaký se ukládá jako kotva;
* ÚZSZ starší o víc než 60 dnů vypíše varování – katastrům vzniklým mezitím
  mohou chybět definiční body a dopočítají se z centroidu hranice.

Proč na tom záleží: kotva pozdější, než jaký stav ``1.zip`` obsahuje,
přeskočí denní změny za rozdílové dny a hlídač stáří dat se neozve. Na testu
plný sync s ``1.zip`` vygenerovaným 12. 10. 2026 a kotvou 12. 10. vynechal
změnový soubor z 12. 10.; Luhačovice zůstaly ve starém stavu, zatímco
sousední Ludkovice a Biskupice dostaly novou hranici o dva dny později, a
katastry se překrývaly. Dřívější datum je naopak neškodné – cron jen zopakuje dny,
které už v datech jsou – ale **jen v rámci retence** změnových souborů ČÚZK
(92 dnů). Dny starší cron už nestáhne a kotva se neposune; kotvu mimo
retenci proto příkaz odmítne.

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

Audit běhů v administraci
-------------------------

Výpis ``/admin/heslar/ruiansyncrun/`` ukazuje u každého běhu sloupec ⚠
(varování, viz níže); detail běhu (``/admin/heslar/ruiansyncrun/<id>/change/``)
má tři textová pole:

* ``error`` – u **neočekávaného selhání** (``status='failed'``) traceback.
  U známých stavů nemusí traceback obsahovat: běh uzavřený po zabití procesu
  nese pevnou větu o přerušení a den, jehož soubor ČÚZK ještě nevydal
  (``not_published_yet (404)``), je ``failed`` s prázdným ``error``;
* ``warnings`` – nálezy, které je třeba **prověřit**: díry nebo překryvy
  v pokrytí, nesoulad ploch úrovní, nesmazatelné prvky, selhaný přepočet
  navázaných záznamů. Většina z nich běh nezastaví; výjimkou je předletová
  kontrola plného syncu (``RuianNeuplnyZdrojError``), která sem zapíše důvod
  zastavení a běh skončí ``failed``. Sloupec ⚠ ve výpisu ukazuje jejich
  počet a po najetí myší i text. Varování z hlubších vrstev (parser,
  stahování, přepočet jednotlivých záznamů, výrazná změna hranice) se
  zapisují jako **souhrn** – jeden řádek za druh události s počtem výskytů,
  několika příklady a v hranatých závorkách klíčem události, podle kterého
  se jednotlivé výskyty dohledají v logu (Kibana);
* ``note`` – **informativní** poznámka bez nutnosti zásahu, např.
  ``no_changes (404)`` (den bez změn), ``not_published_yet (404)`` (ČÚZK
  soubor ještě nevydal), ``opakovani_po_selhani`` (den se opakuje po dřívějším
  selhání) nebo ``uzsz=…`` (soubor ÚZSZ použitý plným syncem).

Úspěšný běh s ⚠ tedy proběhl celý, ale některá kontrola něco našla.

Katastr bez hranice ve změnovém souboru
---------------------------------------

Při slučování katastrálních území pošle ČÚZK nástupci novou hranici, která
zahrnuje celé území rušeného katastru, a rušený katastr ještě **bez hranice**;
formální zánik (``ZaniklePrvky``) přijde až později. Tak to proběhlo 4. 11. 2026
u Nových Petrovic sloučených do Okříšek.

Denní sync takový katastr smaže hned, pokud jeho dosavadní území z alespoň
95 % pokryjí ostatní katastry v databázi – včetně hranic uložených ze
zpracovávaného souboru, takže nevadí, když nástupce dostal novou hranici
v souboru jiného dne. Navázané záznamy se přitom přepočítají na nástupce. Katastr tak z výběrů v AMČR zmizí
dřív, než úředně zanikne, a pozdější zánik už nic nenajde. Do ``warnings`` se
zapíše řádek „… bere se jako zrušený a maže se“.

Když pokrytí nestačí, hranice se ponechá a ve ``warnings`` je řádek „… hranice
ponechána, zkontrolujte“ – může jít o vadný export a je třeba ho prověřit.
Katastr bez hranice, který v databázi není, se nezakládá (hranice je povinná).
Totéž platí pro nový katastr, jehož hranici sync nedokázal načíst (nepodporovaný
GML, neplatná geometrie) – ve ``warnings`` je řádek „… hranici se nepodařilo
načíst – nezaložen“.

Kontrola pokrytí po zrušení nepočítá jako díru tu část území, kterou pokrývají
sousedé – i když nástupce dostal novou hranici v souboru dřívějšího dne.
Ohlásí se jen zbytek, který nepokrývá žádný katastr.

**Návrat na starší verzi.** Mazání neprobíhá v jedné transakci: když den
selže až po smazání takového katastru (typicky jiný katastr nejde smazat kvůli
navázaným záznamům, ``RuianNesmazatelnyKatastrError``), smazání zůstane
zapsané a cron den zopakuje. Taková chyba se ale opakuje při každém pokusu,
dokud se **neopraví záznamy, které smazání blokují** – teprve pak den doběhne.
Verze bez této logiky (před PR #4508) by při opakování smazaný katastr bez
hranice zakládala znovu a selhala na povinné hranici; nic by přitom nezapsala,
jen by další dny neprošly. Po takovém selhání proto den **dokončete touto
verzí** (po opravě blokujících záznamů), než se vrátíte ke starší nebo pustíte
souběžně staré workery. Když už starší verze běží, stačí nasadit tuto a nechat
cron den zopakovat; ruční oprava dat je potřeba, jen když den touto verzí
dokončit nejde.

**Den sloučení zpracovaný starší verzí.** Pravidlo 95 % se uplatní jen při
zpracování dne. Den, který před nasazením této verze **úspěšně** uzavřela
starší verze, se znovu nevyhodnotí: cron pokračuje až po kotvě a rušenému
katastru zůstala stará hranice, která se překrývá s nástupcem (tak to vypadá
po 4. 11. 2026 u Nových Petrovic a Okříšek, pokud den zpracovala starší verze).
Po nasazení ověřte dotazem, které katastry z větší části překrývá jiný::

    SELECT a.kod, a.nazev, b.kod AS kod_prekryva, b.nazev AS nazev_prekryva,
           round((ST_Area(ST_Intersection(a.hranice, b.hranice)) / ST_Area(a.hranice) * 100)::numeric, 1) AS pct
    FROM ruian_katastr a
    JOIN ruian_katastr b ON a.id <> b.id AND ST_Intersects(a.hranice, b.hranice)
    WHERE ST_Area(ST_Intersection(a.hranice, b.hranice)) > 0.5 * ST_Area(a.hranice)
    ORDER BY pct DESC;

V čistém stavu nevrátí nic. Nalezený katastr se dořeší jednou z cest:

* **počkat na formální zánik** – ``ZaniklePrvky`` v pozdějším změnovém souboru
  katastr smaže běžnou cestou a navázané záznamy přepočítá; do té doby
  zůstává překryv;
* **plný sync** z čerstvého ``1.zip`` – SHP katastr bez hranice neobsahuje,
  takže ho plný sync smaže jako chybějící ve snapshotu. Plný sync ale
  nevyhodnocuje pokrytí: ověřte předem, že katastr v ``KATUZE_P`` opravdu
  chybí, jinak se nic nezmění.

**Chybně zrušený katastr.** Pravidlo 95 % smaže katastr ještě před formálním
zánikem a jeho navázané záznamy (projekty, AZ, SN, neidentifikované akce)
přepočítá na sousedy a zapíše jim historii. Kdyby se ukázalo, že šlo o vadný
export a katastr dál existuje:

* **jak se to pozná** – ve ``warnings`` běhu je řádek „… bere se jako
  zrušený a maže se“ (v logu událost
  ``heslar.ruian_sync.syncer._vyhodnot_katastry_bez_hranice.zrusen``), ale
  katastr se později znovu objeví ve změnovém souboru nebo ho dál obsahuje
  ``KATUZE_P`` v aktuálním ``1.zip``;
* **opakování dne nepomůže** – katastr už v databázi není, takže sync jen
  zapíše varování „… v databázi není – nezaložen“ a nic neobnoví;
* **obnova:** ověřte, že kód katastru je v ``KATUZE_P`` čerstvého ``1.zip``,
  a spusťte plný sync – katastr se založí znovu. Navázané záznamy se tím
  nevrátí: v Django shellu spusťte ``reassign_all()`` z
  ``heslar.ruian_sync.reassign``. Ten přepočítá hlavní katastr projektů
  s ``geom``, katastr SN s ``geom`` a u AZ s první DJ jinou než celokatastr
  hlavní katastr i M2M ``katastry``; změněným záznamům aktualizuje metadata
  ve Fedoře. ``reassign_all()`` nepřepočítá záznamy bez vlastní geometrie
  (projekty bez ``geom``, AZ, jejichž DJ nemají PIAN), AZ, jejichž první DJ
  je typu celokatastr, ani M2M ``katastry`` projektů (při mazání se v nich
  katastr nahradil nástupcem); neidentifikované akce neřeší vůbec. Všechny
  tyto záznamy dohledejte podle historie změny katastru z data chybného
  běhu a opravte ručně.

Před prvním denním syncem po nasazení této verze je rozumné mít čerstvou
zálohu databáze – obnova z ní je nejkratší cesta zpět.

Když plný sync selže
--------------------

Plný sync není atomický: upserty a mazání probíhají po prvcích a metadata se
zapisují do Fedory. Rollback databáze do stavu před během proto **neexistuje**
a obnova se dělá dopředu:

1. Zjistit z auditu, kde běh skončil – ``RuianSyncRun`` s ``status='failed'``
   nese v ``error`` traceback; zastavila-li ho předletová kontrola, je důvod
   navíc čitelně ve ``warnings``.
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
nedá dohnat stahováním – jakmile první zameškaný den (kotva + 1) vypadne
z retence, hlásí to ``ERROR`` ``mimo_retenci_zdroje`` a jedinou cestou zpět je
plný sync ze SHP. Stejné pravidlo (``kotva_mimo_retenci``) kontroluje i
``--valid-to`` plného synchu.
