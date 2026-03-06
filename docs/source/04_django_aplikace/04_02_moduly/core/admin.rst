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

      :param request: Aktuální HTTP request předaný view/funkci.
      :param obj: Objekt, se kterým funkce pracuje.
      :param form: Formulářová instance zpracovávaná funkcí.
      :param change: Číselná nebo geometrická hodnota `change` použitá při výpočtu nebo transformaci.

   .. py:method:: has_module_permission()

      Metoda pro určení práv na modul odstávky.

      :param request: Aktuální HTTP request předaný view/funkci.

   .. py:method:: has_view_permission()

      Metoda pro určení práv na videní odstávky.

      :param request: Aktuální HTTP request předaný view/funkci.
      :param obj: Objekt, se kterým funkce pracuje.
      :param args: Dodatečné poziční argumenty předané voláním.

   .. py:method:: has_add_permission()

      Metoda pro určení práv na přidání odstávky. Není možné přidat více než jednu odstávku.

      :param request: Aktuální HTTP request předaný view/funkci.
      :param args: Dodatečné poziční argumenty předané voláním.

   .. py:method:: has_change_permission()

      Metoda pro určení práv pro úpravu odstávky.

      :param request: Aktuální HTTP request předaný view/funkci.
      :param obj: Objekt, se kterým funkce pracuje.
      :param args: Dodatečné poziční argumenty předané voláním.

   .. py:method:: file_handler()

      Pomocní metoda pro úpravu template zobrazených během odstávky.

      :param language: Textový název, klíč nebo zpráva ``language`` používaná v rámci operace.
      :param form: Formulářová instance zpracovávaná funkcí.


.. py:class:: CustomAdminSettingsAdmin

   Admin panel pro vlastních nastavení.


.. py:class:: PermissionAdmin

   Třída admin panelu pro zobrazení a správu oprávnení.

   **Metody:**

   .. py:method:: changelist_view()

      Provádí operaci changelist view.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param extra_context: Kolekce ``extra_context`` zpracovávaná touto funkcí.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_urls()

      Metoda pri definici dodatečných url.

   .. py:method:: import_file()

      Metoda view pro zobrazení formuláře a samtotný import oprávnení z excelu.

      :param request: Aktuální HTTP request předaný view/funkci.

   .. py:method:: import_success()

      Metoda view pro zobrazení tabulky s výsledkom importu.

      :param request: Aktuální HTTP request předaný view/funkci.

   .. py:method:: reload_permissions()

      Metoda view pro automatický import oprávnění z csv v gitu a zobrazení výsledků importu.

      :param request: Aktuální HTTP request předaný view/funkci.


.. py:class:: PermissionSkipAdmin

   Třída admin panelu pro zobrazení a správu proskakovani oprávnení.

   **Metody:**

   .. py:method:: changelist_view()

      Provádí operaci changelist view.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param extra_context: Kolekce ``extra_context`` zpracovávaná touto funkcí.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_urls()

      Metoda pri definici dodatečných url.

   .. py:method:: validate_sheet()

      Metoda pro validaci importovaného excelu a jeho úpravu.

      :param sheet: Záznam/objekt ``sheet``, který funkce čte, validuje nebo upravuje.

   .. py:method:: import_skip_file()

      Metoda view pro zobrazení formuláře a samtotný import oprávnení z excelu.

      :param request: Aktuální HTTP request předaný view/funkci.

   .. py:method:: check_save_row()

      Ověří save row.

      :param row: Záznam/objekt ``row``, který funkce čte, validuje nebo upravuje.

   .. py:method:: import_skip_success()

      Metoda view pro zobrazení tabulky s výsledkom importu.

      :param request: Aktuální HTTP request předaný view/funkci.

   .. py:method:: export_as_csv()

      Exportuje as csv.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param queryset: Vstupní queryset, který má být dále zpracován.


.. py:class:: FedoraCustomAdminSite

   Implementuje komponentu ``FedoraCustomAdminSite`` v rámci aplikace.

   **Metody:**

   .. py:method:: _read_file()

      Načte file.

      :param uploaded_file: Cesta, URL nebo název zdroje ``uploaded_file``, ze kterého funkce čte nebo kam zapisuje.
      :param context: Kontextová data používaná při serializaci nebo renderování.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: update_doi()

      Aktualizuje doi. v aplikaci.

      :param request: Django HTTP požadavek použitý při zpracování.

   .. py:method:: update_metadata_file_upload()

      Aktualizuje metadata file upload.

      :param request: Django HTTP požadavek použitý při zpracování.

   .. py:method:: import_data()

      Creates a view for importing data from a zip file.

      :param request: Aktuální HTTP request předaný view/funkci.

   .. py:method:: get_urls()

      Vrací urls. v aplikaci.

