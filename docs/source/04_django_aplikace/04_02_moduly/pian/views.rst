PIAN views
==========

Definice views.

Třídy
------

.. py:class:: PianPermissionFilterMixin

   Implementuje komponentu ``PianPermissionFilterMixin`` v rámci aplikace.

   **Metody:**

   .. py:method:: filter_by_permission()

      Filtruje by permission.

      :param qs: Vstupní queryset, který má být dále zpracován.
      :param permission: Typová nebo konfigurační hodnota `permission` určující cílovou logiku.

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
      :param qs: Vstupní queryset, který má být dále zpracován.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Typová nebo konfigurační hodnota `permission` určující cílovou logiku.
      :param qs: Vstupní queryset, který má být dále zpracován.


.. py:class:: PianAutocomplete

   Třída pohledu pro autocomplete pianu.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


.. py:class:: ImportovatPianView

   Třída pohledu pro získaní řádku tabulky s externím zdrojem.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.

   .. py:method:: check_epsg()

      Ověří epsg. v aplikaci.

      :param epsg: Číselná nebo geometrická hodnota `epsg` použitá při výpočtu nebo transformaci.


Funkce
------

.. py:function:: detail(request, ident_cely)

   Funkce pohledu pro zapsání změny pianu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: odpojit(request, dj_ident_cely)

   Funkce pohledu pro odpojení pianu pomocí modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param dj_ident_cely: Identifikátor ``dj_ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: potvrdit(request, dj_ident_cely)

   Funkce pohledu pro potvrzení pianu pomocí modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param dj_ident_cely: Identifikátor ``dj_ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: create(request, dj_ident_cely)

   Funkce pohledu pro vytvoření pianu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param dj_ident_cely: Identifikátor ``dj_ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: mapa_dj(request, ident_cely)

   Funkce ziskej Dj pro Pian

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
