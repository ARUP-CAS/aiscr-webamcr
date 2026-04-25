Signály
=======

Dokumentace všech signálů v aplikaci.


ADB
---

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``Adb``
     - ``post_save``
     - ``adb_save_metadata``
   * - ``VyskovyBod``
     - ``post_save``
     - ``vyskovy_bod_save_metadata``
   * - ``Adb``
     - ``post_delete``
     - ``adb_delete_repository_container``
   * - ``VyskovyBod``
     - ``post_delete``
     - ``vyskovy_bod_delete_repository_container``

ARCH_Z
------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``ArcheologickyZaznam``
     - ``pre_save``
     - ``create_arch_z_vazby``
   * - ``ArcheologickyZaznam``
     - ``post_save``
     - ``create_arch_z_metadata``
   * - ``Akce``
     - ``post_save``
     - ``update_akce_snapshot``
   * - ``ExterniOdkaz``
     - ``post_save``
     - ``create_externi_odkaz_metadata``
   * - ``ArcheologickyZaznam``
     - ``pre_delete``
     - ``delete_arch_z_repository_container_and_connections``
   * - ``ArcheologickyZaznam``
     - ``post_delete``
     - ``delete_arch_z_repository_update_connected_records``
   * - ``ExterniOdkaz``
     - ``post_delete``
     - ``delete_externi_odkaz_repository_container``

CORE
----

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``Soubor``
     - ``pre_save``
     - ``soubor_get_rozsah``
   * - ``Soubor``
     - ``post_save``
     - ``soubor_save_update_record_metadata``
   * - ``Soubor``
     - ``pre_delete``
     - ``soubor_delete_connections``
   * - ``Soubor``
     - ``post_delete``
     - ``soubor_delete_update_metadata``

DJ
--

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``DokumentacniJednotka``
     - ``post_save``
     - ``save_dokumentacni_jednotka``
   * - ``DokumentacniJednotka``
     - ``pre_delete``
     - ``pre_delete_dokumentacni_jednotka``
   * - ``DokumentacniJednotka``
     - ``post_delete``
     - ``delete_dokumentacni_jednotka``

DOKUMENT
--------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``Dokument``
     - ``pre_save``
     - ``create_dokument_vazby``
   * - ``DokumentCast``
     - ``pre_save``
     - ``create_dokument_cast_vazby``
   * - ``Dokument``
     - ``post_save``
     - ``dokument_save_metadata``
   * - ``Let``
     - ``post_save``
     - ``let_save_metadata``
   * - ``Dokument``
     - ``post_delete``
     - ``dokument_delete_repository_container``
   * - ``Let``
     - ``post_delete``
     - ``let_delete_repository_container``
   * - ``DokumentCast``
     - ``post_save``
     - ``dokument_cast_save_metadata_save``
   * - ``DokumentCast``
     - ``post_delete``
     - ``dokument_cast_save_metadata_delete``
   * - ``Tvar``
     - ``post_save``
     - ``tvar_save``
   * - ``Tvar``
     - ``post_delete``
     - ``tvar_delete``

EZ
--

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``ExterniZdroj``
     - ``pre_save``
     - ``create_ez_vazby``
   * - ``ExterniZdroj``
     - ``post_save``
     - ``externi_zdroj_save_metadata``
   * - ``ExterniZdroj``
     - ``pre_delete``
     - ``delete_externi_zdroj_repository_container``

HESLAR
------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``Heslar``
     - ``pre_save``
     - ``save_ident_cely``
   * - ``Heslar``
     - ``post_save``
     - ``save_metadata_heslar``
   * - ``RuianKatastr``
     - ``post_save``
     - ``save_metadata_katastr``
   * - ``RuianKraj``
     - ``post_save``
     - ``save_metadata_kraj``
   * - ``RuianOkres``
     - ``post_save``
     - ``save_metadata_okres``
   * - ``HeslarHierarchie``
     - ``post_save``
     - ``save_metadata_heslar_hierarchie``
   * - ``HeslarDatace``
     - ``post_save``
     - ``save_metadata_heslar_datace``
   * - ``HeslarDokumentTypMaterialRada``
     - ``post_save``
     - ``save_metadata_heslar_dokument_typ_material_rada``
   * - ``HeslarOdkaz``
     - ``post_save``
     - ``save_metadata_heslar_odkaz``
   * - ``Heslar``
     - ``pre_delete``
     - ``heslar_delete_repository_container``
   * - ``RuianKatastr``
     - ``pre_delete``
     - ``ruian_katastr_delete_repository_container``
   * - ``RuianKraj``
     - ``pre_delete``
     - ``ruian_kraj_delete_repository_container``
   * - ``RuianOkres``
     - ``pre_delete``
     - ``ruian_okres_delete_repository_container``
   * - ``HeslarHierarchie``
     - ``post_delete``
     - ``delete_uppdate_related_heslar_hierarchie``
   * - ``HeslarDokumentTypMaterialRada``
     - ``post_delete``
     - ``delete_uppdate_related_heslar_dokument_typ_material_rada``
   * - ``HeslarOdkaz``
     - ``post_delete``
     - ``delete_uppdate_related_heslar_odkaz``
   * - ``HeslarDatace``
     - ``post_delete``
     - ``delete_uppdate_related_heslar_datace``

