CORE admin
==========

Konfigurace Django admin.

Třídy
------

.. py:class:: OdstavkaSystemuAdmin

   Třída admin panelu pro zobrazení odstávek systému.
   Pomocí ní se zobrazuje tabulka s odstávkami, detail a jednotlivé akce.

   **Metody:**

   .. py:method:: save_model()

      Metoda na uložení modelu odstávky.
      Jednotlivé texty z modelu se ukladají do textú prekladů a template.
      Po uložení se restartuje wsgi pro načítaní nových prekladů.

   .. py:method:: has_module_permission()

      Metoda pro určení práv na modul odstávky.

   .. py:method:: has_view_permission()

      Metoda pro určení práv na videní odstávky.

   .. py:method:: has_add_permission()

      Metoda pro určení práv na přidání odstávky. Není možné přidat více než jednu odstávku.

   .. py:method:: has_change_permission()

      Metoda pro určení práv pro úpravu odstávky.

   .. py:method:: file_handler()

      Pomocní metoda pro úpravu template zobrazených během odstávky.


.. py:class:: CustomAdminSettingsAdmin

   Admin panel pro vlastních nastavení.


.. py:class:: PermissionAdmin

   Třída admin panelu pro zobrazení a správu oprávnení.

   **Metody:**

   .. py:method:: changelist_view()

      Provádí operaci changelist view.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param extra_context: Vstupní hodnota ``extra_context`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_urls()

      Metoda pri definici dodatečných url.

   .. py:method:: import_file()

      Metoda view pro zobrazení formuláře a samtotný import oprávnení z excelu.

   .. py:method:: import_success()

      Metoda view pro zobrazení tabulky s výsledkom importu.

   .. py:method:: reload_permissions()

      Metoda view pro automatický import oprávnění z csv v gitu a zobrazení výsledků importu.


.. py:class:: PermissionSkipAdmin

   Třída admin panelu pro zobrazení a správu proskakovani oprávnení.

   **Metody:**

   .. py:method:: changelist_view()

      Provádí operaci changelist view.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param extra_context: Vstupní hodnota ``extra_context`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_urls()

      Metoda pri definici dodatečných url.

   .. py:method:: validate_sheet()

      Metoda pro validaci importovaného excelu a jeho úpravu.

   .. py:method:: import_skip_file()

      Metoda view pro zobrazení formuláře a samtotný import oprávnení z excelu.

   .. py:method:: check_save_row()

      Ověří save row.

      :param row: Vstupní hodnota ``row`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

   .. py:method:: import_skip_success()

      Metoda view pro zobrazení tabulky s výsledkom importu.

   .. py:method:: export_as_csv()

      Exportuje as csv.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: FedoraCustomAdminSite

   Implementuje komponentu ``FedoraCustomAdminSite`` v rámci aplikace.

   **Metody:**

   .. py:method:: _read_file()

      Načte file.

      :param uploaded_file: Vstupní hodnota ``uploaded_file`` pro danou operaci.
      :param context: Vstupní hodnota ``context`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: update_doi()

      Aktualizuje doi.

      :param request: Django HTTP požadavek použitý při zpracování.
      :return: Vrací výsledek provedené operace.

   .. py:method:: update_metadata_file_upload()

      Aktualizuje metadata file upload.

      :param request: Django HTTP požadavek použitý při zpracování.
      :return: Vrací výsledek provedené operace.

   .. py:method:: import_data()

      Creates a view for importing data from a zip file.

   .. py:method:: get_urls()

      Vrací urls.

      :return: Vrací načtená data odpovídající vstupním parametrům.

