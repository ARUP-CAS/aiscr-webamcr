URL Routing
===========

Dokumentace všech URL adres v aplikaci.


ADB
---

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``zapsat``
     - ``zapsat/<str:dj_ident_cely>``
     - ``views.zapsat``
   * - ``smazat``
     - ``smazat/<str:ident_cely>``
     - ``views.smazat``
   * - ``smazat-vb``
     - ``vb/smazat/<str:ident_cely>``
     - ``views.smazat_vb``

ARCH_Z
------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``detail``
     - ``akce/detail/<str:ident_cely>``
     - ``views.ArcheologickyZaznamDetailView.as_view()``
   * - ``create-dj``
     - ``akce/detail/<str:ident_cely>/dj/zapsat``
     - ``views.DokumentacniJednotkaCreateView.as_view()``
   * - ``detail-dj``
     - ``akce/detail/<str:ident_cely>/dj/<str:dj_ident_cely>``
     - ``views.DokumentacniJednotkaUpdateView.as_view()``
   * - ``create-komponenta``
     - ``akce/detail/<str:ident_cely>/dj/<str:dj_ident_cely>/komponenta/zapsat``
     - ``views.KomponentaCreateView.as_view()``
   * - ``update-komponenta``
     - ``akce/detail/<str:ident_cely>/dj/<str:dj_ident_cely>/komponenta/detail/<str:komponenta_ident_cely>``
     - ``views.KomponentaUpdateView.as_view()``
   * - ``create-pian``
     - ``akce/detail/<str:ident_cely>/dj/<str:dj_ident_cely>/pian/zapsat``
     - ``views.PianCreateView.as_view()``
   * - ``update-pian``
     - ``akce/detail/<str:ident_cely>/dj/<str:dj_ident_cely>/pian/edit/<str:pian_ident_cely>``
     - ``views.PianUpdateView.as_view()``
   * - ``create-adb``
     - ``akce/detail/<str:ident_cely>/dj/<str:dj_ident_cely>/adb/zapsat``
     - ``views.AdbCreateView.as_view()``
   * - ``edit``
     - ``akce/edit/<str:ident_cely>``
     - ``views.edit``
   * - ``zapsat``
     - ``akce/zapsat/<str:projekt_ident_cely>``
     - ``views.zapsat``
   * - ``zapsat-akci``
     - ``akce/zapsat``
     - ``views.zapsat``
   * - ``odeslat``
     - ``stav/odeslat/<str:ident_cely>``
     - ``views.odeslat``
   * - ``archivovat``
     - ``stav/archivovat/<str:ident_cely>``
     - ``views.archivovat``
   * - ``vratit``
     - ``stav/vratit/<str:ident_cely>``
     - ``views.vratit``
   * - ``smazat``
     - ``akce/smazat/<str:ident_cely>``
     - ``views.smazat``
   * - ``zmenit-proj-akci``
     - ``akce/zmenit-proj-akci/<str:ident_cely>``
     - ``views.ProjektAkceChange.as_view()``
   * - ``zmenit-sam-akci``
     - ``akce/zmenit-sam-akci/<str:ident_cely>``
     - ``views.SamostatnaAkceChange.as_view()``
   * - ``pripojit_dokument``
     - ``dokument/pripojit/<str:arch_z_ident_cely>``
     - ``views.pripojit_dokument``
   * - ``pripojit_dokument``
     - ``dokument/pripojit/<str:arch_z_ident_cely>/<str:proj_ident_cely>``
     - ``views.pripojit_dokument``
   * - ``odpojit_dokument``
     - ``dokument/odpojit/<str:arch_z_ident_cely>/<str:ident_cely>``
     - ``views.odpojit_dokument``
   * - ``post_akce2kat``
     - ``mapa-zoom``
     - ``views.post_akce2kat``
   * - ``smazat_akce_vedouci``
     - ``akce/vedouci/smazat/<str:ident_cely>/<int:akce_vedouci_id>``
     - ``views.smazat_akce_vedoucí``
   * - ``post_ajax_get_akce_other_katastr``
     - ``mapa-dalsi-katastry``
     - ``views.GetAkceOtherKatastrView.as_view()``
   * - ``list``
     - ``akce/vyber``
     - ``views.AkceListView.as_view()``
   * - ``index``
     - ``akce/``
     - ``views.AkceIndexView.as_view()``
   * - ``arch-z-autocomplete``
     - ``autocomplete/<str:type>``
     - ``views.ArchZAutocomplete.as_view()``
   * - ``get_archz_table_row``
     - ``radek-tabulky-odkaz``
     - ``views.ArchZTableRowView.as_view()``

