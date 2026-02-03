PAS views
=========

Definice views.

Třídy
------

.. py:class:: SamostatnyNalezCreateView

   Popis není k dispozici.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: dispatch()

   .. py:method:: _set_copy_source()

   .. py:method:: get_form_kwargs()

   .. py:method:: get_context_data()

   .. py:method:: form_valid()

   .. py:method:: form_invalid()

      Log form invalid errors and display a message to the user.

   .. py:method:: handle_geometry()

      Handle coordinate data parsing and return geometry objects.

   .. py:method:: get()

      Handle GET request and check project type.


.. py:class:: PasPermissionFilterMixin

   Popis není k dispozici.

   **Metody:**

   .. py:method:: add_ownership_lookup()


.. py:class:: SamostatnyNalezListView

   Třída pohledu pro zobrazení přehledu samostatných nálezu s filtrem v podobe tabulky.

   **Metody:**

   .. py:method:: init_translations()

   .. py:method:: rename_field_for_ordering()

   .. py:method:: get_queryset()


.. py:class:: UzivatelSpolupraceListView

   Třída pohledu pro zobrazení přehledu spoluprác s filtrem v podobe tabulky.

   **Metody:**

   .. py:method:: init_translations()

   .. py:method:: rename_field_for_ordering()

   .. py:method:: get_queryset()

   .. py:method:: add_ownership_lookup()

   .. py:method:: add_accessibility_lookup()

   .. py:method:: get_context_data()

   .. py:method:: get_table_kwargs()


.. py:class:: AktivaceEmailView

   Popis není k dispozici.

   **Metody:**

   .. py:method:: post()


.. py:class:: DeaktivaceSpolupraceView

   class pohledu pro deaktivaci spolupráce pomocí modalu.

   **Metody:**

   .. py:method:: get_object()

   .. py:method:: get_context_data()

   .. py:method:: get()

   .. py:method:: post()


.. py:class:: ProjektPasTableView

   Třída pohledu pro zobrazení řádku tabulky samostatných nálezů.

   **Metody:**

   .. py:method:: get()


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
