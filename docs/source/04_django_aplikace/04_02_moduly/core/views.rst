CORE views
==========

Definice views.

Třídy
------

.. py:class:: DownloadFile

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get()


.. py:class:: DownloadThumbnailSmall

   Popis není k dispozici.


.. py:class:: DownloadThumbnailLarge

   Popis není k dispozici.


.. py:class:: UpdateFileView

   Třída pohledu pro zobrazení stránky pro nahrazení souboru.

   **Metody:**

   .. py:method:: get()

   .. py:method:: post()

   .. py:method:: get_context_data()


.. py:class:: Uploadfileview

   Třída pohledu pro zobrazení stránky s uploadem souboru.

   **Metody:**

   .. py:method:: get_zaznam()

   .. py:method:: get_context_data()

   .. py:method:: dispatch()

   .. py:method:: post()


.. py:class:: ExportMixinDate

   Mixin pro získaní názvu exportovaného souboru.

   **Metody:**

   .. py:method:: get_export_filename()


.. py:class:: PermissionFilterMixin

   Popis není k dispozici.

   **Metody:**

   .. py:method:: check_filter_permission()

   .. py:method:: filter_by_permission()

   .. py:method:: add_status_lookup()

   .. py:method:: add_ownership_lookup()

   .. py:method:: add_accessibility_lookup()


.. py:class:: SearchListView

   Třída pohledu pro tabulky záznamů, která je použita jako základ pro jednotlivé pohledy.

   **Metody:**

   .. py:method:: create_export()

   .. py:method:: init_translations()

   .. py:method:: get_paginate_by()

   .. py:method:: get_context_data()

   .. py:method:: get_queryset()

   .. py:method:: get()


.. py:class:: StahnoutDataHistorickaView

   Třída pohledu pro stažení historické verze souboru nebo metadat z Fedory

   **Metody:**

   .. py:method:: get()


.. py:class:: CheckUserAuthentication

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get()


.. py:class:: ReadTempValueView

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get()


.. py:class:: DeleteTempValueView

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get()


.. py:class:: AbortDownloadUpdateTempValueView

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get()


.. py:class:: RosettaFileLevelMixinWithBackup

   Třída podledu pro práci s prekladmi doplnena o backup osubory.

   **Metody:**

   .. py:method:: po_file_path()

      Based on the url kwargs, infer and return the path to the .po file to
      be shown/updated.
      
      Throw a 404 if a file isn't found.


.. py:class:: TranslationImportView

   Třída pohledu pro import prekladových souboru.

   **Metody:**

   .. py:method:: form_valid()

   .. py:method:: get_context_data()

   .. py:method:: handle_uploaded_file()


.. py:class:: TranslationFileListWithBackupView

   Třída pohledu pro zobrazení prekladových souboru s backup souborami.

   **Metody:**

   .. py:method:: get_context_data()


.. py:class:: TranslationFormWithBackupView

   Třída pohledu pro zobrazení formulaře s prekladmi i pro backup soubory

   **Metody:**

   .. py:method:: get_context_data()


.. py:class:: TranslationFileDownloadBackup

   Třída pohledu pro stahování prekladových souboru is backup souborami.

   **Metody:**

   .. py:method:: get()


.. py:class:: TranslationFileSmazatBackup

   Třída pohledu pro smazání backup prekladových souboru.

   **Metody:**

   .. py:method:: get()

   .. py:method:: post()


.. py:class:: PrometheusMetricsView

   Třída pohledu pro zobrazení prometheus metrík doplňena o mixin pro filtrování IP adres.

   **Metody:**

   .. py:method:: get()


.. py:class:: ApplicationRestartView

   Třída pohledu pro restartovani uwsgi aplikace.

   **Metody:**

   .. py:method:: post()


.. py:class:: DataImportProgress

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get()


.. py:class:: DataImportStop

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get()


Funkce
------

.. py:function:: index(request)

   Funkce podledu pro zobrazení hlavní stránky.

.. py:function:: delete_file_DZ(request, typ_vazby, ident_cely, pk)

   Funkce pohledu pro smazání souboru z dropzone. Funkce maže jak záznam v DB tak i soubor na disku.

.. py:function:: delete_file(request, typ_vazby, ident_cely, pk)

   Funkce pohledu pro smazání souboru. Funkce maže jak záznam v DB tak i soubor na disku.

.. py:function:: post_upload(request)

   Funkce pohledu pro upload souboru a k navázaní ke správnemu záznamu.

.. py:function:: get_finds_soubor_name(find, filename, add_to_index)

   Funkce pro získaní jména souboru pro samostatný nález.

.. py:function:: get_projekt_soubor_name(projekt, file_name)

   Funkce pro získaní jména souboru pro projekt.

.. py:function:: check_stav_changed(request, zaznam)

   Funkce pro oveření jestli se zmenil stav záznamu pri uložení formuláře oproti jeho načtení.

.. py:function:: redirect_ident_view(request, ident_cely)

   Funkce pro získaní správneho redirectu na záznam podle ident%cely záznamu.

.. py:function:: prolong_session(request)

   Funkce pohledu pro prodloužení prihlášení.

.. py:function:: post_ajax_get_pas_and_pian_limit(request)

   Funkce pohledu pro získaní heatmapy.

.. py:function:: check_soubor_vazba(typ_vazby, ident, id_zaznamu)

   Popis není k dispozici.