CORE
----

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``home``
     - ````
     - ``views.index``
   * - ``post_upload``
     - ``soubor/nahrat/odeslat``
     - ``views.post_upload``
   * - ``update_file``
     - ``soubor/nahrat/<str:typ_vazby>/nahradit/<str:ident_cely>/<int:file_id>``
     - ``views.UpdateFileView.as_view()``
   * - ``upload_file``
     - ``soubor/nahrat/<str:typ_vazby>/<str:ident_cely>``
     - ``views.Uploadfileview.as_view()``
   * - ``download_file``
     - ``soubor/stahnout/<str:typ_vazby>/<str:ident_cely>/<int:pk>``
     - ``views.DownloadFile.as_view()``
   * - ``download_thumbnail``
     - ``soubor/stahnout-nahled/<str:typ_vazby>/<str:ident_cely>/<int:pk>``
     - ``views.DownloadThumbnailSmall.as_view()``
   * - ``download_thumbnail_large``
     - ``soubor/stahnout-nahled-velky/<str:typ_vazby>/<str:ident_cely>/<int:pk>``
     - ``views.DownloadThumbnailLarge.as_view()``
   * - ``delete_file``
     - ``soubor/smazat/<str:typ_vazby>/<str:ident_cely>/<int:pk>``
     - ``views.delete_file``
   * - ``delete_file_DZ``
     - ``soubor/smazat-DZ/<str:typ_vazby>/<str:ident_cely>/<int:pk>``
     - ``views.delete_file_DZ``
   * - ``redirect_ident``
     - ``id/<str:ident_cely>``
     - ``views.redirect_ident_view``
   * - ``prolong_session``
     - ``session/prodlouzit/``
     - ``views.prolong_session``
   * - ``stahnout_metadata``
     - ``metadata/stahnout/<str:model_name>/<str:ident_cely>``
     - ``views.StahnoutMetadataIdentCelyView.as_view()``
   * - ``post_ajax_get_pas_pian_limit``
     - ``mapa-pian-pas``
     - ``post_ajax_get_pas_and_pian_limit``
   * - ``check_authentication``
     - ``check-authentication``
     - ``views.CheckUserAuthentication.as_view()``
   * - ``read_temp_value``
     - ``read-temp-value``
     - ``views.ReadTempValueView.as_view()``
   * - ``delete_temp_value``
     - ``delete-temp-value``
     - ``views.DeleteTempValueView.as_view()``
   * - ``abort_download_update_temp_value``
     - ``abort-download-temp-value``
     - ``views.AbortDownloadUpdateTempValueView.as_view()``
   * - ``rosetta-import-file``
     - ``rosetta/files/import/<str:po_filter>/<str:lang_id>/<int:idx>/``
     - ``views.TranslationImportView.as_view()``
   * - ``rosetta-file-list``
     - ``rosetta/files/<str:po_filter>/``
     - ``views.TranslationFileListWithBackupView.as_view()``
   * - ``rosetta-form``
     - ``rosetta/files/<str:po_filter>/<str:lang_id>/<int:idx>/``
     - ``views.TranslationFormWithBackupView.as_view()``
   * - ``rosetta-download-file``
     - ``rosetta/files/<str:po_filter>/<str:lang_id>/<int:idx>/download/``
     - ``views.TranslationFileDownloadBackup.as_view()``
   * - ``rosetta-smazat-file``
     - ``rosetta/files/<str:po_filter>/<str:lang_id>/<int:idx>/smazat/``
     - ``views.TranslationFileSmazatBackup.as_view()``
   * - ``prometheus-django-metrics``
     - ``metrics``
     - ``views.PrometheusMetricsView.as_view()``
   * - ``application-restart``
     - ``application-restart``
     - ``views.ApplicationRestartView.as_view()``
   * - ``data-import-progress``
     - ``data-import-progress/<str:job_id>``
     - ``views.DataImportProgress.as_view()``
   * - ``data-import-stop``
     - ``data-import-stop/<str:job_id>``
     - ``views.DataImportStop.as_view()``

