Přesnost souřadnicových systémů
===============================

Definovaná přesnost
-------------------

Zadání
~~~~~~

Nastavit maximální přesnost pomocí přípustných řádů v daném souřadném systému, a to max na úrovni cm - zbytek lze ořezávat (zbytečně skladujeme falešně "přesná" data):

* WGS-84 - 7 řádů
* S-JTSK - 2 řády

Databáze AMČR oblast dat
~~~~~~~~~~~~~~~~~~~~~~~~~

* ``public.samostatny_nalez`` (geom: 7 míst, geom_sjtsk: 2 místa)
* ``public.dokument_extra_data`` (geom: 7 míst)
* ``public.projekt`` (geom: 7 míst)
* ``public.pian`` (geom: 7 míst, geom_sjtsk: 2 místa)

Použitý mechanismus
--------------------

Hlavní varianta uložení
~~~~~~~~~~~~~~~~~~~~~~~

1. Přesnost zobrazených dat je stanovena zadáním, reálná geometrie pak může vzniknout pouze dvěma způsoby
2. Při vytváření nebo editaci nové geometrie (pouze WGS-84, projekce je WorldMercator) vzniká v AMČR nejprve geometrie s vyšší přesností (přesnost datového typu double) v externí komponentě `leaflet <https://leafletjs.com/>`_, tato geometrie se vždy nejprve převede na geometrii s požadovanou přesností (zaokrouhlením na požadovaný počet platných číslic) a formátu `WKT <https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry>`_
3. Jako navazující krok se provede transformace s WGS-84 do S-JTSK, tato transformace je přesná a rychlá a provede se přímo ve webovém prohlížeči. Transformovaná geometrie je též reprezentována ve formátu WKT a je zaokrouhlena na požadovaný počet míst.
4. Při požadavku uložení formuláře na uložení geometrie se z webového prohlížeče přímo posílají "hotové" WKT geometrie na AMČR server. Tyto geometrie se nejprve zvalidují a pokud jsou validní tak se ještě provede duplicitní zaokrouhlení a uložení do databáze.

Hlavní varianta čtení
~~~~~~~~~~~~~~~~~~~~~

1. Data se z DB čtou v "neomezené" přesnosti (tedy tak jak jsou uložena) a v tomto tvaru se též posílají ve formátu WKT na webového klienta
2. Na webovém klientu se geometrická data nejprve zobrazí a pouze v případě, následné editace se zaokrouhlují.
3. Daný mechanismus "neničí" přesnost a topologii dat, která vznikla mimo AMČR

Alternativní varianta zápisu geometrie
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Dále je možné zadávat souřadnice geometrie (v současnosti pouze bod samostatného nálezu) přímo do textových polí pro s.s. WGS-84/S-JTSK.
2. Tato textová pole neumožňují zadání s vyšší přesností a provedou buďto přepis nebo oříznutí poslední číslice. Pro S-JTSK souřadnici ``-690995.19`` je při vložení 2 přímo za číslo 1 vytvořeno číslo ``-690995.12`` nikoliv ``-690995.3`` a při vložení 8 za 9 by došlo ``-690995.19`` se číslice nezmění.
3. Pokud uživatel zadá souřadnice ve WGS-84 o alternativní způsob zápisu geometie se nejedná. Pouze pokud uživatel zadá přímo souřadnice S-JTSK je automaticky zavolána konverze AMČR (proxi na služby INSPIRE ČÚZK) z S-JTSK do WGS-84. Po získání souřadnic WGS-84 se zobrazí na mapě AMČR pin. Pokud není dostupná služba ČÚZK provede se alternativní méně přesná transformace s upozorněním uživatele.
4. Při následném uložení geometrie do DB se navíc posílá příznak, že geometrie vznikla transformací ze systému S-JTSK ``sjtsk`` nebo nepřesnou transformací ``sjtsk*``.

Alternativní varianta čtení
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Pokud geometrie má v DB příznak geom. systému na ``sjtsk`` nebo ``sjtsk*`` tak se uživately zobrazí jako defaultní zobrazení "S-JTSK"
2. Informace o přesnosti transformace se na klientu nezobrazují, ale dále se používají, při změněn negeometrických atributů, pro daný záznam.

Migrace přesnosti pro stávající DB
-----------------------------------

Pro migraci přesnosti stávajících dat je použita funkce `ST_ReducePrecision <https://postgis.net/docs/ST_ReducePrecision.html>`_.

Ukázka použití
~~~~~~~~~~~~~~

.. code-block:: sql

   SELECT ST_AsText(ST_ReducePrecision('POINT(1.412 19.323)', 0.1));
       st_astext
   -----------------
    POINT(1.4 19.3)

Provedené migrace
~~~~~~~~~~~~~~~~~

Samostatný nález
^^^^^^^^^^^^^^^^

WGS-84:

