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

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _set_copy_source()

      Nastaví copy source.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_form_kwargs()

      Vrací form kwargs.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: form_invalid()

      Zaloguje chyby neplatného formuláře a zobrazí uživateli zprávu.

   .. py:method:: handle_geometry()

      Zpracuje geometry.

      :param form_coor: Vstupní hodnota ``form_coor`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: PasPermissionFilterMixin

   Implementuje komponentu ``PasPermissionFilterMixin`` v rámci aplikace.

   **Metody:**

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Vstupní hodnota ``ownership`` pro danou operaci.
      :param qs: Vstupní hodnota ``qs`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: SamostatnyNalezListView

   Třída pohledu pro zobrazení přehledu samostatných nálezu s filtrem v podobe tabulky.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

      :return: Vrací výsledek provedené operace.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Vstupní hodnota ``field`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_queryset()

      Vrací queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: UzivatelSpolupraceListView

   Třída pohledu pro zobrazení přehledu spoluprác s filtrem v podobe tabulky.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

      :return: Vrací výsledek provedené operace.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Vstupní hodnota ``field`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_queryset()

      Vrací queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Vstupní hodnota ``ownership`` pro danou operaci.
      :param qs: Vstupní hodnota ``qs`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Vstupní hodnota ``permission`` pro danou operaci.
      :param qs: Vstupní hodnota ``qs`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_table_kwargs()

      Vrací table kwargs.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: AktivaceEmailView

   Implementuje komponentu ``AktivaceEmailView`` v rámci aplikace.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: DeaktivaceSpolupraceView

   Definuje pohled pro deaktivaci spolupráce v modálním dialogu.

   **Metody:**

   .. py:method:: get_object()

      Vrací object.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: ProjektPasTableView

   Třída pohledu pro zobrazení řádku tabulky samostatných nálezů.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.


Funkce
------

.. py:function:: get_detail_context(sn, request)

   Funkce pro získaní potřebného kontextu pro samostatný nález.

.. py:function:: index(request)

   Funkce pohledu pro zobrazení domovské stránky samostatného nálezu s navigačními možnostmi.

.. py:function:: detail(request, ident_cely)

   Funkce pohledu pro zobrazení detailu samostatného nálezu.

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci samostatného nálezu.

.. py:function:: edit_ulozeni(request, ident_cely)

   Funkce pohledu pro editaci uložení samostatného nálezu pomocí modalu.

.. py:function:: vratit(request, ident_cely)

   Funkce pohledu pro vrácení stavu samostatného nálezu pomocí modalu.

.. py:function:: odeslat(request, ident_cely)

   Funkce pohledu pro odeslání samostatného nálezu pomocí modalu.

.. py:function:: potvrdit(request, ident_cely)

   Funkce pohledu pro potvrzení samostatného nálezu pomocí modalu.

.. py:function:: archivovat(request, ident_cely)

   Funkce pohledu pro archivaci samostatného nálezu pomocí modalu.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání samostatného nálezu pomocí modalu.

.. py:function:: zadost(request)

   Funkce pohledu pro vytvoření žádosti o spolupráci.

.. py:function:: aktivace(request, pk)

   Funkce pohledu pro aktivaci spolupráce pomocí modalu.

.. py:function:: smazat_spolupraci(request, pk)

   Funkce pohledu pro smazání spolupráce pomocí modalu.

.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní historických datumu.

.. py:function:: get_detail_template_shows(sn, user)

   Funkce pro získaní kontextu pro zobrazování možností na stránkách.

.. py:function:: post_point_position_2_katastre(request)

   Funkce pro získaní názvu katastru z bodu.

.. py:function:: post_point_position_2_katastre_with_geom(request)

   Funkce pro získaní názvu katastru, geomu z bodu.

.. py:function:: get_required_fields(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu samostatného nálezu.


   **Argumenty:**

   - ``zaznam`` (*PAS*): model samostatního nálezu pro který se dané pole počítají.
   - ``next`` (*int*): pokud je poskytnuto číslo tak se jedná o povinné pole pro příští stav.

   **Návratová hodnota:**

   *required_fields*: list polí.