DJ
--

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``detail``
     - ``detail/<str:typ_vazby>/<str:ident_cely>``
     - ``views.detail``
   * - ``zapsat``
     - ``zapsat/<str:arch_z_ident_cely>``
     - ``views.zapsat``
   * - ``smazat``
     - ``smazat/<str:ident_cely>``
     - ``views.smazat``
   * - ``zmenit-katastr``
     - ``zmenit-katastr/<str:ident_cely>``
     - ``views.ChangeKatastrView.as_view()``

DOKUMENT
--------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``index``
     - ````
     - ``views.DokumentIndexView.as_view()``
   * - ``detail``
     - ``detail/<str:ident_cely>``
     - ``views.DokumentDetailView.as_view()``
   * - ``detail-cast``
     - ``detail/<str:ident_cely>/cast/<str:cast_ident_cely>``
     - ``views.DokumentCastDetailView.as_view()``
   * - ``edit-cast``
     - ``cast/edit/<slug:slug>``
     - ``views.DokumentCastEditView.as_view()``
   * - ``detail-komponenta``
     - ``detail/<str:ident_cely>/komponenta/<str:komp_ident_cely>``
     - ``views.KomponentaDokumentDetailView.as_view()``
   * - ``create-komponenta``
     - ``detail/<str:ident_cely>/cast/<str:cast_ident_cely>/komponenta/zapsat``
     - ``views.KomponentaDokumentCreateView.as_view()``
   * - ``edit-tvar``
     - ``tvar/edit/<str:ident_cely>``
     - ``views.TvarEditView.as_view()``
   * - ``smazat-tvar``
     - ``tvar/smazat/<str:ident_cely>/<int:pk>``
     - ``views.TvarSmazatView.as_view()``
   * - ``vytvorit-cast``
     - ``cast/zapsat/<str:ident_cely>``
     - ``views.VytvoritCastView.as_view()``
   * - ``pripojit-az-cast``
     - ``cast/pripojit-arch-z/<str:ident_cely>``
     - ``views.DokumentCastPripojitAkciView.as_view()``
   * - ``pripojit-projekt-cast``
     - ``cast/pripojit-projekt/<str:ident_cely>``
     - ``views.DokumentCastPripojitProjektView.as_view()``
   * - ``odpojit-cast``
     - ``cast/odpojit/<str:ident_cely>``
     - ``views.DokumentCastOdpojitView.as_view()``
   * - ``smazat-cast``
     - ``cast/smazat/<str:ident_cely>``
     - ``views.DokumentCastSmazatView.as_view()``
   * - ``smazat-neident-akce``
     - ``neident-akce/smazat/<str:ident_cely>``
     - ``views.DokumentNeidentAkceSmazatView.as_view()``
   * - ``edit``
     - ``edit/<str:ident_cely>``
     - ``views.edit``
   * - ``zapsat``
     - ``zapsat``
     - ``views.zapsat``
   * - ``zapsat-do-akce``
     - ``zapsat/do-arch-z/<str:arch_z_ident_cely>``
     - ``views.zapsat_do_akce``
   * - ``zapsat-do-projektu``
     - ``zapsat/do-projektu/<str:proj_ident_cely>``
     - ``views.zapsat_do_projektu``
   * - ``odeslat``
     - ``stav/odeslat/<str:ident_cely>``
     - ``views.odeslat``
   * - ``archivovat``
     - ``stav/archivovat/<str:ident_cely>``
     - ``views.archivovat``
   * - ``vratit``
     - ``stav/vratit/<str:ident_cely>``
     - ``views.vratit``
   * - ``smazat``
     - ``smazat/<str:ident_cely>``
     - ``views.smazat``
   * - ``dokument-autocomplete``
     - ``autocomplete``
     - ``DokumentAutocomplete.as_view()``
   * - ``list``
     - ``vyber``
     - ``DokumentListView.as_view()``
   * - ``index-model-3D``
     - ``model/``
     - ``views.index_model_3D``
   * - ``list-model-3D``
     - ``model/vyber``
     - ``Model3DListView.as_view()``
   * - ``create-model-3D``
     - ``model/zapsat``
     - ``views.create_model_3D``
   * - ``edit-model-3D``
     - ``model/edit/<str:ident_cely>``
     - ``views.edit_model_3D``
   * - ``detail-model-3D``
     - ``model/detail/<str:ident_cely>``
     - ``views.detail_model_3D``
   * - ``get_dokument_table_row``
     - ``radek-tabulky-odkaz``
     - ``views.get_dokument_table_row``
   * - ``get_dokument_table_row_vratit``
     - ``radek-tabulky-odkaz-vratit``
     - ``views.get_dokument_table_row_vratit``
   * - ``post_ajax_get_3d_limit``
     - ``model/mapa-3d``
     - ``post_ajax_get_3d_limit``
   * - ``get_dokumenty_table``
     - ``dokumenty-tabulka/<str:typ_vazby>/<str:ident_cely>``
     - ``DokumentyAzTableView.as_view()``
   * - ``zjisti-licenci-organizace``
     - ``zjisti-licenci-organizace/``
     - ``views.zjisti_licenci_organizace``

