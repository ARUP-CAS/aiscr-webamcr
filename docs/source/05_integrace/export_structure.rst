Struktura XML exportu
=====================

Tento dokument popisuje strukturu XML exportu z databáze AMCR podle XML schématu verze 2.2.

Mapování modelů na komplexní typy
---------------------------------

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Model
     - Komplexní typ
   * - ``Projekt``
     - ``amcr:projektType``
   * - ``ArcheologickyZaznam``
     - ``amcr:archeologicky_zaznamType``
   * - ``Let``
     - ``amcr:letType``
   * - ``Adb``
     - ``amcr:adbType``
   * - ``Dokument``
     - ``amcr:dokumentType``
   * - ``ExterniZdroj``
     - ``amcr:ext_zdrojType``
   * - ``Pian``
     - ``amcr:pianType``
   * - ``SamostatnyNalez``
     - ``amcr:samostatny_nalezType``
   * - ``User``
     - ``amcr:uzivatelType``
   * - ``Heslar``
     - ``amcr:hesloType``
   * - ``RuianKraj``
     - ``amcr:ruian_krajType``
   * - ``RuianOkres``
     - ``amcr:ruian_okresType``
   * - ``RuianKatastr``
     - ``amcr:ruian_katastrType``
   * - ``Organizace``
     - ``amcr:organizaceType``
   * - ``Osoba``
     - ``amcr:osobaType``

projektType
-----------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``stav``
     - ``1``
     - ``1``
     - ``xs:integer``
     - ``stav``
     - 
     - 
   * - ``typ_projektu``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``typ_projektu.ident_cely``
     - ``typ_projektu.heslo``
     - 
   * - ``okres``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``ruian-{hlavni_katastr.okres.kod}``
     - ``hlavni_katastr.okres.nazev``
     - 
   * - ``podnet``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``podnet``
     - 
     - 
   * - ``planovane_zahajeni``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``planovane_zahajeni_str``
     - 
     - 
   * - ``vedouci_projektu``
     - ``0``
     - ``1``
     - ``amcr:refType``
     - ``vedouci_projektu.ident_cely``
     - ``vedouci_projektu.vypis_cely``
     - 
   * - ``organizace``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``organizace.ident_cely``
     - ``organizace.nazev``
     - 
   * - ``uzivatelske_oznaceni``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``uzivatelske_oznaceni``
     - 
     - 
   * - ``oznaceni_stavby``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``oznaceni_stavby``
     - 
     - 
   * - ``kulturni_pamatka``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``kulturni_pamatka.ident_cely``
     - ``kulturni_pamatka.heslo``
     - 
   * - ``datum_zahajeni``
     - ``0``
     - ``1``
     - ``xs:date``
     - ``datum_zahajeni``
     - 
     - 
   * - ``datum_ukonceni``
     - ``0``
     - ``1``
     - ``xs:date``
     - ``datum_ukonceni``
     - 
     - 
   * - ``termin_odevzdani_nz``
     - ``0``
     - ``1``
     - ``xs:date``
     - ``termin_odevzdani_nz``
     - 
     - 
   * - ``pristupnost_pom``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``pristupnost_snapshot.ident_cely``
     - ``pristupnost_snapshot.heslo``
     - 
   * - ``geom_system``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``geom_system``
     - 
     - 
   * - ``chranene_udaje``
     - ``0``
     - ``1``
     - ``amcr:projekt-chranene_udajeType``
     - 
     - 
     - 
   * - ``historie``
     - ``0``
     - ``unbounded``
     - ``amcr:historieType``
     - ``historie.historie_set``
     - 
     - 
   * - ``oznamovatel``
     - ``0``
     - ``1``
     - ``amcr:oznamovatelType``
     - ``oznamovatel``
     - 
     - 
   * - ``soubor``
     - ``0``
     - ``unbounded``
     - ``amcr:souborType``
     - ``soubory.soubory``
     - 
     - 
   * - ``archeologicky_zaznam``
     - ``0``
     - ``unbounded``
     - ``amcr:refType``
     - ``akce_set.archeologicky_zaznam.ident_cely``
     - ``akce_set.archeologicky_zaznam.ident_cely``
     - 
   * - ``samostatny_nalez``
     - ``0``
     - ``unbounded``
     - ``amcr:refType``
     - ``samostatne_nalezy.ident_cely``
     - ``samostatne_nalezy.ident_cely``
     - 
   * - ``dokument``
     - ``0``
     - ``unbounded``
     - ``amcr:refType``
     - ``casti_dokumentu.dokument.ident_cely``
     - ``casti_dokumentu.dokument.ident_cely``
     - 

archeologicky_zaznamType
------------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``stav``
     - ``1``
     - ``1``
     - ``xs:integer``
     - ``stav``
     - 
     - 
   * - ``okres``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``ruian-{hlavni_katastr.okres.kod}``
     - ``hlavni_katastr.okres.nazev``
     - 
   * - ``pristupnost``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``pristupnost.ident_cely``
     - ``pristupnost.heslo``
     - 
   * - ``chranene_udaje``
     - ``0``
     - ``1``
     - ``amcr:az-chranene_udajeType``
     - 
     - 
     - 
   * - ``akce``
     - ``1``
     - ``1``
     - ``amcr:akceType``
     - ``akce``
     - 
     - Volba mezi akce a lokalita
   * - ``lokalita``
     - ``1``
     - ``1``
     - ``amcr:lokalitaType``
     - ``lokalita``
     - 
     - Volba mezi akce a lokalita
   * - ``historie``
     - ``0``
     - ``unbounded``
     - ``amcr:historieType``
     - ``historie.historie_set``
     - 
     - 
   * - ``dokumentacni_jednotka``
     - ``0``
     - ``unbounded``
     - ``amcr:dokumentacni_jednotkaType``
     - ``dokumentacni_jednotky_akce``
     - 
     - 
   * - ``ext_odkaz``
     - ``0``
     - ``unbounded``
     - ``amcr:az-ext_odkazType``
     - ``externi_odkazy``
     - 
     - 
   * - ``dokument``
     - ``0``
     - ``unbounded``
     - ``amcr:refType``
     - ``casti_dokumentu.dokument.ident_cely``
     - ``casti_dokumentu.dokument.ident_cely``
     - 