.. code-block:: sql

   -- Vyhledat
   SELECT st_astext(geom) FROM public.samostatny_nalez
   WHERE geom IS NOT NULL and st_astext(geom)<>st_astext(ST_ReducePrecision(geom,0.0000001));

   -- Nahradit
   UPDATE public.samostatny_nalez SET geom=ST_ReducePrecision(geom,0.0000001)
   WHERE geom IS NOT NULL and st_astext(geom)<>st_astext(ST_ReducePrecision(geom,0.0000001));

   -- Kontrola
   SELECT st_astext(geom),ident_cely FROM public.samostatny_nalez
   WHERE ST_IsValid(geom)='false';

S-JTSK:

.. code-block:: sql

   -- Vyhledat
   SELECT st_astext(geom_sjtsk) FROM public.samostatny_nalez
   WHERE geom_sjtsk IS NOT NULL and st_astext(geom_sjtsk)<>st_astext(ST_ReducePrecision(geom_sjtsk,0.01));

   -- Nahradit
   UPDATE public.samostatny_nalez SET geom_sjtsk=ST_ReducePrecision(geom_sjtsk,0.01)
   WHERE geom_sjtsk IS NOT NULL and st_astext(geom_sjtsk)<>st_astext(ST_ReducePrecision(geom_sjtsk,0.01));

   -- Kontrola
   SELECT st_astext(geom_sjtsk),ident_cely FROM public.samostatny_nalez
   WHERE ST_IsValid(geom_sjtsk)='false'

Dokument 3D
^^^^^^^^^^^

WGS-84:

.. code-block:: sql

   -- Vyhledat
   SELECT st_astext(geom) FROM public.dokument_extra_data
   WHERE geom IS NOT NULL and st_astext(geom)<>st_astext(ST_ReducePrecision(geom,0.0000001));

   -- Nahradit
   UPDATE public.dokument_extra_data SET geom=ST_ReducePrecision(geom,0.0000001)
   WHERE geom IS NOT NULL and st_astext(geom)<>st_astext(ST_ReducePrecision(geom,0.0000001));

   -- Kontrola
   SELECT st_astext(geom),id FROM public.dokument_extra_data
   WHERE ST_IsValid(geom)='false';

Projekt
^^^^^^^

WGS-84:

.. code-block:: sql

   -- Vyhledat
   SELECT count(*) FROM public.projekt
   WHERE geom IS NOT NULL and st_astext(geom)<>st_astext(ST_ReducePrecision(geom,0.0000001));

   -- Nahradit
   UPDATE public.projekt SET geom=ST_ReducePrecision(geom,0.0000001)
   WHERE geom IS NOT NULL and st_astext(geom)<>st_astext(ST_ReducePrecision(geom,0.0000001));

   -- Kontrola
   SELECT st_astext(geom),id FROM public.projekt
   WHERE ST_IsValid(geom)='false';

Pian
^^^^

WGS-84:

.. code-block:: sql

   -- Vyhledat současné chyby geometrie
   SELECT count(*) FROM public.pian
   WHERE geom IS NOT NULL and ST_IsValid(geom)<>'true';

   -- Upravit současné chyby geometrie
   UPDATE public.pian SET geom=st_makeValid(geom)
   WHERE geom IS NOT NULL and ST_IsValid(geom)<>'true';

   -- Vyhledat
   SELECT count(*) FROM public.pian
   WHERE geom IS NOT NULL and st_astext(geom)<>st_astext(ST_ReducePrecision(geom,0.0000001));

   -- Nahradit
   UPDATE public.pian SET geom=ST_ReducePrecision(geom,0.0000001)
   WHERE geom IS NOT NULL and st_astext(geom)<>st_astext(ST_ReducePrecision(geom,0.0000001));

   -- Kontrola
   SELECT st_astext(geom),id FROM public.pian
   WHERE ST_IsValid(geom)<>'true';

S-JTSK:

.. code-block:: sql

   -- Vyhledat současné chyby geometrie
   SELECT count(*) FROM public.pian
   WHERE geom_sjtsk IS NOT NULL and ST_IsValid(geom_sjtsk)<>'true';

   -- Upravit současné chyby geometrie
   UPDATE public.pian SET geom=st_makeValid(geom_sjtsk)
   WHERE geom_sjtsk IS NOT NULL and ST_IsValid(geom_sjtsk)<>'true';

   -- Vyhledat
   SELECT st_astext(geom_sjtsk) FROM public.pian
   WHERE geom_sjtsk IS NOT NULL and st_astext(geom_sjtsk)<>st_astext(ST_ReducePrecision(geom_sjtsk,0.01));

   -- Nahradit
   UPDATE public.pian SET geom_sjtsk=ST_ReducePrecision(geom_sjtsk,0.01)
   WHERE geom_sjtsk IS NOT NULL and st_astext(geom_sjtsk)<>st_astext(ST_ReducePrecision(geom_sjtsk,0.01));

   -- Kontrola
   SELECT st_astext(geom_sjtsk),ident_cely FROM public.pian
   WHERE ST_IsValid(geom_sjtsk)<>'true';