HISTORIE
--------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``Historie``
     - ``pre_save``
     - ``soubor_update_metadata``

KOMPONENTA
----------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``Komponenta``
     - ``post_save``
     - ``komponenta_save``
   * - ``Komponenta``
     - ``post_delete``
     - ``komponenta_delete``

LOKALITA
--------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``Lokalita``
     - ``pre_save``
     - ``save_lokalita_snapshot``
   * - ``Lokalita``
     - ``post_save``
     - ``save_lokalita_redis_snapshot``
   * - ``Lokalita``
     - ``pre_delete``
     - ``delete_lokalita``

NALEZ
-----

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``NalezObjekt``
     - ``post_delete``
     - ``delete_nalez_objekt``
   * - ``NalezPredmet``
     - ``post_delete``
     - ``delete_nalez_predmet``

NEIDENTAKCE
-----------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``NeidentAkce``
     - ``post_save``
     - ``neident_akce_post_save``
   * - ``NeidentAkce``
     - ``post_delete``
     - ``neident_akce_post_delete``

NOTIFIKACE_PROJEKTY
-------------------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``Pes``
     - ``post_save``
     - ``pes_save``
   * - ``Pes``
     - ``pre_delete``
     - ``pes_delete``

PAS
---

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``SamostatnyNalez``
     - ``pre_save``
     - ``create_dokument_vazby``
   * - ``SamostatnyNalez``
     - ``post_save``
     - ``save_metadata_samostatny_nalez``
   * - ``SamostatnyNalez``
     - ``pre_delete``
     - ``dokument_delete_container_soubor_vazby``
   * - ``UzivatelSpoluprace``
     - ``post_save``
     - ``save_uzivatel_spoluprce``
   * - ``UzivatelSpoluprace``
     - ``post_delete``
     - ``delete_uzivatel_spoluprce_connections``

PIAN
----

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``Pian``
     - ``pre_save``
     - ``create_pian_vazby``
   * - ``Pian``
     - ``post_save``
     - ``pian_save_metadata``
   * - ``Pian``
     - ``pre_delete``
     - ``samostatny_nalez_okres_delete_repository_container``

PROJEKT
-------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``Projekt``
     - ``pre_save``
     - ``projekt_pre_save``
   * - ``Projekt``
     - ``post_delete``
     - ``projekt_pre_delete``
   * - ``Projekt``
     - ``post_save``
     - ``projekt_post_save``

UZIVATEL
--------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Model
     - Typ signálu
     - Název funkce
   * - ``Organizace``
     - ``post_save``
     - ``orgnaizace_save_metadata``
   * - ``Osoba``
     - ``post_save``
     - ``osoba_save_metadata``
   * - ``User``
     - ``pre_save``
     - ``create_ident_cely``
   * - ``User``
     - ``post_save``
     - ``user_post_save_method``
   * - ``User``
     - ``pre_delete``
     - ``delete_user_connections``
   * - ``User``
     - ``post_delete``
     - ``delete_profile``
   * - ``Osoba``
     - ``pre_delete``
     - ``osoba_delete_repository_container``
   * - ``Osoba``
     - ``post_delete``
     - ``osoba_close_repository_transaction``
   * - ``Organizace``
     - ``pre_delete``
     - ``organizace_delete_repository_container``
   * - ``Organizace``
     - ``post_delete``
     - ``organizace_close_repository_transaction``
   * - ``N/A``
     - ``user_logged_in``
     - ``log_user_signin``