letType
-------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``datum``
     - ``0``
     - ``1``
     - ``xs:date``
     - ``datum``
     - 
     - 
   * - ``hodina_zacatek``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``hodina_zacatek``
     - 
     - 
   * - ``hodina_konec``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``hodina_konec``
     - 
     - 
   * - ``pozorovatel``
     - ``0``
     - ``1``
     - ``amcr:refType``
     - ``pozorovatel.ident_cely``
     - ``pozorovatel.vypis_cely``
     - 
   * - ``organizace``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``organizace.ident_cely``
     - ``organizace.nazev``
     - 
   * - ``fotoaparat``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``fotoaparat``
     - 
     - 
   * - ``pilot``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``pilot``
     - 
     - 
   * - ``typ_letounu``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``typ_letounu``
     - 
     - 
   * - ``ucel_letu``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``ucel_letu``
     - 
     - 
   * - ``letiste_start``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``letiste_start.ident_cely``
     - ``letiste_start.heslo``
     - 
   * - ``letiste_cil``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``letiste_cil.ident_cely``
     - ``letiste_cil.heslo``
     - 
   * - ``pocasi``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``pocasi.ident_cely``
     - ``pocasi.heslo``
     - 
   * - ``dohlednost``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``dohlednost.ident_cely``
     - ``dohlednost.heslo``
     - 
   * - ``uzivatelske_oznaceni``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``uzivatelske_oznaceni``
     - 
     - 
   * - ``dokument``
     - ``0``
     - ``unbounded``
     - ``amcr:refType``
     - ``dokument_set.ident_cely``
     - ``dokument_set.ident_cely``
     - 

adbType
-------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``dokumentacni_jednotka``
     - ``1``
     - ``1``
     - ``amcr:refType``
     - ``dokumentacni_jednotka.archeologicky_zaznam.ident_cely``
     - ``dokumentacni_jednotka.ident_cely``
     - 
   * - ``stav_pom``
     - ``1``
     - ``1``
     - ``xs:integer``
     - ``dokumentacni_jednotka.archeologicky_zaznam.stav``
     - 
     - 
   * - ``typ_sondy``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``typ_sondy.ident_cely``
     - ``typ_sondy.heslo``
     - 
   * - ``podnet``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``podnet.ident_cely``
     - ``podnet.heslo``
     - 
   * - ``stratigraficke_jednotky``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``stratigraficke_jednotky``
     - 
     - 
   * - ``autor_popisu``
     - ``1``
     - ``1``
     - ``amcr:refType``
     - ``autor_popisu.ident_cely``
     - ``autor_popisu.vypis_cely``
     - 
   * - ``rok_popisu``
     - ``1``
     - ``1``
     - ``xs:integer``
     - ``rok_popisu``
     - 
     - 
   * - ``autor_revize``
     - ``0``
     - ``1``
     - ``amcr:refType``
     - ``autor_revize.ident_cely``
     - ``autor_revize.vypis_cely``
     - 
   * - ``rok_revize``
     - ``0``
     - ``1``
     - ``xs:integer``
     - ``rok_revize``
     - 
     - 
   * - ``sm5``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``sm5.mapno``
     - 
     - 
   * - ``pristupnost_pom``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``dokumentacni_jednotka.archeologicky_zaznam.pristupnost.ident_cely``
     - ``dokumentacni_jednotka.archeologicky_zaznam.pristupnost.heslo``
     - 
   * - ``chranene_udaje``
     - ``0``
     - ``1``
     - ``amcr:adb-chranene_udajeType``
     - 
     - 
     - 

dokumentType
------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``doi``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``doi``
     - 
     - 
   * - ``let``
     - ``0``
     - ``1``
     - ``amcr:refType``
     - ``let.ident_cely``
     - ``let.ident_cely``
     - 
   * - ``stav``
     - ``1``
     - ``1``
     - ``xs:integer``
     - ``stav``
     - 
     - 
   * - ``typ_dokumentu``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``typ_dokumentu.ident_cely``
     - ``typ_dokumentu.heslo``
     - 
   * - ``material_originalu``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``material_originalu.ident_cely``
     - ``material_originalu.heslo``
     - 
   * - ``rada``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``rada.ident_cely``
     - ``rada.heslo``
     - 
   * - ``posudek``
     - ``0``
     - ``unbounded``
     - ``amcr:vocabType``
     - ``posudky.ident_cely``
     - ``posudky.heslo``
     - 
   * - ``autor``
     - ``0``
     - ``unbounded``
     - ``amcr:autorType``
     - ``dokumentautor_set.autor.ident_cely``
     - ``dokumentautor_set.poradi``
     - 
   * - ``rok_vzniku``
     - ``0``
     - ``1``
     - ``xs:integer``
     - ``rok_vzniku``
     - 
     - 
   * - ``organizace``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``organizace.ident_cely``
     - ``organizace.nazev``
     - 
   * - ``pristupnost``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``pristupnost.ident_cely``
     - ``pristupnost.heslo``
     - 
   * - ``datum_zverejneni``
     - ``0``
     - ``1``
     - ``xs:date``
     - ``datum_zverejneni``
     - 
     - 
   * - ``jazyk_dokumentu``
     - ``0``
     - ``unbounded``
     - ``amcr:vocabType``
     - ``jazyky.ident_cely``
     - ``jazyky.heslo``
     - 
   * - ``ulozeni_originalu``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``ulozeni_originalu.ident_cely``
     - ``ulozeni_originalu.heslo``
     - 
   * - ``oznaceni_originalu``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``oznaceni_originalu``
     - 
     - 
   * - ``popis``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``popis``
     - 
     - 
   * - ``poznamka``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``poznamka``
     - 
     - 
   * - ``licence``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``licence.ident_cely``
     - ``licence.heslo``
     - 
   * - ``osoba``
     - ``0``
     - ``unbounded``
     - ``amcr:refType``
     - ``osoby.ident_cely``
     - ``osoby.vypis_cely``
     - 
   * - ``historie``
     - ``0``
     - ``unbounded``
     - ``amcr:historieType``
     - ``historie.historie_set``
     - 
     - 
   * - ``soubor``
     - ``0``
     - ``unbounded``
     - ``amcr:souborType``
     - ``soubory.soubory``
     - 
     - 
   * - ``extra_data``
     - ``0``
     - ``1``
     - ``amcr:extra_dataType``
     - ``extra_data``
     - 
     - 
   * - ``tvar``
     - ``0``
     - ``unbounded``
     - ``amcr:tvarType``
     - ``tvar_set``
     - 
     - 
   * - ``dokument_cast``
     - ``0``
     - ``unbounded``
     - ``amcr:dokument_castType``
     - ``casti``
     - 
     - 

