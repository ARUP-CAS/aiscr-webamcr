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

      :param qs: Vstupní hodnota ``qs`` pro danou operaci.
      :param permission: Vstupní hodnota ``permission`` pro danou operaci.

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Vstupní hodnota ``ownership`` pro danou operaci.
      :param qs: Vstupní hodnota ``qs`` pro danou operaci.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Vstupní hodnota ``permission`` pro danou operaci.
      :param qs: Vstupní hodnota ``qs`` pro danou operaci.


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

      :param epsg: Vstupní hodnota ``epsg`` pro danou operaci.


Funkce
------

.. py:function:: detail(request, ident_cely)

   Funkce pohledu pro zapsání změny pianu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: odpojit(request, dj_ident_cely)

   Funkce pohledu pro odpojení pianu pomocí modalu.

   :param request: Popis parametru ``request``.
   :param dj_ident_cely: Popis parametru ``dj_ident_cely``.

.. py:function:: potvrdit(request, dj_ident_cely)

   Funkce pohledu pro potvrzení pianu pomocí modalu.

   :param request: Popis parametru ``request``.
   :param dj_ident_cely: Popis parametru ``dj_ident_cely``.

.. py:function:: create(request, dj_ident_cely)

   Funkce pohledu pro vytvoření pianu.

   :param request: Popis parametru ``request``.
   :param dj_ident_cely: Popis parametru ``dj_ident_cely``.

.. py:function:: mapa_dj(request, ident_cely)

   Funkce ziskej Dj pro Pian

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.
