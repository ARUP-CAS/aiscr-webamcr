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

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: _set_copy_source()

      Nastaví copy source.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_form_kwargs()

      Vrací form kwargs.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Formulářová instance zpracovávaná funkcí.

   .. py:method:: form_invalid()

      Zaloguje chyby neplatného formuláře a zobrazí uživateli zprávu.

      :param form: Formulářová instance zpracovávaná funkcí.

   .. py:method:: handle_geometry()

      Zpracuje geometry. v aplikaci.

      :param form_coor: Záznam/objekt ``form_coor``, který funkce čte, validuje nebo upravuje.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: PasPermissionFilterMixin

   Implementuje komponentu ``PasPermissionFilterMixin`` v rámci aplikace.

   **Metody:**

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
      :param qs: Vstupní queryset, který má být dále zpracován.


.. py:class:: SamostatnyNalezListView

   Třída pohledu pro zobrazení přehledu samostatných nálezu s filtrem v podobe tabulky.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Záznam/objekt ``field``, který funkce čte, validuje nebo upravuje.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


.. py:class:: UzivatelSpolupraceListView

   Třída pohledu pro zobrazení přehledu spoluprác s filtrem v podobe tabulky.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Záznam/objekt ``field``, který funkce čte, validuje nebo upravuje.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
      :param qs: Vstupní queryset, který má být dále zpracován.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Typová nebo konfigurační hodnota `permission` určující cílovou logiku.
      :param qs: Vstupní queryset, který má být dále zpracován.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_table_kwargs()

      Vrací table kwargs.


.. py:class:: AktivaceEmailView

   Implementuje komponentu ``AktivaceEmailView`` v rámci aplikace.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DeaktivaceSpolupraceView

   Definuje pohled pro deaktivaci spolupráce v modálním dialogu.

   **Metody:**

   .. py:method:: get_object()

      Vrací object. v aplikaci.

   .. py:method:: get_context_data()

      Vrací context data.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ProjektPasTableView

   Třída pohledu pro zobrazení řádku tabulky samostatných nálezů.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.


Funkce
------

.. py:function:: get_detail_context(sn, request)

   Funkce pro získaní potřebného kontextu pro samostatný nález.

   :param sn: Číselná nebo geometrická hodnota `sn` použitá při výpočtu nebo transformaci.
   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: index(request)

   Funkce pohledu pro zobrazení domovské stránky samostatného nálezu s navigačními možnostmi.

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: detail(request, ident_cely)

   Funkce pohledu pro zobrazení detailu samostatného nálezu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci samostatného nálezu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: edit_ulozeni(request, ident_cely)

   Funkce pohledu pro editaci uložení samostatného nálezu pomocí modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: vratit(request, ident_cely)

   Funkce pohledu pro vrácení stavu samostatného nálezu pomocí modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: odeslat(request, ident_cely)

   Funkce pohledu pro odeslání samostatného nálezu pomocí modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: potvrdit(request, ident_cely)

   Funkce pohledu pro potvrzení samostatného nálezu pomocí modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: archivovat(request, ident_cely)

   Funkce pohledu pro archivaci samostatného nálezu pomocí modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání samostatného nálezu pomocí modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: zadost(request)

   Funkce pohledu pro vytvoření žádosti o spolupráci.

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: aktivace(request, pk)

   Funkce pohledu pro aktivaci spolupráce pomocí modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param pk: Identifikátor ``pk`` používaný pro dohledání cílového záznamu.

.. py:function:: smazat_spolupraci(request, pk)

   Funkce pohledu pro smazání spolupráce pomocí modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param pk: Identifikátor ``pk`` používaný pro dohledání cílového záznamu.

.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní historických datumu.

   :param historie_vazby: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
   :param request_user: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.
   :return: Slovník dat jednotlivých změn stavu pro zobrazení v historii.

.. py:function:: get_detail_template_shows(sn, user)

   Funkce pro získaní kontextu pro zobrazování možností na stránkách.

   :param sn: Číselná nebo geometrická hodnota `sn` použitá při výpočtu nebo transformaci.
   :param user: Uživatel, v jehož kontextu se operace provádí.
   :return: Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.

.. py:function:: post_point_position_2_katastre(request)

   Funkce pro získaní názvu katastru z bodu.

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: post_point_position_2_katastre_with_geom(request)

   Funkce pro získaní názvu katastru, geomu z bodu.

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: get_required_fields(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu samostatného nálezu.

   :param zaznam: Záznam/objekt ``zaznam``, který funkce čte, validuje nebo upravuje.
   :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
   :return: Seznam názvů polí, která mají být v daném stavu povinná.