ext_zdrojType
-------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``doi``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``doi``
     - 
     - 
   * - ``stav``
     - ``1``
     - ``1``
     - ``xs:integer``
     - ``stav``
     - 
     - 
   * - ``typ``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``typ.ident_cely``
     - ``typ.heslo``
     - 
   * - ``autor``
     - ``0``
     - ``unbounded``
     - ``amcr:autorType``
     - ``externizdrojautor_set.autor.ident_cely``
     - ``externizdrojautor_set.poradi``
     - 
   * - ``nazev``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``nazev``
     - 
     - 
   * - ``edice_rada``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``edice_rada``
     - 
     - 
   * - ``rok_vydani_vzniku``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``rok_vydani_vzniku``
     - 
     - 
   * - ``isbn``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``isbn``
     - 
     - 
   * - ``issn``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``issn``
     - 
     - 
   * - ``vydavatel``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``vydavatel``
     - 
     - 
   * - ``editor``
     - ``0``
     - ``unbounded``
     - ``amcr:autorType``
     - ``externizdrojeditor_set.editor.ident_cely``
     - ``externizdrojeditor_set.poradi``
     - 
   * - ``sbornik_nazev``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``sbornik_nazev``
     - 
     - 
   * - ``misto``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``misto``
     - 
     - 
   * - ``casopis_denik_nazev``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``casopis_denik_nazev``
     - 
     - 
   * - ``casopis_rocnik``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``casopis_rocnik``
     - 
     - 
   * - ``datum_rd``
     - ``0``
     - ``1``
     - ``xs:date``
     - ``datum_rd``
     - 
     - 
   * - ``paginace_titulu``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``paginace_titulu``
     - 
     - 
   * - ``link``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``link``
     - 
     - 
   * - ``typ_dokumentu``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``typ_dokumentu.ident_cely``
     - ``typ_dokumentu.heslo``
     - 
   * - ``organizace``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``organizace``
     - 
     - 
   * - ``poznamka``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``poznamka``
     - 
     - 
   * - ``historie``
     - ``0``
     - ``unbounded``
     - ``amcr:historieType``
     - ``historie.historie_set``
     - 
     - 
   * - ``ext_odkaz``
     - ``0``
     - ``unbounded``
     - ``amcr:ez-ext_odkazType``
     - ``externi_odkazy_zdroje``
     - 
     - 

pianType
--------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``stav``
     - ``1``
     - ``1``
     - ``xs:integer``
     - ``stav``
     - 
     - 
   * - ``typ``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``typ.ident_cely``
     - ``typ.heslo``
     - 
   * - ``presnost``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``presnost.ident_cely``
     - ``presnost.heslo``
     - 
   * - ``geom_system``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``geom_system``
     - 
     - 
   * - ``pristupnost_pom``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``pristupnost_pom.ident_cely``
     - ``pristupnost_pom.heslo``
     - 
   * - ``chranene_udaje``
     - ``0``
     - ``1``
     - ``amcr:pian-chranene_udajeType``
     - 
     - 
     - 
   * - ``historie``
     - ``0``
     - ``unbounded``
     - ``amcr:historieType``
     - ``historie.historie_set``
     - 
     - 
   * - ``dokumentacni_jednotka``
     - ``0``
     - ``unbounded``
     - ``amcr:refType``
     - ``dokumentacni_jednotky_pianu.archeologicky_zaznam.ident_cely``
     - ``dokumentacni_jednotky_pianu.ident_cely``
     - 

samostatny_nalezType
--------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``evidencni_cislo``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``evidencni_cislo``
     - 
     - 
   * - ``igsn``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``igsn``
     - 
     - 
   * - ``projekt``
     - ``1``
     - ``1``
     - ``amcr:refType``
     - ``projekt.ident_cely``
     - ``projekt.ident_cely``
     - 
   * - ``okres``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``ruian-{katastr.okres.kod}``
     - ``katastr.okres.nazev``
     - 
   * - ``hloubka``
     - ``0``
     - ``1``
     - ``xs:integer``
     - ``hloubka``
     - 
     - 
   * - ``okolnosti``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``okolnosti.ident_cely``
     - ``okolnosti.heslo``
     - 
   * - ``obdobi``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``obdobi.ident_cely``
     - ``obdobi.heslo``
     - 
   * - ``presna_datace``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``presna_datace``
     - 
     - 
   * - ``druh_nalezu``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``druh_nalezu.ident_cely``
     - ``druh_nalezu.heslo``
     - 
   * - ``specifikace``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``specifikace.ident_cely``
     - ``specifikace.heslo``
     - 
   * - ``pocet``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``pocet``
     - 
     - 
   * - ``poznamka``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``poznamka``
     - 
     - 
   * - ``nalezce``
     - ``0``
     - ``1``
     - ``amcr:refType``
     - ``nalezce.ident_cely``
     - ``nalezce.vypis_cely``
     - 
   * - ``datum_nalezu``
     - ``0``
     - ``1``
     - ``xs:date``
     - ``datum_nalezu``
     - 
     - 
   * - ``stav``
     - ``1``
     - ``1``
     - ``xs:integer``
     - ``stav``
     - 
     - 
   * - ``predano``
     - ``0``
     - ``1``
     - ``xs:boolean``
     - ``predano``
     - 
     - 
   * - ``predano_organizace``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``predano_organizace.ident_cely``
     - ``predano_organizace.nazev``
     - 
   * - ``geom_system``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``geom_system``
     - 
     - 
   * - ``pristupnost``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``pristupnost.ident_cely``
     - ``pristupnost.heslo``
     - 
   * - ``chranene_udaje``
     - ``0``
     - ``1``
     - ``amcr:sn-chranene_udajeType``
     - 
     - 
     - 
   * - ``historie``
     - ``0``
     - ``unbounded``
     - ``amcr:historieType``
     - ``historie.historie_set``
     - 
     - 
   * - ``soubor``
     - ``0``
     - ``unbounded``
     - ``amcr:souborType``
     - ``soubory.soubory``
     - 
     - 

