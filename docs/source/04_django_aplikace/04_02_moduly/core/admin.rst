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

   .. py:method:: get_urls()

      Metoda pri definici dodatečných url.

   .. py:method:: validate_sheet()

      Metoda pro validaci importovaného excelu a jeho úpravu.

   .. py:method:: import_skip_file()

      Metoda view pro zobrazení formuláře a samtotný import oprávnení z excelu.

   .. py:method:: check_save_row()

   .. py:method:: import_skip_success()

      Metoda view pro zobrazení tabulky s výsledkom importu.

   .. py:method:: export_as_csv()


.. py:class:: FedoraCustomAdminSite

   Popis není k dispozici.

   **Metody:**

   .. py:method:: _read_file()

   .. py:method:: update_doi()

   .. py:method:: update_metadata_file_upload()

   .. py:method:: import_data()

      Creates a view for importing data from a zip file.

   .. py:method:: get_urls()

