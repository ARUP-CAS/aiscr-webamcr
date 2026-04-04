DOKUMENT views
==============

Definice views.

Třídy
------

.. py:class:: Model3DListView

   Třida pohledu pro zobrazení listu/tabulky s modelama 3D.

   **Metody:**

   .. py:method:: init_translations()

      Inicializuje přeložené texty pro seznam dokumentů.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Parametr ``field`` předává se do volání ``get()``, pracuje se s atributy ``replace``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací výsledek volání ``check_filter_permission()``.


.. py:class:: DokumentIndexView

   Třida pohledu pro zobrazení domovské stránky dokumentů s navigačními možnostmi.


.. py:class:: DokumentListView

   Třida pohledu pro zobrazení listu/tabulky s dokumentama.

   **Metody:**

   .. py:method:: init_translations()

      Inicializuje přeložené texty pro seznam dokumentů.

   .. py:method:: get_context_data()

      Vytvoří kontext pro renderování šablony.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: kontext šablony

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Parametr ``field`` předává se do volání ``get()``, pracuje se s atributy ``replace``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací výsledek volání ``check_filter_permission()``.


.. py:class:: RelatedContext

   Třida, která se dedí a která obsahuje metody pro získaní relací dokumentů.

   **Metody:**

   .. py:method:: get_cast()

      Metoda pro získaní informací o součásti dokumentu.

      :param context: Slovník kontextu pro aktualizaci.
      :param cast: Součást dokumentu k zobrazení.
      :param kwargs: Dodatečné pojmenované argumenty.

   .. py:method:: get_context_data()

      Metoda pro získaní contextu dokumentu pro template.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: render_to_response()

      Metoda pro render response, kvúli správnemu zobrazení zpět možnosti.

      :param context: Parametr ``context`` se předává do volání ``render_to_response()``, ovlivňuje větvení podmínek.
      :param response_kwargs: Dodatečné argumenty předané voláním.

      :return: Vrací proměnná ``response``.


.. py:class:: DokumentDetailView

   Třida pohledu pro zobrazení detailu dokumentu.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``get()``.


.. py:class:: DokumentCastDetailView

   Třida pohledu pro zobrazení detailu části dokumentu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.


.. py:class:: DokumentCastEditView

   Třida pohledu pro editaci části dokumentu pomocí modalu.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get_success_url()

      Vrací success url.

      :return: Vrací výsledek volání ``get_absolute_url()``.

   .. py:method:: get_object()

      Vrací object. v aplikaci.

      :param queryset: Parametr ``queryset`` předává se do volání ``get_object()``.

      :return: Vrací atribut objektu.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``create_transaction()``, ``post()``, pracuje se s atributy ``user``.
      :param args: Parametr ``args`` se předává do volání ``post()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``post()``.

      :return: Vrací výsledek volání ``JsonResponse()``.

   .. py:method:: form_invalid()

      Provádí operaci form invalid.

      :param form: Parametr ``form`` se předává do volání ``debug()``, ``form_invalid()``, pracuje se s atributy ``errors``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``form_invalid()``.


.. py:class:: KomponentaDokumentDetailView

   Třida pohledu pro zobrazení detailu komponenty části dokumentu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.


.. py:class:: KomponentaDokumentCreateView

   Třida pohledu pro vytvoření komponenty části dokumentu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``get()``.


.. py:class:: TvarEditView

   Třida pohledu pro uložení zmeny tvaru z formuláře.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``TvarFormset()``, ``add_message()``, pracuje se s atributy ``POST``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``redirect()``.


.. py:class:: TvarSmazatView

   Třida pohledu pro smazání tvaru dokumentu pomocí modalu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``add_message()``, ``dispatch()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      :return: Vrací výsledek volání ``get_object_or_404()``.

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

      :param request: Parametr ``request`` předává se do volání ``create_transaction()``, pracuje se s atributy ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: VytvoritCastView

   Třida pohledu pro vytvoření části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

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

      :param request: Parametr ``request`` předává se do volání ``DokumentCastCreateForm()``, ``add_message()``, pracuje se s atributy ``POST``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: TransakceView

   Třida pohledu pro změnu stavu a práci s dokumentama cez modal, která se dedí pro jednotlivá změny.

   **Metody:**

   .. py:method:: init_translations()

      Inicializuje přeložené texty pro seznam dokumentů.

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: get_context_data()

      Vytvoří kontext pro renderování šablony

      :param kwargs: Dodatečné položky kontextu předané z rodičovské metody.
      :return: kontext šablony.

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``add_message()``, ``check_stav_changed()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``dispatch()``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací výsledek volání ``render_to_response()``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``add_message()``, pracuje se s atributy ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: DokumentCastPripojitAkciView

   Třida pohledu pro připojení akce do části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: init_translations()

      Inicializuje přeložené texty pro seznam dokumentů.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``PripojitArchZaznamForm()``, pracuje se s atributy ``POST``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: DokumentCastPripojitProjektView

   Třida pohledu pro připojení projektu do části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: init_translations()

      Inicializuje přeložené texty pro seznam dokumentů.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``PripojitProjektForm()``, pracuje se s atributy ``POST``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: DokumentCastOdpojitView

   Třida pohledu pro odpojení části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: init_translations()

      Inicializuje přeložené texty pro seznam dokumentů.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``create_transaction()``, pracuje se s atributy ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: DokumentCastSmazatView

   Třida pohledu pro smazání části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: init_translations()

      Inicializuje přeložené texty pro seznam dokumentů.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``create_transaction()``, pracuje se s atributy ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: DokumentNeidentAkceSmazatView

   Třida pohledu pro smazání neident akce z části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: init_translations()

      Inicializuje přeložené texty pro seznam dokumentů.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``add_message()``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: DokumentAutocomplete

   Třída pohledu pro autocomplete dokumentů.

   **Metody:**

   .. py:method:: get_result_label()

      Vrací result label.

      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``none()``, výsledek volání ``check_filter_permission()``.