uzivatelType
------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``jmeno``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``first_name``
     - 
     - 
   * - ``prijmeni``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``last_name``
     - 
     - 
   * - ``email``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``email``
     - 
     - 
   * - ``osoba``
     - ``0``
     - ``1``
     - ``amcr:refType``
     - ``osoba.ident_cely``
     - ``osoba.vypis_cely``
     - 
   * - ``orcid``
     - ``0``
     - ``1``
     - ``xs:anyURI``
     - ``orcid``
     - 
     - 
   * - ``organizace``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``organizace.ident_cely``
     - ``organizace.nazev``
     - 
   * - ``jazyk``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``jazyk``
     - 
     - 
   * - ``telefon``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``telefon``
     - 
     - 
   * - ``aktivni``
     - ``1``
     - ``1``
     - ``xs:boolean``
     - ``is_active``
     - 
     - 
   * - ``admin``
     - ``1``
     - ``1``
     - ``xs:boolean``
     - ``is_staff``
     - 
     - 
   * - ``superadmin``
     - ``1``
     - ``1``
     - ``xs:boolean``
     - ``is_superuser``
     - 
     - 
   * - ``skupina``
     - ``1``
     - ``unbounded``
     - ``amcr:langstringType``
     - ``groups.name``
     - 
     - 
   * - ``notifikace``
     - ``0``
     - ``unbounded``
     - ``xs:string``
     - ``notification_types.ident_cely``
     - 
     - 
   * - ``hlidaci_pes``
     - ``0``
     - ``unbounded``
     - ``amcr:vocabType``
     - ``pes_set``
     - 
     - 
   * - ``datum_registrace``
     - ``1``
     - ``1``
     - ``xs:dateTime``
     - ``date_joined``
     - 
     - 
   * - ``historie``
     - ``0``
     - ``unbounded``
     - ``amcr:historieType``
     - ``history_vazba.historie_set``
     - 
     - 
   * - ``spoluprace_nadrizeni``
     - ``0``
     - ``unbounded``
     - ``amcr:spoluprace_nadrizeniType``
     - ``spoluprace_badatelu``
     - 
     - 
   * - ``spoluprace_podrizeni``
     - ``0``
     - ``unbounded``
     - ``amcr:spoluprace_podrizeniType``
     - ``spoluprace_archeologu``
     - 
     - 

hesloType
---------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``nazev_heslare``
     - ``1``
     - ``1``
     - ``amcr:langstringType``
     - ``nazev_heslare.nazev``
     - 
     - 
   * - ``heslo``
     - ``1``
     - ``1``
     - ``amcr:langstringType``
     - ``heslo``
     - 
     - 
   * - ``heslo_en``
     - ``1``
     - ``1``
     - ``amcr:langstringType``
     - ``heslo_en``
     - 
     - 
   * - ``popis``
     - ``0``
     - ``1``
     - ``amcr:langstringType``
     - ``popis``
     - 
     - 
   * - ``popis_en``
     - ``0``
     - ``1``
     - ``amcr:langstringType``
     - ``popis_en``
     - 
     - 
   * - ``zkratka``
     - ``0``
     - ``1``
     - ``amcr:langstringType``
     - ``zkratka``
     - 
     - 
   * - ``razeni``
     - ``0``
     - ``1``
     - ``xs:integer``
     - ``razeni``
     - 
     - 
   * - ``hierarchie_vyse``
     - ``0``
     - ``unbounded``
     - ``amcr:hierarchie_vyseType``
     - ``nadrazena_hesla``
     - 
     - 
   * - ``hierarchie_nize``
     - ``0``
     - ``unbounded``
     - ``amcr:hierarchie_nizeType``
     - ``podrazena_hesla``
     - 
     - 
   * - ``dokument_typ_material_rada``
     - ``0``
     - ``unbounded``
     - ``amcr:dokument_typ_material_radaType``
     - ``dokument_typ_material_rada``
     - 
     - 
   * - ``datace``
     - ``0``
     - ``1``
     - ``amcr:dataceType``
     - ``datace_obdobi``
     - 
     - 
   * - ``odkaz``
     - ``0``
     - ``unbounded``
     - ``amcr:odkazType``
     - ``heslar_odkaz``
     - 
     - 

ruian_krajType
--------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``kod``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ruian-{kod}``
     - 
     - 
   * - ``nazev``
     - ``1``
     - ``1``
     - ``amcr:langstringType``
     - ``nazev``
     - 
     - 
   * - ``nazev_en``
     - ``1``
     - ``1``
     - ``amcr:langstringType``
     - ``nazev_en``
     - 
     - 
   * - ``rada_id``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``rada_id``
     - 
     - 
   * - ``definicni_bod_gml``
     - ``0``
     - ``1``
     - ``amcr:gmlType``
     - ``ST_AsGML("{definicni_bod}")``
     - 
     - 
   * - ``definicni_bod_wkt``
     - ``0``
     - ``1``
     - ``amcr:wktType``
     - ``ST_SRID("{definicni_bod}")``
     - ``ST_AsText("{definicni_bod}")``
     - 
   * - ``hranice_gml``
     - ``0``
     - ``1``
     - ``amcr:gmlType``
     - ``ST_AsGML("{hranice}")``
     - 
     - 
   * - ``hranice_wkt``
     - ``0``
     - ``1``
     - ``amcr:wktType``
     - ``ST_SRID("{hranice}")``
     - ``ST_AsText("{hranice}")``
     - 
   * - ``email``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``email``
     - 
     - 

ruian_okresType
---------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``kod``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ruian-{kod}``
     - 
     - 
   * - ``nazev``
     - ``1``
     - ``1``
     - ``amcr:langstringType``
     - ``nazev``
     - 
     - 
   * - ``nazev_en``
     - ``1``
     - ``1``
     - ``amcr:langstringType``
     - ``nazev_en``
     - 
     - 
   * - ``spz``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``spz``
     - 
     - 
   * - ``kraj``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``ruian-{kraj.kod}``
     - ``kraj.nazev``
     - 
   * - ``definicni_bod_gml``
     - ``0``
     - ``1``
     - ``amcr:gmlType``
     - ``ST_AsGML("{definicni_bod}")``
     - 
     - 
   * - ``definicni_bod_wkt``
     - ``0``
     - ``1``
     - ``amcr:wktType``
     - ``ST_SRID("{definicni_bod}")``
     - ``ST_AsText("{definicni_bod}")``
     - 
   * - ``hranice_gml``
     - ``0``
     - ``1``
     - ``amcr:gmlType``
     - ``ST_AsGML("{hranice}")``
     - 
     - 
   * - ``hranice_wkt``
     - ``0``
     - ``1``
     - ``amcr:wktType``
     - ``ST_SRID("{hranice}")``
     - ``ST_AsText("{hranice}")``
     - 