EZ
--

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``index``
     - ````
     - ``views.ExterniZdrojIndexView.as_view()``
   * - ``create``
     - ``zapsat``
     - ``views.ExterniZdrojCreateView.as_view()``
   * - ``detail``
     - ``detail/<slug:slug>``
     - ``views.ExterniZdrojDetailView.as_view()``
   * - ``odeslat``
     - ``stav/odeslat/<str:ident_cely>``
     - ``views.ExterniZdrojOdeslatView.as_view()``
   * - ``vratit``
     - ``stav/vratit/<str:ident_cely>``
     - ``views.ExterniZdrojVratitView.as_view()``
   * - ``potvrdit``
     - ``stav/potvrdit/<str:ident_cely>``
     - ``views.ExterniZdrojPotvrditView.as_view()``
   * - ``smazat``
     - ``smazat/<str:ident_cely>``
     - ``views.ExterniZdrojSmazatView.as_view()``
   * - ``edit``
     - ``edit/<slug:slug>``
     - ``views.ExterniZdrojEditView.as_view()``
   * - ``list``
     - ``vyber``
     - ``views.ExterniZdrojListView.as_view()``
   * - ``odpojit_eo``
     - ``ext-odkaz/odpojit-az/<str:ident_cely>/<int:eo_id>``
     - ``views.ExterniOdkazOdpojitView.as_view()``
   * - ``pripojit_eo``
     - ``ext-odkaz/pripojit-az/<str:ident_cely>``
     - ``views.ExterniOdkazPripojitView.as_view()``
   * - ``zmenit_eo``
     - ``ext-odkaz/edit/<str:typ_vazby>/<str:ident_cely>/<slug:slug>``
     - ``views.ExterniOdkazEditView.as_view()``
   * - ``pripojit_eo_do_az``
     - ``ext-odkaz/pripojit-ez/<str:ident_cely>``
     - ``views.ExterniOdkazPripojitDoAzView.as_view()``
   * - ``odpojit_eo_az``
     - ``ext-odkaz/odpojit-ez/<str:ident_cely>/<int:eo_id>``
     - ``views.ExterniOdkazOdpojitAZView.as_view()``
   * - ``ez-autocomplete``
     - ``autocomplete``
     - ``views.ExterniZdrojAutocomplete.as_view()``
   * - ``get_ez_table_row``
     - ``radek-tabulky-odkaz``
     - ``views.ExterniZdrojTableRowView.as_view()``
   * - ``get_ez_odkazy_table``
     - ``ext-odkaz-tabulka/<str:ident_cely>``
     - ``views.EzOdkazyTableView.as_view()``

FEDORA
------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``continue-processing``
     - ``continue-processing/<str:job_id>``
     - ``views.ContinueMedataProcessing.as_view()``

