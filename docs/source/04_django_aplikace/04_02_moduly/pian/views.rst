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

      :param qs: Parametr ``qs`` předává se do volání ``filter()``, ``add_ownership_lookup()``, pracuje se s atributy ``annotate``, ``none``, vstupuje do návratové hodnoty.
      :param permission: Parametr ``permission`` předává se do volání ``filter()``, ``add_status_lookup()``, pracuje se s atributy ``base``, ``status``, ovlivňuje větvení podmínek.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``none()``, proměnná ``qs``.

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
      :param qs: Parametr ``qs`` slouží jako vstup pro logiku funkce ``add_ownership_lookup``.

          :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Parametr ``permission`` předává se do volání ``filter()``, ``Q()``, pracuje se s atributy ``accessibility``, vstupuje do návratové hodnoty.
      :param qs: Parametr ``qs`` pracuje se s atributy ``annotate``, ``filter``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``filter()``.


.. py:class:: PianAutocomplete

   Třída pohledu pro autocomplete pianu.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací výsledek volání ``check_filter_permission()``.


.. py:class:: ImportovatPianView

   Třída pohledu pro získaní řádku tabulky s externím zdrojem.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``set()``, ``str()``, pracuje se s atributy ``FILES``, ``user``, ovlivňuje větvení podmínek.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``HttpResponseBadRequest()``, výsledek volání ``render_to_response()``.

   .. py:method:: check_epsg()

      Ověří epsg. v aplikaci.

      :param epsg: Parametr ``epsg`` se předává do volání ``file_validate_epsg()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``file_validate_epsg()``.


Funkce
------

.. py:function:: detail(request, ident_cely)

   Funkce pohledu pro zapsání změny pianu.

   :param request: Parametr ``request`` se předává do volání ``PianCreateForm()``, ``create_transaction()``, pracuje se s atributy ``POST``, ``user``.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``filter()``.

       :return: Vrací proměnná ``response``.
       :raises PermissionDenied: Vyvolá se při splnění podmínky ``pian == PIAN_POTVRZEN``.

.. py:function:: odpojit(request, dj_ident_cely)

   Funkce pohledu pro odpojení pianu pomocí modalu.

   :param request: Parametr ``request`` se předává do volání ``create_transaction()``, ``render()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param dj_ident_cely: Identifikátor ``dj_ident_cely`` používaný pro dohledání cílového záznamu.

       :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``response``, výsledek volání ``render()``.

.. py:function:: potvrdit(request, dj_ident_cely)

   Funkce pohledu pro potvrzení pianu pomocí modalu.

   :param request: Parametr ``request`` se předává do volání ``error()``, ``create_transaction()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param dj_ident_cely: Identifikátor ``dj_ident_cely`` používaný pro dohledání cílového záznamu.

       :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, proměnná ``response``, výsledek volání ``render()``.
       :raises PermissionDenied: Vyvolá se při splnění podmínky ``pian == PIAN_POTVRZEN``.

.. py:function:: create(request, dj_ident_cely)

   Funkce pohledu pro vytvoření pianu.

   :param request: Parametr ``request`` se předává do volání ``PianCreateForm()``, ``add_message()``, pracuje se s atributy ``POST``, ``user``.
   :param dj_ident_cely: Identifikátor ``dj_ident_cely`` používaný pro dohledání cílového záznamu.

       :return: Vrací proměnná ``response``.

.. py:function:: mapa_dj(request, ident_cely)

   Funkce ziskej Dj pro Pian

   :param request: Parametr ``request`` se předává do volání ``get_dj_akce_for_pian()``.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_dj_akce_for_pian()``.

       :return: Vrací výsledek volání ``JsonResponse()``.