.. py:class:: DokumentyAzTableView

   Třída pohledu pro zobrazení tabulky dokumentů.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``check_permissions()``, pracuje se s atributy ``user``.
      :param typ_vazby: Parametr ``typ_vazby`` ovlivňuje větvení podmínek.
      :param ident_cely: Parametr ``ident_cely`` se předává do volání ``filter()``, ``get()``.

      :return: Vrací výsledek volání ``HttpResponse()``.


Funkce
------

.. py:function:: index_model_3D(request)

   Funkce pohledu pro zobrazení domovské stránky modelu 3D s navigačními možnostmi.

   :param request: Parametr ``request`` se předává do volání ``render()``, vstupuje do návratové hodnoty.

   :return: Vrací výsledek volání ``render()``.

.. py:function:: detail_model_3D(request, ident_cely)

   Třida pohledu pro zobrazení detailu modelu 3D.

   :param request: Parametr ``request`` se předává do volání ``get_detail_template_shows()``, ``get_history_dates()``, pracuje se s atributy ``session``, ``user``, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``.

   :return: Vrací výsledek volání ``render()``.
   :raises UnexpectedDataRelations: Vyvolá se při splnění podmínky ``casti.count() != 1``; nebo při splnění podmínky ``komponenty.count() != 1``.

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci dokumentu.

   :param request: Parametr ``request`` se předává do volání ``create_transaction()``, ``EditDokumentForm()``, pracuje se s atributy ``user``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
   :raises PermissionDenied: Vyvolá se při splnění podmínky ``dokument.stav == D_STAV_ARCHIVOVANY``.

.. py:function:: edit_model_3D(request, ident_cely)

   Funkce pohledu pro editaci modelu 3D.

   :param request: Parametr ``request`` se předává do volání ``CreateModelDokumentForm()``, ``CreateModelExtraDataForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
   :raises PermissionDenied: Vyvolá se při splnění podmínky ``dokument.stav == D_STAV_ARCHIVOVANY``.

.. py:function:: zapsat_do_akce(request, arch_z_ident_cely)

   Funkce pohledu pro zapsání dokumentu do akce.

   :param request: Parametr ``request`` se předává do volání ``zapsat()``, vstupuje do návratové hodnoty.
   :param arch_z_ident_cely: Identifikátor ``arch_z_ident_cely`` používaný pro dohledání cílového záznamu.

   :return: Vrací výsledek volání ``zapsat()``.

.. py:function:: zapsat_do_projektu(request, proj_ident_cely)

   Funkce pohledu pro zapsání dokumentu do projektu.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``zapsat()``, vstupuje do návratové hodnoty.
   :param proj_ident_cely: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``zapsat()``.

.. py:function:: create_model_3D(request)

   Funkce pohledu pro vytvoření modelu 3D.

   :param request: Parametr ``request`` se předává do volání ``CreateModelDokumentForm()``, ``CreateModelExtraDataForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.

.. py:function:: odeslat(request, ident_cely)

   Funkce pohledu pro odeslání dokumentu cez modal.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``debug()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, proměnná ``returned_value``, výsledek volání ``render()``.

.. py:function:: archivovat(request, ident_cely)

   Funkce pohledu pro archivaci dokumentu cez modal.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``debug()``, pracuje se s atributy ``startswith``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: vratit(request, ident_cely)

   Funkce pohledu pro vrácení dokumentu cez modal.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání dokumentu cez modal.

   :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ``create_transaction()``, pracuje se s atributy ``user``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
   :raises ValueError: Vyvolá se s textem "dokument.views.smazat.deleted".

.. py:function:: get_hierarchie_dokument_typ()

   Funkce pro získaní hierarchie pro heslař.

   :return: Vrací proměnná ``hierarchie``.

.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní historických datumu.

   :param historie_vazby: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
   :param request_user: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.
   :return: Slovník dat jednotlivých změn stavu pro zobrazení v historii.