HEALTHCHECK
-----------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``healthcheck``
     - ````
     - ``views.HealthCheckView.as_view()``

HESLAR
------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``katastr-autocomplete``
     - ``katastry/``
     - ``RuianKatastrAutocomplete.as_view()``
   * - ``zjisti-katastr-souradnic``
     - ``mapa-zjisti-katastr/``
     - ``zjisti_katastr_souradnic``
   * - ``get-initial-value``
     - ``zjisti-vychozi-hodnotu/``
     - ``zjisti_vychozi_hodnotu``
   * - ``get-nadrazena-value``
     - ``zjisti-nadrazenou-hodnotu/``
     - ``zjisti_nadrazenou_hodnotu``
   * - ``create_osoba``
     - ``osoba/zapsat``
     - ``create_osoba``
   * - ``osoba-autocomplete``
     - ``osoba/autocomplete/``
     - ``OsobaAutocomplete.as_view()``
   * - ``dokument-typ-autocomplete``
     - ``dokument-typ/``
     - ``DokumentTypAutocomplete.as_view()``
   * - ``dokument-format-autocomplete``
     - ``dokument-format/``
     - ``DokumentFormatAutocomplete.as_view()``
   * - ``pristupnost-autocomplete``
     - ``pristupnost/``
     - ``PristupnostAutocomplete.as_view()``
   * - ``heslar-autocomplete``
     - ``heslar/autocomplete/``
     - ``HeslarAutocompleteView.as_view()``
   * - ``heslar_nazev-autocomplete``
     - ``heslar-nazev/autocomplete/``
     - ``HeslarNazevAutocompleteView.as_view()``

HISTORIE
--------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``projekt``
     - ``projekt/<str:ident_cely>``
     - ``ProjektHistorieListView.as_view()``
   * - ``akce``
     - ``arch-z/<str:ident_cely>``
     - ``AkceHistorieListView.as_view()``
   * - ``dokument``
     - ``dokument/<str:ident_cely>``
     - ``DokumentHistorieListView.as_view()``
   * - ``pas``
     - ``pas/<str:ident_cely>``
     - ``SamostatnyNalezHistorieListView.as_view()``
   * - ``soubor``
     - ``soubor/<int:soubor_id>``
     - ``SouborHistorieListView.as_view()``
   * - ``spoluprace``
     - ``spoluprace/<int:pk>``
     - ``SpolupraceHistorieListView.as_view()``
   * - ``lokalita``
     - ``lokalita/<str:ident_cely>``
     - ``LokalitaHistorieListView.as_view()``
   * - ``uzivatel``
     - ``uzivatel/<str:ident_cely>``
     - ``UzivatelHistorieListView.as_view()``
   * - ``ez``
     - ``ez/<str:ident_cely>``
     - ``ExterniZdrojHistorieListView.as_view()``

KOMPONENTA
----------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``detail``
     - ``detail/<str:typ_vazby>/<str:ident_cely>``
     - ``views.detail``
   * - ``zapsat``
     - ``zapsat/<str:typ_vazby>/<str:dj_ident_cely>``
     - ``views.zapsat``
   * - ``smazat``
     - ``smazat/<str:typ_vazby>/<str:ident_cely>``
     - ``views.smazat``

