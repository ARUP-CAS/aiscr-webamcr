PIAN views
==========

Definice views.

Třídy
------

.. py:class:: PianPermissionFilterMixin

   Popis není k dispozici.

   **Metody:**

   .. py:method:: filter_by_permission()

   .. py:method:: add_ownership_lookup()

   .. py:method:: add_accessibility_lookup()


.. py:class:: PianAutocomplete

   Třída pohledu pro autocomplete pianu.

   **Metody:**

   .. py:method:: get_queryset()


.. py:class:: ImportovatPianView

   Třída pohledu pro získaní řádku tabulky s externím zdrojem.

   **Metody:**

   .. py:method:: post()

   .. py:method:: check_epsg()


Funkce
------

.. py:function:: detail(request, ident_cely)

   Funkce pohledu pro zapsání změny pianu.

.. py:function:: odpojit(request, dj_ident_cely)

   Funkce pohledu pro odpojení pianu pomocí modalu.

.. py:function:: potvrdit(request, dj_ident_cely)

   Funkce pohledu pro potvrzení pianu pomocí modalu.

.. py:function:: create(request, dj_ident_cely)

   Funkce pohledu pro vytvoření pianu.

.. py:function:: mapa_dj(request, ident_cely)

   Funkce ziskej Dj pro Pian
