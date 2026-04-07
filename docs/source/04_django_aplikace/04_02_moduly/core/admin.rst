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

      :param request: Parametr ``request`` se předává do volání ``int()``, ``utime()``, pracuje se s atributy ``environ``.
      :param obj: Parametr ``obj`` předává se do volání ``save_model()``.
      :param form: Parametr ``form`` se předává do volání ``file_handler()``, ``save_model()``, pracuje se s atributy ``cleaned_data``.
      :param change: Parametr ``change`` se předává do volání ``save_model()``.

   .. py:method:: has_module_permission()

      Metoda pro určení práv na modul odstávky.

      :param request: Parametr ``request`` pracuje se s atributy ``user``, vstupuje do návratové hodnoty.

          :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: has_view_permission()

      Metoda pro určení práv na videní odstávky.

      :param request: Parametr ``request`` pracuje se s atributy ``user``, vstupuje do návratové hodnoty.
      :param obj: Volitelný objekt modelu, na který se oprávnění vztahuje (není využit).
      :param args: Další poziční argumenty (nejsou využity).

          :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: has_add_permission()

      Metoda pro určení práv na přidání odstávky. Není možné přidat více než jednu odstávku.

      :param request: Parametr ``request`` pracuje se s atributy ``user``, vstupuje do návratové hodnoty.
      :param args: Další poziční argumenty (nejsou využity).

          :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: has_change_permission()

      Metoda pro určení práv pro úpravu odstávky.

      :param request: Parametr ``request`` pracuje se s atributy ``user``, vstupuje do návratové hodnoty.
      :param obj: Volitelný objekt modelu, na který se oprávnění vztahuje (není využit).
      :param args: Další poziční argumenty (nejsou využity).

          :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   .. py:method:: file_handler()

      Pomocní metoda pro úpravu template zobrazených během odstávky.

      :param language: Textový název, klíč nebo zpráva ``language`` používaná v rámci operace.
      :param form: Parametr ``form`` se předává do volání ``replace_with()``, pracuje se s atributy ``cleaned_data``.


.. py:class:: CustomAdminSettingsAdmin

   Admin panel pro vlastních nastavení.


.. py:class:: PermissionAdmin

   Třída admin panelu pro zobrazení a správu oprávnení.

   **Metody:**

   .. py:method:: changelist_view()

      Zobrazí přehledovou stránku oprávnění s přidaným příznakem pro zobrazení tlačítka importu.

      :param request: HTTP požadavek od klienta.
      :param extra_context: Volitelný slovník s dalším kontextem předaným do šablony.

      :return: HTTP odpověď s vyrenderovanou šablonou přehledové stránky.

   .. py:method:: get_urls()

      Metoda pri definici dodatečných url.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: import_file()

      Metoda view pro zobrazení formuláře a samtotný import oprávnení z excelu.

      :param request: Parametr ``request`` se předává do volání ``message_user()``, ``each_context()``, pracuje se s atributy ``method``, ``FILES``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``TemplateResponse()``.

   .. py:method:: import_success()

      Metoda view pro zobrazení tabulky s výsledkom importu.

      :param request: Parametr ``request`` se předává do volání ``each_context()``, ``message_user()``, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``TemplateResponse()``.

   .. py:method:: reload_permissions()

      Metoda view pro automatický import oprávnění z csv v gitu a zobrazení výsledků importu.

      :param request: Parametr ``request`` se předává do volání ``message_user()``, ``each_context()``, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``TemplateResponse()``.


.. py:class:: PermissionSkipAdmin

   Třída admin panelu pro zobrazení a správu proskakovani oprávnení.

   **Metody:**

   .. py:method:: changelist_view()

      Zobrazí přehledovou stránku výjimek oprávnění s přidaným příznakem pro zobrazení tlačítka importu.

      :param request: HTTP požadavek od klienta.
      :param extra_context: Volitelný slovník s dalším kontextem předaným do šablony.

      :return: HTTP odpověď s vyrenderovanou šablonou přehledové stránky.

   .. py:method:: get_urls()

      Metoda pri definici dodatečných url.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: validate_sheet()

      Metoda pro validaci importovaného excelu a jeho úpravu.

      :param sheet: Parametr ``sheet`` pracuje se s atributy ``columns``, ovlivňuje větvení podmínek.

          :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
          :raises WrongCSVError: Vyvolá se při splnění podmínky ``not sheet.columns[0] == 'IDENT_CELY' or not sheet.columns[1] == 'IDENT_LIST'``.

   .. py:method:: import_skip_file()

      Metoda view pro zobrazení formuláře a samtotný import oprávnení z excelu.

      :param request: Parametr ``request`` se předává do volání ``message_user()``, ``each_context()``, pracuje se s atributy ``method``, ``FILES``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``TemplateResponse()``.

   .. py:method:: check_save_row()

      Ověří save row.

      :param row: Parametr ``row`` předává se do volání ``create()``, ``get()``, pracuje se s atributy ``iloc``.

          :return: Vrací str.

   .. py:method:: import_skip_success()

      Metoda view pro zobrazení tabulky s výsledkom importu.

      :param request: Parametr ``request`` se předává do volání ``each_context()``, ``message_user()``, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``TemplateResponse()``.

   .. py:method:: export_as_csv()

      Exportuje vybrané záznamy PermissionsSkip do CSV souboru ke stažení.

      :param request: HTTP požadavek od klienta.
      :param queryset: Queryset vybraných záznamů PermissionsSkip určených k exportu.

      :return: HTTP odpověď s CSV souborem ke stažení.


.. py:class:: FedoraCustomAdminSite

   Implementuje komponentu ``FedoraCustomAdminSite`` v rámci aplikace.

   **Metody:**

   .. py:method:: _read_file()

      Načte file.

      :param uploaded_file: Parametr ``uploaded_file`` se předává do volání ``read_csv()``, ``read_excel()``, pracuje se s atributy ``content_type``, ovlivňuje větvení podmínek.
      :param context: Parametr ``context`` slouží jako vstup pro logiku funkce ``_read_file``.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: update_doi()

      Aktualizuje doi. v aplikaci.

      :param request: Parametr ``request`` předává se do volání ``get_app_list()``, ``each_context()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``TemplateResponse()``.

   .. py:method:: update_metadata_file_upload()

      Aktualizuje metadata file upload.

      :param request: Parametr ``request`` předává se do volání ``get_app_list()``, ``each_context()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``TemplateResponse()``.

   .. py:method:: get_urls()

      Vrací urls. v aplikaci.

      :return: Vrací hodnotu podle větve zpracování.