LOKALITA
--------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``index``
     - ````
     - ``views.LokalitaIndexView.as_view()``
   * - ``create``
     - ``zapsat``
     - ``views.LokalitaCreateView.as_view()``
   * - ``create-dj``
     - ``detail/<slug:slug>/dj/zapsat``
     - ``views.LokalitaDokumentacniJednotkaCreateView.as_view()``
   * - ``detail-dj``
     - ``detail/<slug:slug>/dj/<str:dj_ident_cely>``
     - ``views.LokalitaDokumentacniJednotkaUpdateView.as_view()``
   * - ``create-komponenta``
     - ``detail/<slug:slug>/dj/<str:dj_ident_cely>/komponenta/zapsat``
     - ``views.LokalitaKomponentaCreateView.as_view()``
   * - ``update-komponenta``
     - ``detail/<slug:slug>/dj/<str:dj_ident_cely>/komponenta/detail/<str:komponenta_ident_cely>``
     - ``views.LokalitaKomponentaUpdateView.as_view()``
   * - ``create-pian``
     - ``detail/<slug:slug>/dj/<str:dj_ident_cely>/pian/zapsat``
     - ``views.LokalitaPianCreateView.as_view()``
   * - ``update-pian``
     - ``detail/<slug:slug>/dj/<str:dj_ident_cely>/pian/edit/<str:pian_ident_cely>``
     - ``views.LokalitaPianUpdateView.as_view()``
   * - ``detail``
     - ``detail/<slug:slug>``
     - ``views.LokalitaDetailView.as_view()``
   * - ``edit``
     - ``edit/<slug:slug>``
     - ``views.LokalitaEditView.as_view()``
   * - ``list``
     - ``vyber``
     - ``views.LokalitaListView.as_view()``

NALEZ
-----

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``smazat_nalez``
     - ``smazat/<str:typ_vazby>/<str:typ>/<str:ident_cely>``
     - ``views.smazat_nalez``
   * - ``edit_nalez``
     - ``edit/<str:typ_vazby>/<str:komp_ident_cely>``
     - ``views.edit_nalez``

NEIDENTAKCE
-----------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``edit``
     - ``edit/<slug:slug>``
     - ``views.NeidentAkceEditView.as_view()``

NOTIFIKACE_PROJEKTY
-------------------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``list``
     - ````
     - ``PesListView.as_view()``
   * - ``zapsat``
     - ``zapsat/``
     - ``PesCreateView.as_view()``
   * - ``smazat``
     - ``smazat/<int:pk>``
     - ``PesSmazatView.as_view()``

OZNAMENI
--------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``index``
     - ````
     - ``OznameniZapsatView.as_view()``
   * - ``index``
     - ``zapsat/<str:ident_cely>``
     - ``OznameniZapsatView.as_view()``
   * - ``index2``
     - ``dokumentace``
     - ``OznameniDokumentaceView.as_view()``
   * - ``index2``
     - ``dokumentace/<str:ident_cely>``
     - ``OznameniDokumentaceView.as_view()``
   * - ``index3``
     - ``potvrzeni/<str:ident_cely>``
     - ``OznameniPotvrzeniView.as_view()``
   * - ``post_poi2kat``
     - ``mapa-zjisti-katastr``
     - ``post_poi2kat``

PAS
---

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``index``
     - ````
     - ``views.index``
   * - ``create``
     - ``zapsat``
     - ``views.SamostatnyNalezCreateView.as_view()``
   * - ``create-from-project``
     - ``zapsat/<str:ident_cely>``
     - ``views.SamostatnyNalezCreateView.as_view()``
   * - ``create-copy``
     - ``zapsat/kopie/<str:ident_cely>``
     - ``views.SamostatnyNalezCreateView.as_view()``
   * - ``detail``
     - ``detail/<str:ident_cely>``
     - ``views.detail``
   * - ``edit``
     - ``edit/<str:ident_cely>``
     - ``views.edit``
   * - ``edit_ulozeni``
     - ``ulozeni/edit/<str:ident_cely>``
     - ``views.edit_ulozeni``
   * - ``vratit``
     - ``stav/vratit/<str:ident_cely>``
     - ``views.vratit``
   * - ``odeslat``
     - ``stav/odeslat/<str:ident_cely>``
     - ``views.odeslat``
   * - ``potvrdit``
     - ``stav/potvrdit/<str:ident_cely>``
     - ``views.potvrdit``
   * - ``archivovat``
     - ``stav/archivovat/<str:ident_cely>``
     - ``views.archivovat``
   * - ``list``
     - ``vyber``
     - ``SamostatnyNalezListView.as_view()``
   * - ``smazat``
     - ``smazat/<str:ident_cely>``
     - ``views.smazat``
   * - ``spoluprace_zadost``
     - ``spoluprace/zadost``
     - ``views.zadost``
   * - ``spoluprace_list``
     - ``spoluprace/vyber``
     - ``UzivatelSpolupraceListView.as_view()``
   * - ``spoluprace_aktivace_email``
     - ``spoluprace/aktivace-email/<int:pk>``
     - ``views.AktivaceEmailView.as_view()``
   * - ``spoluprace_aktivace``
     - ``spoluprace/aktivovat/<int:pk>``
     - ``views.aktivace``
   * - ``spoluprace_deaktivace``
     - ``spoluprace/deaktivovat/<int:pk>``
     - ``views.DeaktivaceSpolupraceView.as_view()``
   * - ``post_point_position_2_katastre``
     - ``mapa-zjisti-katastr``
     - ``views.post_point_position_2_katastre``
   * - ``post_point_position_2_katastre_with_geom``
     - ``mapa-zjisti-katastr-geom``
     - ``views.post_point_position_2_katastre_with_geom``
   * - ``spoluprace_smazani``
     - ``spoluprace/smazat/<int:pk>``
     - ``views.smazat_spolupraci``
   * - ``get_projekt_pas_table``
     - ``projekt-pas-tabulka/<str:ident_cely>``
     - ``ProjektPasTableView.as_view()``