ruian_katastrType
-----------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``kod``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ruian-{kod}``
     - 
     - 
   * - ``nazev``
     - ``1``
     - ``1``
     - ``amcr:langstringType``
     - ``nazev``
     - 
     - 
   * - ``okres``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``ruian-{okres.kod}``
     - ``okres.nazev``
     - 
   * - ``pian``
     - ``0``
     - ``1``
     - ``amcr:refType``
     - ``pian.ident_cely``
     - ``pian.ident_cely``
     - 
   * - ``definicni_bod_gml``
     - ``1``
     - ``1``
     - ``amcr:gmlType``
     - ``ST_AsGML("{definicni_bod}")``
     - 
     - 
   * - ``definicni_bod_wkt``
     - ``1``
     - ``1``
     - ``amcr:wktType``
     - ``ST_SRID("{definicni_bod}")``
     - ``ST_AsText("{definicni_bod}")``
     - 
   * - ``hranice_gml``
     - ``1``
     - ``1``
     - ``amcr:gmlType``
     - ``ST_AsGML("{hranice}")``
     - 
     - 
   * - ``hranice_wkt``
     - ``1``
     - ``1``
     - ``amcr:wktType``
     - ``ST_SRID("{hranice}")``
     - ``ST_AsText("{hranice}")``
     - 

organizaceType
--------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``nazev``
     - ``1``
     - ``1``
     - ``amcr:langstringType``
     - ``nazev``
     - 
     - 
   * - ``nazev_en``
     - ``0``
     - ``1``
     - ``amcr:langstringType``
     - ``nazev_en``
     - 
     - 
   * - ``nazev_zkraceny``
     - ``1``
     - ``1``
     - ``amcr:langstringType``
     - ``nazev_zkraceny``
     - 
     - 
   * - ``nazev_zkraceny_en``
     - ``1``
     - ``1``
     - ``amcr:langstringType``
     - ``nazev_zkraceny_en``
     - 
     - 
   * - ``typ_organizace``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``typ_organizace.ident_cely``
     - ``typ_organizace.heslo``
     - 
   * - ``oao``
     - ``1``
     - ``1``
     - ``xs:boolean``
     - ``oao``
     - 
     - 
   * - ``mesicu_do_zverejneni``
     - ``1``
     - ``1``
     - ``xs:integer``
     - ``mesicu_do_zverejneni``
     - 
     - 
   * - ``zverejneni_pristupnost``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``zverejneni_pristupnost.ident_cely``
     - ``zverejneni_pristupnost.heslo``
     - 
   * - ``email``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``email``
     - 
     - 
   * - ``telefon``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``telefon``
     - 
     - 
   * - ``adresa``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``adresa``
     - 
     - 
   * - ``ico``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``ico``
     - 
     - 
   * - ``soucast``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``soucast.ident_cely``
     - ``soucast.nazev``
     - 
   * - ``zanikla``
     - ``1``
     - ``1``
     - ``xs:boolean``
     - ``zanikla``
     - 
     - 
   * - ``cteni_dokumentu``
     - ``1``
     - ``1``
     - ``xs:boolean``
     - ``cteni_dokumentu``
     - 
     - 
   * - ``ror``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``ror``
     - 
     - 

osobaType
---------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``jmeno``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``jmeno``
     - 
     - 
   * - ``prijmeni``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``prijmeni``
     - 
     - 
   * - ``vypis``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``vypis``
     - 
     - 
   * - ``vypis_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``vypis_cely``
     - 
     - 
   * - ``rok_narozeni``
     - ``0``
     - ``1``
     - ``xs:integer``
     - ``rok_narozeni``
     - 
     - 
   * - ``rok_umrti``
     - ``0``
     - ``1``
     - ``xs:integer``
     - ``rok_umrti``
     - 
     - 
   * - ``rodne_prijmeni``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``rodne_prijmeni``
     - 
     - 
   * - ``orcid``
     - ``0``
     - ``1``
     - ``xs:anyURI``
     - ``orcid``
     - 
     - 
   * - ``wikidata``
     - ``0``
     - ``1``
     - ``xs:anyURI``
     - ``wikidata``
     - 
     - 

projekt-chranene_udajeType
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``hlavni_katastr``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``ruian-{hlavni_katastr.kod}``
     - ``hlavni_katastr.nazev``
     - 
   * - ``dalsi_katastr``
     - ``0``
     - ``unbounded``
     - ``amcr:vocabType``
     - ``ruian-{katastry.kod}``
     - ``katastry.nazev``
     - 
   * - ``lokalizace``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``lokalizace``
     - 
     - 
   * - ``parcelni_cislo``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``parcelni_cislo``
     - 
     - 
   * - ``geom_gml``
     - ``0``
     - ``1``
     - ``amcr:gmlType``
     - ``ST_AsGML("{geom}")``
     - 
     - 
   * - ``geom_wkt``
     - ``0``
     - ``1``
     - ``amcr:wktType``
     - ``ST_SRID("{geom}")``
     - ``ST_AsText("{geom}")``
     - 
   * - ``geom_sjtsk_gml``
     - ``0``
     - ``1``
     - ``amcr:gmlType``
     - ``ST_AsGML("{geom_sjtsk}")``
     - 
     - 
   * - ``geom_sjtsk_wkt``
     - ``0``
     - ``1``
     - ``amcr:wktType``
     - ``ST_SRID("{geom_sjtsk}")``
     - ``ST_AsText("{geom_sjtsk}")``
     - 
   * - ``kulturni_pamatka_cislo``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``kulturni_pamatka_cislo``
     - 
     - 
   * - ``kulturni_pamatka_popis``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``kulturni_pamatka_popis``
     - 
     - 

oznamovatelType
---------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``oznamovatel``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``oznamovatel``
     - 
     - 
   * - ``odpovedna_osoba``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``odpovedna_osoba``
     - 
     - 
   * - ``adresa``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``adresa``
     - 
     - 
   * - ``telefon``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``telefon``
     - 
     - 
   * - ``email``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``email``
     - 
     - 
   * - ``poznamka``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``poznamka``
     - 
     - 

historieType
------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``id``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``hist-{id}``
     - 
     - 
   * - ``datum_zmeny``
     - ``1``
     - ``1``
     - ``xs:dateTime``
     - ``datum_zmeny``
     - 
     - 
   * - ``uzivatel``
     - ``1``
     - ``1``
     - ``amcr:refType``
     - ``uzivatel.ident_cely``
     - ``uzivatel.ident_cely``
     - 
   * - ``poznamka``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``poznamka``
     - 
     - 
   * - ``typ_zmeny``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``typ_zmeny``
     - 
     - 

