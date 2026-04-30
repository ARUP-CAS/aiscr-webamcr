PAS views
=========

Definice views.

Třídy
------

.. py:class:: SamostatnyNalezCreateView

   Implementuje komponentu ``SamostatnyNalezCreateView`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``dispatch()``.

   .. py:method:: _set_copy_source()

             Nastaví copy source.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_form_kwargs()

      Vrací form kwargs.

      :return: Vrací proměnná ``kwargs``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Parametr ``form`` se předává do volání ``form_invalid()``, pracuje se s atributy ``save``, ``save_m2m``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``form_invalid()``, výsledek volání ``HttpResponseRedirect()``.

   .. py:method:: form_invalid()

      Zaloguje chyby neplatného formuláře a zobrazí uživateli zprávu.

      :param form: Parametr ``form`` se předává do volání ``info()``, ``form_invalid()``, pracuje se s atributy ``errors``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``form_invalid()``.

   .. py:method:: handle_geometry()

      Zpracuje geometry. v aplikaci.

      :param form_coor: Parametr ``form_coor`` předává se do volání ``float()``, pracuje se s atributy ``data``.

      :return: Vrací n-tici.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``success()``, ``get()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, pracuje se s atributy ``get``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``HttpResponseRedirect()``, výsledek volání ``get()``.


.. py:class:: PasPermissionFilterMixin

   Implementuje komponentu ``PasPermissionFilterMixin`` v rámci aplikace.

   **Metody:**

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
      :param qs: Parametr ``qs`` slouží jako vstup pro logiku funkce ``add_ownership_lookup``.

      :return: Vrací výsledek volání ``Q()``.


.. py:class:: SamostatnyNalezListView

   Třída pohledu pro zobrazení přehledu samostatných nálezu s filtrem v podobe tabulky.

   **Metody:**

   .. py:method:: init_translations()

      Inicializuje překlady pro zobrazení seznamu.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Parametr ``field`` předává se do volání ``get()``, pracuje se s atributy ``replace``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací výsledek volání ``check_filter_permission()``.


.. py:class:: UzivatelSpolupraceListView

   Třída pohledu pro zobrazení přehledu spoluprác s filtrem v podobe tabulky.

   **Metody:**

   .. py:method:: init_translations()

      Inicializuje překlady pro zobrazení seznamu.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Parametr ``field`` předává se do volání ``get()``, pracuje se s atributy ``replace``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací výsledek volání ``order_by()``.

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
      :param qs: Parametr ``qs`` slouží jako vstup pro logiku funkce ``add_ownership_lookup``.

      :return: Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, proměnná ``filtered_my``.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Parametr ``permission`` slouží jako vstup pro logiku funkce ``add_accessibility_lookup``.
      :param qs: Parametr ``qs`` vstupuje do návratové hodnoty.

      :return: Vrací proměnná ``qs``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get_table_kwargs()

      Vrací table kwargs s případným vyloučením sloupce ``smazani`` u neadminů a předáním uživatele.

      :return: Vrací slovník.


.. py:class:: AktivaceEmailView

   Implementuje komponentu ``AktivaceEmailView`` v rámci aplikace.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``set_aktivni()``, pracuje se s atributy ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``redirect()``.


.. py:class:: DeaktivaceSpolupraceView

   Definuje pohled pro deaktivaci spolupráce v modálním dialogu.

   **Metody:**

   .. py:method:: get_object()

      Vrací object. v aplikaci.

      :return: Vrací výsledek volání ``get_object_or_404()``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get_context_data``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``add_message()``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render_to_response()``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``DeaktivovatSpolupraciForm()``, ``set_neaktivni()``, pracuje se s atributy ``POST``, ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``redirect()``.


.. py:class:: EditSpolupraceProjekyView

   Pohled pro editaci projektů přiřazených ke spolupráci v modálním dialogu.

   **Metody:**

   .. py:method:: get_object()

      Vrací objekt spolupráce.

      :return: Vrací výsledek volání ``get_object_or_404()``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get_context_data``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``add_message()``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render_to_response()``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``EditSpolupraceProjekyForm()``, pracuje se s atributy ``POST``, ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``.


.. py:class:: ProjektPasTableView

   Třída pohledu pro zobrazení řádku tabulky samostatných nálezů.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get()``.

      :return: Vrací výsledek volání ``HttpResponse()``.


Funkce
------

.. py:function:: get_detail_context(sn, request)

   Funkce pro získaní potřebného kontextu pro samostatný nález.

   :param sn: Parametr ``sn`` se předává do volání ``CreateSamostatnyNalezForm()``, ``PotvrditNalezForm()``, pracuje se s atributy ``historie``, ``soubory``, ovlivňuje větvení podmínek.
   :param request: Parametr ``request`` se předává do volání ``CreateSamostatnyNalezForm()``, ``get_history_dates()``, pracuje se s atributy ``user``.

   :return: Vrací proměnná ``context``.

.. py:function:: index(request)

   Funkce pohledu pro zobrazení domovské stránky samostatného nálezu s navigačními možnostmi.

   :param request: Parametr ``request`` se předává do volání ``render()``, vstupuje do návratové hodnoty.

   :return: Vrací výsledek volání ``render()``.

.. py:function:: detail(request, ident_cely)

   Funkce pohledu pro zobrazení detailu samostatného nálezu.

   :param request: Parametr ``request`` se předává do volání ``update()``, ``get_detail_context()``, pracuje se s atributy ``session``, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``.

   :return: Vrací výsledek volání ``render()``.

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci samostatného nálezu.

   :param request: Parametr ``request`` se předává do volání ``CreateSamostatnyNalezForm()``, ``CoordinatesDokumentForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``redirect()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
   :raises PermissionDenied: Vyvolá se při splnění podmínky ``sn.stav == SN_ARCHIVOVANY``.

.. py:function:: edit_ulozeni(request, ident_cely)

   Funkce pohledu pro editaci uložení samostatného nálezu pomocí modalu.

   :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ``PotvrditNalezForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: vratit(request, ident_cely)

   Funkce pohledu pro vrácení stavu samostatného nálezu pomocí modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: odeslat(request, ident_cely)

   Funkce pohledu pro odeslání samostatného nálezu pomocí modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: potvrdit(request, ident_cely)

   Funkce pohledu pro potvrzení samostatného nálezu pomocí modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``session``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: archivovat(request, ident_cely)

   Funkce pohledu pro archivaci samostatného nálezu pomocí modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``session``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání samostatného nálezu pomocí modalu.

   :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ``create_transaction()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: zadost(request)

   Funkce pohledu pro vytvoření žádosti o spolupráci.

   :param request: Parametr ``request`` se předává do volání ``CreateZadostForm()``, ``filter()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.

.. py:function:: aktivace(request, pk)

   Funkce pohledu pro aktivaci spolupráce pomocí modalu.

   :param request: Parametr ``request`` se předává do volání ``set_aktivni()``, ``add_message()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param pk: Identifikátor ``pk`` používaný pro dohledání cílového záznamu.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``redirect()``, výsledek volání ``render()``.

.. py:function:: smazat_spolupraci(request, pk)

   Funkce pohledu pro smazání spolupráce pomocí modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``render()``, pracuje se s atributy ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param pk: Identifikátor ``pk`` používaný pro dohledání cílového záznamu.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.

.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní historických datumu.

   :param historie_vazby: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
   :param request_user: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.
   :return: Slovník dat jednotlivých změn stavu pro zobrazení v historii.

.. py:function:: get_detail_template_shows(sn, user)

   Funkce pro získaní kontextu pro zobrazování možností na stránkách.

   :param sn: Parametr ``sn`` se předává do volání ``check_permissions()``, pracuje se s atributy ``stav``, ``ident_cely``.
   :param user: Parametr ``user`` se předává do volání ``check_permissions()``, pracuje se s atributy ``is_archeolog_or_more``.
   :return: Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.

.. py:function:: post_point_position_2_katastre(request)

   Funkce pro získaní názvu katastru z bodu.

   :param request: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

   :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: post_point_position_2_katastre_with_geom(request)

   Funkce pro získaní názvu katastru, geomu z bodu.

   :param request: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

   :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: get_required_fields(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu samostatného nálezu.

   :param zaznam: Parametr ``zaznam`` pracuje se s atributy ``stav``, ovlivňuje větvení podmínek.
   :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
   :return: Seznam názvů polí, která mají být v daném stavu povinná.