PIAN
----

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``detail``
     - ``detail/<str:ident_cely>``
     - ``views.detail``
   * - ``create``
     - ``zapsat/<str:dj_ident_cely>``
     - ``views.create``
   * - ``potvrdit``
     - ``stav/potvrdit/<str:dj_ident_cely>``
     - ``views.potvrdit``
   * - ``odpojit``
     - ``odpojit/<str:dj_ident_cely>``
     - ``views.odpojit``
   * - ``pian-autocomplete``
     - ``autocomplete/``
     - ``PianAutocomplete.as_view()``
   * - ``importovat-pian``
     - ``importovat``
     - ``views.ImportovatPianView.as_view()``
   * - ``mapaDj``
     - ``mapa-connections/<str:ident_cely>``
     - ``views.mapa_dj``

PID
---

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``doi-autocomplete``
     - ``doi-autocomplete``
     - ``views.DoiAutocompleteView.as_view()``
   * - ``orcid-autocomplete``
     - ``orcid-autocomplete``
     - ``views.OrcidAutocompleteView.as_view()``
   * - ``ror-autocomplete``
     - ``ror-autocomplete``
     - ``views.RorAutocompleteView.as_view()``
   * - ``wikidata-autocomplete``
     - ``wikidata-autocomplete``
     - ``views.WikiDataAutocompleteView.as_view()``
   * - ``continue-processing``
     - ``continue-processing/<str:job_id>/<str:performed_action>``
     - ``views.ContinuePidProcessing.as_view()``