souborType
----------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``id``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``soub-{id}``
     - 
     - 
   * - ``path``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``path``
     - 
     - 
   * - ``nazev``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``nazev``
     - 
     - 
   * - ``mimetype``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``mimetype``
     - 
     - 
   * - ``rozsah``
     - ``0``
     - ``1``
     - ``xs:integer``
     - ``rozsah``
     - 
     - 
   * - ``size_mb``
     - ``1``
     - ``1``
     - ``xs:decimal``
     - ``size_mb``
     - 
     - 
   * - ``sha_512``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``sha_512``
     - 
     - 
   * - ``url``
     - ``1``
     - ``1``
     - ``xs:anyURI``
     - ``url``
     - 
     - 
   * - ``historie``
     - ``0``
     - ``unbounded``
     - ``amcr:historieType``
     - ``historie.historie_set``
     - 
     - 

az-chranene_udajeType
---------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``hlavni_katastr``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``ruian-{hlavni_katastr.kod}``
     - ``hlavni_katastr.nazev``
     - 
   * - ``dalsi_katastr``
     - ``0``
     - ``unbounded``
     - ``amcr:vocabType``
     - ``ruian-{katastry.kod}``
     - ``katastry.nazev``
     - 
   * - ``uzivatelske_oznaceni``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``uzivatelske_oznaceni``
     - 
     - 

akceType
--------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``projekt``
     - ``0``
     - ``1``
     - ``amcr:refType``
     - ``projekt.ident_cely``
     - ``projekt.ident_cely``
     - 
   * - ``typ``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``typ``
     - 
     - 
   * - ``je_nz``
     - ``1``
     - ``1``
     - ``xs:boolean``
     - ``je_nz``
     - 
     - 
   * - ``odlozena_nz``
     - ``1``
     - ``1``
     - ``xs:boolean``
     - ``odlozena_nz``
     - 
     - 
   * - ``hlavni_vedouci``
     - ``0``
     - ``1``
     - ``amcr:refType``
     - ``hlavni_vedouci.ident_cely``
     - ``hlavni_vedouci.vypis_cely``
     - 
   * - ``organizace``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``organizace.ident_cely``
     - ``organizace.nazev``
     - 
   * - ``vedouci_akce_ostatni``
     - ``0``
     - ``unbounded``
     - ``amcr:vedouci_akce_ostatniType``
     - ``akcevedouci_set``
     - 
     - 
   * - ``specifikace_data``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``specifikace_data.ident_cely``
     - ``specifikace_data.heslo``
     - 
   * - ``datum_zahajeni``
     - ``0``
     - ``1``
     - ``xs:date``
     - ``datum_zahajeni``
     - 
     - 
   * - ``datum_ukonceni``
     - ``0``
     - ``1``
     - ``xs:date``
     - ``datum_ukonceni``
     - 
     - 
   * - ``hlavni_typ``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``hlavni_typ.ident_cely``
     - ``hlavni_typ.heslo``
     - 
   * - ``vedlejsi_typ``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``vedlejsi_typ.ident_cely``
     - ``vedlejsi_typ.heslo``
     - 
   * - ``ulozeni_nalezu``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``ulozeni_nalezu``
     - 
     - 
   * - ``ulozeni_dokumentace``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``ulozeni_dokumentace``
     - 
     - 
   * - ``chranene_udaje``
     - ``0``
     - ``1``
     - ``amcr:akce-chranene_udajeType``
     - 
     - 
     - 

vedouci_akce_ostatniType
------------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``id``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``vedo-{id}``
     - 
     - 
   * - ``vedouci``
     - ``1``
     - ``1``
     - ``amcr:refType``
     - ``vedouci.ident_cely``
     - ``vedouci.vypis_cely``
     - 
   * - ``organizace``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``organizace.ident_cely``
     - ``organizace.nazev``
     - 

akce-chranene_udajeType
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``lokalizace_okolnosti``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``lokalizace_okolnosti``
     - 
     - 
   * - ``souhrn_upresneni``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``souhrn_upresneni``
     - 
     - 

lokalitaType
------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``igsn``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``igsn``
     - 
     - 
   * - ``typ_lokality``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``typ_lokality.ident_cely``
     - ``typ_lokality.heslo``
     - 
   * - ``druh``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``druh.ident_cely``
     - ``druh.heslo``
     - 
   * - ``zachovalost``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``zachovalost.ident_cely``
     - ``zachovalost.heslo``
     - 
   * - ``jistota``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``jistota.ident_cely``
     - ``jistota.heslo``
     - 
   * - ``chranene_udaje``
     - ``0``
     - ``1``
     - ``amcr:lok-chranene_udajeType``
     - 
     - 
     - 

lok-chranene_udajeType
----------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``nazev``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``nazev``
     - 
     - 
   * - ``popis``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``popis``
     - 
     - 
   * - ``poznamka``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``poznamka``
     - 
     - 

dokumentacni_jednotkaType
-------------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``pian``
     - ``0``
     - ``1``
     - ``amcr:refType``
     - ``pian.ident_cely``
     - ``pian.ident_cely``
     - 
   * - ``typ``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``typ.ident_cely``
     - ``typ.heslo``
     - 
   * - ``negativni_jednotka``
     - ``1``
     - ``1``
     - ``xs:boolean``
     - ``negativni_jednotka``
     - 
     - 
   * - ``nazev``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``nazev``
     - 
     - 
   * - ``adb``
     - ``0``
     - ``1``
     - ``amcr:refType``
     - ``Adb.ident_cely``
     - ``Adb.ident_cely``
     - 
   * - ``komponenta``
     - ``0``
     - ``unbounded``
     - ``amcr:komponentaType``
     - ``komponenty.komponenty``
     - 
     - 

az-ext_odkazType
----------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``id``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``exto-{id}``
     - 
     - 
   * - ``ext_zdroj``
     - ``1``
     - ``1``
     - ``amcr:refType``
     - ``externi_zdroj.ident_cely``
     - ``externi_zdroj.ident_cely``
     - 
   * - ``paginace``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``paginace``
     - 
     - 

ez-ext_odkazType
----------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``id``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``exto-{id}``
     - 
     - 
   * - ``archeologicky_zaznam``
     - ``1``
     - ``1``
     - ``amcr:refType``
     - ``archeologicky_zaznam.ident_cely``
     - ``archeologicky_zaznam.ident_cely``
     - 
   * - ``paginace``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``paginace``
     - 
     - 

adb-chranene_udajeType
----------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``uzivatelske_oznaceni_sondy``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``uzivatelske_oznaceni_sondy``
     - 
     - 
   * - ``trat``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``trat``
     - 
     - 
   * - ``cislo_popisne``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``cislo_popisne``
     - 
     - 
   * - ``parcelni_cislo``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``parcelni_cislo``
     - 
     - 
   * - ``poznamka``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``poznamka``
     - 
     - 
   * - ``vyskovy_bod``
     - ``0``
     - ``unbounded``
     - ``amcr:vyskovy_bodType``
     - ``vyskove_body``
     - 
     - 