.. py:function:: get_detail_template_shows(dokument, user)

   Funkce pro získaní kontextu pro zobrazování možností na stránkách.

   :param dokument: Parametr ``dokument`` předává se do volání ``check_permissions()``, pracuje se s atributy ``ident_cely``, ``stav``, ovlivňuje větvení podmínek.
   :param user: Parametr ``user`` se předává do volání ``check_permissions()``.
   :return: Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.

.. py:function:: zapsat(request, zaznam)

   Funkce pohledu pro zapsání dokumentu.

   :param request: Parametr ``request`` se předává do volání ``EditDokumentForm()``, ``create_transaction()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param zaznam: Parametr ``zaznam`` předává se do volání ``isinstance()``, ``DokumentCast()``, pracuje se s atributy ``ident_cely``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.

.. py:function:: odpojit(request, ident_doku, ident_zaznamu, zaznam)

   Funkce pohledu pro odpojení dokumentu cez modal.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``FedoraTransaction()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_doku: Identifikátor ``ident_doku`` používaný pro dohledání cílového záznamu.
   :param ident_zaznamu: Identifikátor ``ident_zaznamu`` používaný pro dohledání cílového záznamu.
   :param zaznam: Parametr ``zaznam`` předává se do volání ``JsonResponse()``, ``isinstance()``, pracuje se s atributy ``get_absolute_url``, ``typ_zaznamu``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: pripojit(request, ident_zaznam, proj_ident_cely, typ)

   Funkce pohledu pro pripojení dokumentu cez modal.

   :param request: Parametr ``request`` se předává do volání ``create_transaction()``, ``add_message()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_zaznam: Identifikátor ``ident_zaznam`` používaný pro dohledání cílového záznamu.
   :param proj_ident_cely: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.
   :param typ: Parametr ``typ`` předává se do volání ``get_object_or_404()``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: get_dokument_table_row(request)

   Funkce pohledu pro získaní řádku dokumentu pro vykreslení v modalu.

   :param request: Parametr ``request`` se předává do volání ``get()``, pracuje se s atributy ``GET``.

   :return: Vrací výsledek volání ``HttpResponse()``.

.. py:function:: get_dokument_table_row_vratit(request)

   AJAX pohled pro načtení jednoho řádku dokumentu do tabulky pro "vrácení dokumentu".

   :param request: Parametr ``request`` pracuje se s atributy ``GET``.

   :return: Vrací výsledek volání ``HttpResponse()``.
   :raises Http404: Vyvolá se s textem "Dokument neexistuje.".

.. py:function:: get_detail_view(ident_cely)

   Funkce pohledu pro redirect podle identu na model 3D nebo dokument detail.

   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``redirect()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

   :return: Vrací výsledek volání ``redirect()``.

.. py:function:: get_detail_json_view(ident_cely)

   Funkce pohledu pro vrácení url pro redirect podle identu na model 3D nebo dokument detail.

   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``reverse()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

   :return: Vrací výsledek volání ``reverse()``.

.. py:function:: get_required_fields_model3D(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu modelu 3D.

   :param zaznam: Parametr ``zaznam`` pracuje se s atributy ``stav``, ovlivňuje větvení podmínek.
   :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
   :return: Seznam názvů polí, která mají být v daném stavu povinná.

.. py:function:: get_required_fields_dokument(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu dokumentu.

   :param zaznam: Parametr ``zaznam`` pracuje se s atributy ``stav``, ovlivňuje větvení podmínek.
   :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
   :return: Seznam názvů polí, která mají být v daném stavu povinná.

.. py:function:: get_komponenta_form_detail(komponenta, show, old_nalez_post, komp_ident_cely, session)

   Funkce pro získaní formsetu predmetu a objektu pro komponentu.

   :param komponenta: Komponenta, se kterou funkce pracuje.
   :param show: Parametr ``show`` se předává do volání ``inlineformset_factory()``, ``create_nalez_objekt_form()``.
   :param old_nalez_post: Parametr ``old_nalez_post`` se předává do volání ``NalezObjektFormset()``, ``NalezPredmetFormset()``.
   :param komp_ident_cely: Identifikátor ``komp_ident_cely`` používaný pro dohledání cílového záznamu.
   :param session: Volitelná Django session pro načtení dat souběžné editace.

   :return: Vrací proměnná ``komponenta_form_detail``.

.. py:function:: get_obdobi_choices()

   Funkce která vrací dvou stupňový heslař pro období.

   :return: Vrací výsledek volání ``heslar_12()``.

.. py:function:: get_areal_choices()

   Funkce která vrací dvou stupňový heslař pro areál.

   :return: Vrací výsledek volání ``heslar_12()``.

.. py:function:: post_ajax_get_3d_limit(request)

   Funkce pohledu pro získaní 3D.

   :param request: Parametr ``request`` se předává do volání ``loads()``, ``get_3d_from_envelope()``, pracuje se s atributy ``body``.

   :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: zjisti_licenci_organizace(request)

   Funkce pohledu pro zjištení licence organizace.

   :param request: Parametr ``request`` pracuje se s atributy ``GET``.

   :return: Vrací výsledek volání ``JsonResponse()``.