PROJEKT
-------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``index``
     - ````
     - ``index``
   * - ``detail``
     - ``detail/<str:ident_cely>``
     - ``detail``
   * - ``create``
     - ``zapsat``
     - ``create``
   * - ``edit``
     - ``edit/<str:ident_cely>``
     - ``edit``
   * - ``smazat``
     - ``smazat/<str:ident_cely>``
     - ``smazat``
   * - ``list``
     - ``vyber``
     - ``ProjektListView.as_view()``
   * - ``projekt_schvalit``
     - ``stav/schvalit/<str:ident_cely>``
     - ``schvalit``
   * - ``projekt_prihlasit``
     - ``stav/prihlasit/<str:ident_cely>``
     - ``prihlasit``
   * - ``projekt_zahajit_v_terenu``
     - ``stav/zahajit-v-terenu/<str:ident_cely>``
     - ``zahajit_v_terenu``
   * - ``projekt_ukoncit_v_terenu``
     - ``stav/ukoncit-v-terenu/<str:ident_cely>``
     - ``ukoncit_v_terenu``
   * - ``projekt_uzavrit``
     - ``stav/uzavrit/<str:ident_cely>``
     - ``uzavrit``
   * - ``projekt_archivovat``
     - ``stav/archivovat/<str:ident_cely>``
     - ``archivovat``
   * - ``projekt_navrhnout_ke_zruseni``
     - ``stav/navrhnout-ke-zruseni/<str:ident_cely>``
     - ``navrhnout_ke_zruseni``
   * - ``projekt_zrusit``
     - ``stav/zrusit/<str:ident_cely>``
     - ``zrusit``
   * - ``projekt_vratit``
     - ``stav/vratit/<str:ident_cely>``
     - ``vratit``
   * - ``projekt_vratit_navrh_zruseni``
     - ``stav/vratit-navrh-zruseni/<str:ident_cely>``
     - ``vratit_navrh_zruseni``
   * - ``post_ajax_get_project_one``
     - ``akce-get-projekt``
     - ``post_ajax_get_project_one``
   * - ``post_ajax_get_projects_limit``
     - ``mapa-projekty``
     - ``post_ajax_get_projects_limit``
   * - ``post_ajax_get_project_pas_limit``
     - ``mapa-pas``
     - ``ProjectPasFromEnvelopeView.as_view()``
   * - ``post_ajax_get_project_pian_limit``
     - ``mapa-pian``
     - ``ProjectPianFromEnvelopeView.as_view()``
   * - ``odpojit_dokument``
     - ``dokument/odpojit/<str:proj_ident_cely>/<str:ident_cely>``
     - ``odpojit_dokument``
   * - ``pripojit_dokument``
     - ``dokument/pripojit/<str:proj_ident_cely>``
     - ``pripojit_dokument``
   * - ``generovat_oznameni``
     - ``generovat-oznameni/<str:ident_cely>``
     - ``generovat_oznameni``
   * - ``generovat_expertni_list``
     - ``generovat-expertni-list/<str:ident_cely>``
     - ``generovat_expertni_list``
   * - ``projekt-autocomplete-bez-zrusenych``
     - ``autocomplete/<str:typ>``
     - ``ProjektAutocompleteBezZrusenych.as_view()``
   * - ``get_projekt_table_row``
     - ``radek-tabulky-odkaz``
     - ``ProjectTableRowView.as_view()``
   * - ``pridat-oznamovatele``
     - ``oznamovatel/zapsat/<str:ident_cely>``
     - ``OznamovatelCreateView.as_view()``
   * - ``zadost-udaje-oznamovatel``
     - ``zadost-udaje-oznamovatel/<str:ident_cely>``
     - ``ZadostUdajeOznamovatelView.as_view()``
   * - ``upravit-datum-oznameni``
     - ``upravit-datum-oznameni/<str:ident_cely>``
     - ``UpravitDatumOznameniView.as_view()``
   * - ``zadost-odhlaseni-projektu``
     - ``zadost-odhlaseni-projektu/<str:ident_cely>``
     - ``ZadostOdhlaseniProjektuView.as_view()``
   * - ``zadost-zruseni-projektu``
     - ``zadost-zruseni-projektu/<str:ident_cely>``
     - ``ZadostZruseniProjektuView.as_view()``

UZIVATEL
--------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``uzivatel-autocomplete``
     - ``uzivatel/autocomplete/``
     - ``UzivatelAutocomplete.as_view()``
   * - ``uzivatel-autocomplete-public``
     - ``uzivatel/autocomplete-public/``
     - ``UzivatelAutocompletePublic.as_view()``
   * - ``update-uzivatel``
     - ``uzivatel/edit/``
     - ``UserAccountUpdateView.as_view()``
   * - ``update-notifications``
     - ``uzivatel/notifikace/edit/``
     - ``update_notifications``
   * - ``N/A``
     - ``api/token-auth/``
     - ``ObtainAuthTokenWithUpdate.as_view()``
   * - ``N/A``
     - ``api/uzivatel-info/``
     - ``GetUserInfo.as_view()``
   * - ``delete-uzivatel-request``
     - ``uzivatel/delete-request/``
     - ``UserDeleteRequest.as_view()``

VYPIS
-----

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Název
     - URL
     - Cíl
   * - ``vypis``
     - ``<str:typ_vazby>/<str:ident_cely>/``
     - ``VypisView.as_view()``
   * - ``vypis_only``
     - ``cisty/<str:typ_vazby>/<str:ident_cely>/``
     - ``VypisOnlyView.as_view()``
   * - ``vypisy``
     - ``list/<str:typ_vazby>/<str:identy_cele>/``
     - ``VypisListView.as_view()``