vyskovy_bodType
---------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``typ``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``typ.ident_cely``
     - ``typ.heslo``
     - 
   * - ``geom_gml``
     - ``1``
     - ``1``
     - ``amcr:gmlType``
     - ``ST_AsGML("{geom}")``
     - 
     - 
   * - ``geom_wkt``
     - ``1``
     - ``1``
     - ``amcr:wktType``
     - ``ST_SRID("{geom}")``
     - ``ST_AsText("{geom}")``
     - 

extra_dataType
--------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``cislo_objektu``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``cislo_objektu``
     - 
     - 
   * - ``format``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``format.ident_cely``
     - ``format.heslo``
     - 
   * - ``meritko``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``meritko``
     - 
     - 
   * - ``vyska``
     - ``0``
     - ``1``
     - ``xs:integer``
     - ``vyska``
     - 
     - 
   * - ``sirka``
     - ``0``
     - ``1``
     - ``xs:integer``
     - ``sirka``
     - 
     - 
   * - ``zachovalost``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``zachovalost.ident_cely``
     - ``zachovalost.heslo``
     - 
   * - ``nahrada``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``nahrada.ident_cely``
     - ``nahrada.heslo``
     - 
   * - ``pocet_variant_originalu``
     - ``0``
     - ``1``
     - ``xs:integer``
     - ``pocet_variant_originalu``
     - 
     - 
   * - ``odkaz``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``odkaz``
     - 
     - 
   * - ``datum_vzniku``
     - ``0``
     - ``1``
     - ``xs:date``
     - ``datum_vzniku``
     - 
     - 
   * - ``udalost_typ``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``udalost_typ.ident_cely``
     - ``udalost_typ.heslo``
     - 
   * - ``udalost``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``udalost``
     - 
     - 
   * - ``zeme``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``zeme.ident_cely``
     - ``zeme.heslo``
     - 
   * - ``region``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``region_extra``
     - 
     - 
   * - ``rok_od``
     - ``0``
     - ``1``
     - ``xs:integer``
     - ``rok_od``
     - 
     - 
   * - ``rok_do``
     - ``0``
     - ``1``
     - ``xs:integer``
     - ``rok_do``
     - 
     - 
   * - ``duveryhodnost``
     - ``0``
     - ``1``
     - ``xs:integer``
     - ``duveryhodnost``
     - 
     - 
   * - ``geom_system``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``geom_system``
     - 
     - 
   * - ``geom_gml``
     - ``0``
     - ``1``
     - ``amcr:gmlType``
     - ``ST_AsGML("{geom}")``
     - 
     - 
   * - ``geom_wkt``
     - ``0``
     - ``1``
     - ``amcr:wktType``
     - ``ST_SRID("{geom}")``
     - ``ST_AsText("{geom}")``
     - 
   * - ``geom_sjtsk_gml``
     - ``0``
     - ``1``
     - ``amcr:gmlType``
     - ``ST_AsGML("{geom_sjtsk}")``
     - 
     - 
   * - ``geom_sjtsk_wkt``
     - ``0``
     - ``1``
     - ``amcr:wktType``
     - ``ST_SRID("{geom_sjtsk}")``
     - ``ST_AsText("{geom_sjtsk}")``
     - 

tvarType
--------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``id``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``tvar-{id}``
     - 
     - 
   * - ``tvar``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``tvar.ident_cely``
     - ``tvar.heslo``
     - 
   * - ``poznamka``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``poznamka``
     - 
     - 

dokument_castType
-----------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``archeologicky_zaznam``
     - ``0``
     - ``1``
     - ``amcr:refType``
     - ``archeologicky_zaznam.ident_cely``
     - ``archeologicky_zaznam.ident_cely``
     - 
   * - ``projekt``
     - ``0``
     - ``1``
     - ``amcr:refType``
     - ``projekt.ident_cely``
     - ``projekt.ident_cely``
     - 
   * - ``poznamka``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``poznamka``
     - 
     - 
   * - ``komponenta``
     - ``0``
     - ``unbounded``
     - ``amcr:komponentaType``
     - ``komponenty.komponenty``
     - 
     - 
   * - ``neident_akce``
     - ``0``
     - ``1``
     - ``amcr:neident_akceType``
     - ``neident_akce``
     - 
     - 

neident_akceType
----------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``okres``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``ruian-{katastr.okres.kod}``
     - ``katastr.okres.nazev``
     - 
   * - ``katastr``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``ruian-{katastr.kod}``
     - ``katastr.nazev``
     - 
   * - ``vedouci``
     - ``0``
     - ``unbounded``
     - ``amcr:refType``
     - ``vedouci.ident_cely``
     - ``vedouci.vypis_cely``
     - 
   * - ``rok_zahajeni``
     - ``0``
     - ``1``
     - ``xs:integer``
     - ``rok_zahajeni``
     - 
     - 
   * - ``rok_ukonceni``
     - ``0``
     - ``1``
     - ``xs:integer``
     - ``rok_ukonceni``
     - 
     - 
   * - ``lokalizace``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``lokalizace``
     - 
     - 
   * - ``popis``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``popis``
     - 
     - 
   * - ``poznamka``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``poznamka``
     - 
     - 
   * - ``pian``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``pian``
     - 
     - 

komponentaType
--------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``ident_cely``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``ident_cely``
     - 
     - 
   * - ``obdobi``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``obdobi.ident_cely``
     - ``obdobi.heslo``
     - 
   * - ``jistota``
     - ``0``
     - ``1``
     - ``xs:boolean``
     - ``jistota``
     - 
     - 
   * - ``presna_datace``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``presna_datace``
     - 
     - 
   * - ``areal``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``areal.ident_cely``
     - ``areal.heslo``
     - 
   * - ``aktivita``
     - ``0``
     - ``unbounded``
     - ``amcr:vocabType``
     - ``aktivity.ident_cely``
     - ``aktivity.heslo``
     - 
   * - ``poznamka``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``poznamka``
     - 
     - 
   * - ``nalez_objekt``
     - ``0``
     - ``unbounded``
     - ``amcr:nalez_objektType``
     - ``objekty``
     - 
     - 
   * - ``nalez_predmet``
     - ``0``
     - ``unbounded``
     - ``amcr:nalez_predmetType``
     - ``predmety``
     - 
     - 

