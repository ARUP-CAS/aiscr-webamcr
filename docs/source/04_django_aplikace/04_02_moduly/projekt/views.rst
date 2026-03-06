PROJEKT views
=============

Definice views.

Třídy
------

.. py:class:: ProjectPasFromEnvelopeView

   Trida pohledu pro získaní heatmapy pas.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``loads()``, pracuje se s atributy ``body``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: ProjectPianFromEnvelopeView

   Trida pohledu pro získaní heatmapy pianu.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``loads()``, pracuje se s atributy ``body``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: ProjektPermissionFilterMixin

   Implementuje komponentu ``ProjektPermissionFilterMixin`` v rámci aplikace.

   **Metody:**

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
      :param qs: Parametr ``qs`` slouží jako vstup pro logiku funkce ``add_ownership_lookup``.

      :return: Vrací výsledek volání ``Q()``.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Parametr ``permission`` předává se do volání ``filter()``, ``add_ownership_lookup()``, pracuje se s atributy ``accessibility``, vstupuje do návratové hodnoty.
      :param qs: Parametr ``qs`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``filter()``.


.. py:class:: ProjektListView

   Třida pohledu pro zobrazení listu/tabulky s projektami.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací výsledek volání ``check_filter_permission()``.


.. py:class:: GenerovatOznameniView

   Implementuje komponentu ``GenerovatOznameniView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_redirect_url()

      Vrací redirect url.

      :param args: Parametr ``args`` se předává do volání ``get_redirect_url()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_redirect_url()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``get_redirect_url()``.


.. py:class:: ProjektAutocompleteBezZrusenych

   Třída pohledu získaní projektů pro autocomplete pro připojení do dokumentu.

   **Metody:**

   .. py:method:: get_result_label()

      Vrací result label.

      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``none()``, výsledek volání ``check_filter_permission()``.

   .. py:method:: check_filter_permission()

      Ověří filter permission.

      :param qs: Parametr ``qs`` předává se do volání ``filter_by_permission()``, vstupuje do návratové hodnoty.

      :return: Vrací proměnná ``qs``.


.. py:class:: ProjectTableRowView

   Třída pohledu pro zobrazení řádku tabulky projektů pri připájení.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``get()``, pracuje se s atributy ``GET``.

      :return: Vrací výsledek volání ``HttpResponse()``.


.. py:class:: UpravitDatumOznameniView

   Implementuje komponentu ``UpravitDatumOznameniView`` v rámci aplikace.

   **Metody:**

   .. py:method:: _get_existing_record()

      Vrací existing record.

      :param projekt: Parametr ``projekt`` předává se do volání ``filter()``, pracuje se s atributy ``historie``.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací výsledek volání ``render_to_response()``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``UpravitDatumOznameniForm()``, ``create_transaction()``, pracuje se s atributy ``POST``, ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: ZadostUdajeOznamovatelView

   Třida pohledu pro odeslání žádosti o údaje o oznamovateli.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      :return: Vrací proměnná ``zaznam``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      :return: Vrací výsledek volání ``render_to_response()``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``ZadostProjektForm()``, ``send_ep08()``, pracuje se s atributy ``POST``, ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: ZadostOdhlaseniProjektuView

   Třida pohledu pro odeslání žádosti pro odhlášení projektu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      :return: Vrací proměnná ``zaznam``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      :return: Vrací výsledek volání ``render_to_response()``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``ZadostProjektForm()``, ``send_ep07()``, pracuje se s atributy ``POST``, ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: ZadostZruseniProjektuView

   Třida pohledu pro odeslání žádosti pro zrušení projektu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      :return: Vrací proměnná ``zaznam``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      :return: Vrací výsledek volání ``render_to_response()``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``ZadostProjektForm()``, ``send_ep11()``, pracuje se s atributy ``POST``, ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``JsonResponse()``.


Funkce
------

.. py:function:: index(request)

   Funkce pohledu pro zobrazení indexu s navigací projektu.

   :param request: Parametr ``request`` se předává do volání ``render()``, vstupuje do návratové hodnoty.

   :return: Vrací výsledek volání ``render()``.

.. py:function:: detail(request, ident_cely)

   Funkce pohledu pro zobrazení detailu projektu.

   :param request: Parametr ``request`` se předává do volání ``get_history_dates()``, ``get_detail_template_shows()``, pracuje se s atributy ``session``, ``user``, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``filter()``.

   :return: Vrací výsledek volání ``render()``.

.. py:function:: post_ajax_get_projects_limit(request)

   Funkce pohledu pro získaní heatmapy projektu.

   :param request: Parametr ``request`` se předává do volání ``loads()``, ``get_num_projects_from_envelope()``, pracuje se s atributy ``body``.

   :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: post_ajax_get_project_one(request)

   Funkce pohledu pro získaní geometrie projektu.

   :param request: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

   :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: create(request)

   Funkce pohledu pro vytvoření projektu.

   :param request: Parametr ``request`` se předává do volání ``katastr_text_to_id()``, ``CreateProjektForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``render()``, výsledek volání ``redirect()``.

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci projektu.

   :param request: Parametr ``request`` se předává do volání ``katastr_text_to_id()``, ``EditProjektForm()``, pracuje se s atributy ``user``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``redirect()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání projektu pomoci modalu.

   :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ``create_transaction()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: schvalit(request, ident_cely)

   Funkce pohledu pro schválení projektu pomoci modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``debug()``, ``get_object_or_404()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: prihlasit(request, ident_cely)

   Funkce pohledu pro přihlášení projektu pomoci modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``user``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: zahajit_v_terenu(request, ident_cely)

   Funkce pohledu pro zahájení v terenu projektu pomoci modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``session``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: ukoncit_v_terenu(request, ident_cely)

   Funkce pohledu pro ukončení v terenu projektu pomoci modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: uzavrit(request, ident_cely)

   Funkce pohledu pro uzavření projektu pomoci modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: archivovat(request, ident_cely)

   Funkce pohledu pro archivaci projektu pomoci modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: navrhnout_ke_zruseni(request, ident_cely)

   Funkce pohledu pro navržení projektu ke zrušení pomoci modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: zrusit(request, ident_cely)

   Funkce pohledu pro zrušení projektu pomoci modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: vratit(request, ident_cely)

   Funkce pohledu pro vrácení projektu pomoci modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: vratit_navrh_zruseni(request, ident_cely)

   Funkce pohledu pro vrácení návrhu na zrušení projektu pomoci modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: odpojit_dokument(request, ident_cely, proj_ident_cely)

   Funkce pohledu pro odpojení dokumentu z projektu pomoci modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``filter()``, ``odpojit()``, vstupuje do návratové hodnoty.
   :param proj_ident_cely: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``odpojit()``.

.. py:function:: pripojit_dokument(request, proj_ident_cely)

   Funkce pohledu pro pripojení dokumentu z projektu pomoci modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``pripojit()``, vstupuje do návratové hodnoty.
   :param proj_ident_cely: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``pripojit()``.

.. py:function:: generovat_oznameni(request, ident_cely)

   Funkce pohledu pro generování oznámení projektu pomoci modalu.

   :param request: Parametr ``request`` se předává do volání ``debug()``, ``add_message()``, pracuje se s atributy ``POST``, ``user``, ovlivňuje větvení podmínek.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``debug()``, ``get_object_or_404()``.

   :return: Vrací výsledek volání ``redirect()``.

.. py:function:: generovat_expertni_list(request, ident_cely)

   Funkce pohledu pro generování expertního listu projektu pomoci modalu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, pracuje se s atributy ``POST``.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, proměnná ``response``.

.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní dátumů pro historii.

   :param historie_vazby: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
   :param request_user: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.
   :return: Slovník dat jednotlivých změn stavu pro zobrazení v historii.

.. py:function:: get_detail_template_shows(projekt, user)

   Funkce pro získaní dictionary uživatelských akcí které mají být zobrazeny uživately.

   :param projekt: Parametr ``projekt`` předává se do volání ``get_show_oznamovatel()``, ``check_permissions()``, pracuje se s atributy ``typ_projektu``, ``ident_cely``, ovlivňuje větvení podmínek.
   :param user: Parametr ``user`` se předává do volání ``get_show_oznamovatel()``, ``check_permissions()``, pracuje se s atributy ``organizace``.
   :return: Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.

.. py:function:: get_show_oznamovatel(projekt, user)

   Vrací show oznamovatel.

   :param projekt: Parametr ``projekt`` pracuje se s atributy ``typ_projektu``, ``has_oznamovatel``, ovlivňuje větvení podmínek.
   :param user: Parametr ``user`` pracuje se s atributy ``is_archiver_or_more``, ``hlavni_role``, ovlivňuje větvení podmínek.
   :return: Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.

.. py:function:: get_required_fields(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu projektu.

   :param zaznam: Parametr ``zaznam`` pracuje se s atributy ``stav``, ovlivňuje větvení podmínek.
   :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
   :return: Seznam názvů polí, která mají být v daném stavu povinná.

.. py:function:: katastr_text_to_id(request)

   Funkce podlehu pro získaní ID katastru podle názvu katastru.

   :param request: Parametr ``request`` pracuje se s atributy ``POST``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``copy()``, proměnná ``post``.