nalez_objektType
----------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``id``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``nalo-{id}``
     - 
     - 
   * - ``druh``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``druh.ident_cely``
     - ``druh.heslo``
     - 
   * - ``specifikace``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``specifikace.ident_cely``
     - ``specifikace.heslo``
     - 
   * - ``pocet``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``pocet``
     - 
     - 
   * - ``poznamka``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``poznamka``
     - 
     - 

nalez_predmetType
-----------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``id``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``nalp-{id}``
     - 
     - 
   * - ``druh``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``druh.ident_cely``
     - ``druh.heslo``
     - 
   * - ``specifikace``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``specifikace.ident_cely``
     - ``specifikace.heslo``
     - 
   * - ``pocet``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``pocet``
     - 
     - 
   * - ``poznamka``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``poznamka``
     - 
     - 

pian-chranene_udajeType
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``zm10``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``zm10.cislo``
     - 
     - 
   * - ``geom_gml``
     - ``1``
     - ``1``
     - ``amcr:gmlType``
     - ``ST_AsGML("{geom}")``
     - 
     - 
   * - ``geom_wkt``
     - ``1``
     - ``1``
     - ``amcr:wktType``
     - ``ST_SRID("{geom}")``
     - ``ST_AsText("{geom}")``
     - 
   * - ``geom_sjtsk_gml``
     - ``0``
     - ``1``
     - ``amcr:gmlType``
     - ``ST_AsGML("{geom_sjtsk}")``
     - 
     - 
   * - ``geom_sjtsk_wkt``
     - ``0``
     - ``1``
     - ``amcr:wktType``
     - ``ST_SRID("{geom_sjtsk}")``
     - ``ST_AsText("{geom_sjtsk}")``
     - 

sn-chranene_udajeType
---------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``katastr``
     - ``0``
     - ``1``
     - ``amcr:vocabType``
     - ``ruian-{katastr.kod}``
     - ``katastr.nazev``
     - 
   * - ``lokalizace``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``lokalizace``
     - 
     - 
   * - ``geom_gml``
     - ``0``
     - ``1``
     - ``amcr:gmlType``
     - ``ST_AsGML("{geom}")``
     - 
     - 
   * - ``geom_wkt``
     - ``0``
     - ``1``
     - ``amcr:wktType``
     - ``ST_SRID("{geom}")``
     - ``ST_AsText("{geom}")``
     - 
   * - ``geom_sjtsk_gml``
     - ``0``
     - ``1``
     - ``amcr:gmlType``
     - ``ST_AsGML("{geom_sjtsk}")``
     - 
     - 
   * - ``geom_sjtsk_wkt``
     - ``0``
     - ``1``
     - ``amcr:wktType``
     - ``ST_SRID("{geom_sjtsk}")``
     - ``ST_AsText("{geom_sjtsk}")``
     - 

spoluprace_nadrizeniType
------------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``id``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``spol-{id}``
     - 
     - 
   * - ``vedouci``
     - ``1``
     - ``1``
     - ``amcr:refType``
     - ``vedouci.ident_cely``
     - ``vedouci.ident_cely``
     - 
   * - ``stav``
     - ``1``
     - ``1``
     - ``xs:integer``
     - ``stav``
     - 
     - 
   * - ``historie``
     - ``0``
     - ``unbounded``
     - ``amcr:historieType``
     - ``historie.historie_set``
     - 
     - 

spoluprace_podrizeniType
------------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``id``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``spol-{id}``
     - 
     - 
   * - ``spolupracovnik``
     - ``1``
     - ``1``
     - ``amcr:refType``
     - ``spolupracovnik.ident_cely``
     - ``spolupracovnik.ident_cely``
     - 
   * - ``stav``
     - ``1``
     - ``1``
     - ``xs:integer``
     - ``stav``
     - 
     - 
   * - ``historie``
     - ``0``
     - ``unbounded``
     - ``amcr:historieType``
     - ``historie.historie_set``
     - 
     - 

hierarchie_vyseType
-------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``id``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``hier-{id}``
     - 
     - 
   * - ``heslo_nadrazene``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``heslo_nadrazene.ident_cely``
     - ``heslo_nadrazene.heslo``
     - 
   * - ``typ``
     - ``1``
     - ``1``
     - ``amcr:langstringType``
     - ``typ``
     - 
     - 

hierarchie_nizeType
-------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``id``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``hier-{id}``
     - 
     - 
   * - ``heslo_podrazene``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``heslo_podrazene.ident_cely``
     - ``heslo_podrazene.heslo``
     - 
   * - ``typ``
     - ``1``
     - ``1``
     - ``amcr:langstringType``
     - ``typ``
     - 
     - 

dokument_typ_material_radaType
------------------------------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``id``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``hdtm-{id}``
     - 
     - 
   * - ``dokument_typ``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``dokument_typ.ident_cely``
     - ``dokument_typ.heslo``
     - 
   * - ``dokument_material``
     - ``1``
     - ``1``
     - ``amcr:vocabType``
     - ``dokument_material.ident_cely``
     - ``dokument_material.heslo``
     - 

dataceType
----------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``rok_od_min``
     - ``1``
     - ``1``
     - ``xs:integer``
     - ``rok_od_min``
     - 
     - 
   * - ``rok_od_max``
     - ``1``
     - ``1``
     - ``xs:integer``
     - ``rok_od_max``
     - 
     - 
   * - ``rok_do_min``
     - ``1``
     - ``1``
     - ``xs:integer``
     - ``rok_do_min``
     - 
     - 
   * - ``rok_do_max``
     - ``1``
     - ``1``
     - ``xs:integer``
     - ``rok_do_max``
     - 
     - 
   * - ``poznamka``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``poznamka``
     - 
     - 

odkazType
---------

.. list-table::
   :header-rows: 1
   :widths: 18 10 10 18 18 18 18

   * - Název elementu
     - Min. počet
     - Max. počet
     - Typ
     - Mapování hodnoty
     - Mapování popisu
     - Poznámka
   * - ``id``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``hodk-{id}``
     - 
     - 
   * - ``zdroj``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``zdroj``
     - 
     - 
   * - ``nazev_kodu``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``nazev_kodu``
     - 
     - 
   * - ``kod``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``kod``
     - 
     - 
   * - ``uri``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``uri``
     - 
     - 
   * - ``scheme_uri``
     - ``0``
     - ``1``
     - ``xs:string``
     - ``scheme_uri``
     - 
     - 
   * - ``skos_mapping_relation``
     - ``1``
     - ``1``
     - ``xs:string``
     - ``skos_mapping_relation``
     - 
     - 

Generické typy
---------------

- ``refType``
- ``autorType``
- ``wktType``
- ``gmlType``
- ``langstringType``
- ``vocabType``
