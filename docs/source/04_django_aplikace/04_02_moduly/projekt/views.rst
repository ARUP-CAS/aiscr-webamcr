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

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``loads()``, pracuje se s atributy ``body``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: ProjectPianFromEnvelopeView

   Trida pohledu pro získaní heatmapy pianu.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``loads()``, pracuje se s atributy ``body``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: ProjektPermissionFilterMixin

   Implementuje komponentu ``ProjektPermissionFilterMixin`` v rámci aplikace.

   **Metody:**

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      **Parametry:**

      - ``ownership``: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
      - ``qs``: Parametr ``qs`` slouží jako vstup pro logiku funkce ``add_ownership_lookup``.

      **Návratová hodnota:**

      Vrací výsledek volání ``Q()``.


   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      **Parametry:**

      - ``permission``: Parametr ``permission`` předává se do volání ``filter()``, ``add_ownership_lookup()``, pracuje se s atributy ``accessibility``, vstupuje do návratové hodnoty.
      - ``qs``: Parametr ``qs`` pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``filter()``.



.. py:class:: ProjektListView

   Třida pohledu pro zobrazení listu/tabulky s projektami.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: get_table_kwargs()

      Předá aktuálního uživatele konstruktoru tabulky.

      ``ProjektTable`` potřebuje uživatele pro metodu ``render_oznamovatel_oznamovatel``,
      která aplikuje pravidla viditelnosti oznamovatele per-řádek.

      **Návratová hodnota:**

      Slovník kwargs předávaných konstruktoru tabulky.


   .. py:method:: postprocess_export_dataframe()

      Aplikuje oprávnění na sloupec ``oznamovatel_oznamovatel`` v exportním DataFrame.

      Pro archivující uživatele vrací DataFrame beze změny.
      Pro archeology a ostatní role je DB dotazem sestaven set identifikátorů projektů,
      u nichž má aktuální uživatel právo vidět oznamovatele (dle pravidel ``get_show_oznamovatel``).
      Hodnota oznamovatele je v nepřístupných řádcích nahrazena prázdným řetězcem.

      Časová kritéria jsou vyhodnocována přímo z polí ``datum_uzavreni`` a ``datum_prihlaseni``
      na modelu ``Projekt``. DB provede filtrování viditelnosti a vrátí pouze relevantní
      identifikátory; Python-level smyčka přes všechny projekty je vyloučena.

      **Parametry:**

      - ``df``: DataFrame sestavený z Redis snapshotů se strojovými názvy sloupců.

      **Návratová hodnota:**

      Upravený DataFrame s aplikovanými pravidly viditelnosti oznamovatele.


   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      **Návratová hodnota:**

      Vrací výsledek volání ``check_filter_permission()``.



.. py:class:: GenerovatOznameniView

   Implementuje komponentu ``GenerovatOznameniView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_redirect_url()

      Vrací redirect url.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``get_redirect_url()``, vstupuje do návratové hodnoty.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_redirect_url()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``get_redirect_url()``.



.. py:class:: ProjektAutocompleteBezZrusenych

   Třída pohledu získaní projektů pro autocomplete pro připojení do dokumentu.

   **Metody:**

   .. py:method:: get_result_label()

      Vrací result label.

      **Parametry:**

      - ``result``: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování.


   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``none()``, výsledek volání ``check_filter_permission()``.


   .. py:method:: check_filter_permission()

      Ověří filter permission.

      **Parametry:**

      - ``qs``: Parametr ``qs`` předává se do volání ``filter_by_permission()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací proměnná ``qs``.



.. py:class:: ProjectTableRowView

   Třída pohledu pro zobrazení řádku tabulky projektů pri připájení.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get()``, pracuje se s atributy ``GET``.

      **Návratová hodnota:**

      Vrací výsledek volání ``HttpResponse()``.



.. py:class:: UpravitDatumOznameniView

   Implementuje komponentu ``UpravitDatumOznameniView`` v rámci aplikace.

   **Metody:**

   .. py:method:: _get_existing_record()

      Vrací existing record.

      **Parametry:**

      - ``projekt``: Parametr ``projekt`` předává se do volání ``filter()``, pracuje se s atributy ``historie``.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací výsledek volání ``render_to_response()``.


   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``UpravitDatumOznameniForm()``, ``create_transaction()``, pracuje se s atributy ``POST``, ``user``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: ZadostUdajeOznamovatelView

   Třida pohledu pro odeslání žádosti o údaje o oznamovateli.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      **Návratová hodnota:**

      Vrací proměnná ``zaznam``.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      **Návratová hodnota:**

      Vrací výsledek volání ``render_to_response()``.


   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``ZadostProjektForm()``, ``send_ep08()``, pracuje se s atributy ``POST``, ``user``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: ZadostOdhlaseniProjektuView

   Třida pohledu pro odeslání žádosti pro odhlášení projektu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      **Návratová hodnota:**

      Vrací proměnná ``zaznam``.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      **Návratová hodnota:**

      Vrací výsledek volání ``render_to_response()``.


   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``ZadostProjektForm()``, ``send_ep07()``, pracuje se s atributy ``POST``, ``user``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: ZadostZruseniProjektuView

   Třida pohledu pro odeslání žádosti pro zrušení projektu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      **Návratová hodnota:**

      Vrací proměnná ``zaznam``.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      **Návratová hodnota:**

      Vrací výsledek volání ``render_to_response()``.


   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``ZadostProjektForm()``, ``send_ep11()``, pracuje se s atributy ``POST``, ``user``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



Funkce
------

.. py:function:: index(request)

   Funkce pohledu pro zobrazení indexu s navigací projektu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``render()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací výsledek volání ``render()``.


.. py:function:: detail(request, ident_cely)

   Funkce pohledu pro zobrazení detailu projektu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``get_history_dates()``, ``get_detail_template_shows()``, pracuje se s atributy ``session``, ``user``, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``filter()``.

   **Návratová hodnota:**

   Vrací výsledek volání ``render()``.


.. py:function:: post_ajax_get_projects_limit(request)

   Funkce pohledu pro získaní heatmapy projektu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``loads()``, ``get_num_projects_from_envelope()``, pracuje se s atributy ``body``.

   **Návratová hodnota:**

   Vrací výsledek volání ``JsonResponse()``.


.. py:function:: post_ajax_get_project_one(request)

   Funkce pohledu pro získaní geometrie projektu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

   **Návratová hodnota:**

   Vrací výsledek volání ``JsonResponse()``.


.. py:function:: create(request)

   Funkce pohledu pro vytvoření projektu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``katastr_text_to_id()``, ``CreateProjektForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``render()``, výsledek volání ``redirect()``.


.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci projektu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``katastr_text_to_id()``, ``EditProjektForm()``, pracuje se s atributy ``user``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``redirect()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.


.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání projektu pomoci modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``check_stav_changed()``, ``create_transaction()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: schvalit(request, ident_cely)

   Funkce pohledu pro schválení projektu pomoci modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``debug()``, ``get_object_or_404()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: prihlasit(request, ident_cely)

   Funkce pohledu pro přihlášení projektu pomoci modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``user``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: zahajit_v_terenu(request, ident_cely)

   Funkce pohledu pro zahájení v terenu projektu pomoci modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``session``, ``method``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: ukoncit_v_terenu(request, ident_cely)

   Funkce pohledu pro ukončení v terenu projektu pomoci modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: uzavrit(request, ident_cely)

   Funkce pohledu pro uzavření projektu pomoci modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: archivovat(request, ident_cely)

   Funkce pohledu pro archivaci projektu pomoci modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: navrhnout_ke_zruseni(request, ident_cely)

   Funkce pohledu pro navržení projektu ke zrušení pomoci modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: zrusit(request, ident_cely)

   Funkce pohledu pro zrušení projektu pomoci modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: vratit(request, ident_cely)

   Funkce pohledu pro vrácení projektu pomoci modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: vratit_navrh_zruseni(request, ident_cely)

   Funkce pohledu pro vrácení návrhu na zrušení projektu pomoci modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``JsonResponse()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: odpojit_dokument(request, ident_cely, proj_ident_cely)

   Funkce pohledu pro odpojení dokumentu z projektu pomoci modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``filter()``, ``odpojit()``, vstupuje do návratové hodnoty.
   - ``proj_ident_cely``: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``odpojit()``.


.. py:function:: pripojit_dokument(request, proj_ident_cely)

   Funkce pohledu pro pripojení dokumentu z projektu pomoci modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``pripojit()``, vstupuje do návratové hodnoty.
   - ``proj_ident_cely``: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``pripojit()``.


.. py:function:: generovat_oznameni(request, ident_cely)

   Funkce pohledu pro generování oznámení projektu pomoci modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``debug()``, ``add_message()``, pracuje se s atributy ``POST``, ``user``, ovlivňuje větvení podmínek.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``debug()``, ``get_object_or_404()``.

   **Návratová hodnota:**

   Vrací výsledek volání ``redirect()``.


.. py:function:: generovat_expertni_list(request, ident_cely)

   Funkce pohledu pro generování expertního listu projektu pomoci modalu.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, pracuje se s atributy ``POST``.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, proměnná ``response``.


.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní dátumů pro historii.

   **Parametry:**

   - ``historie_vazby``: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
   - ``request_user``: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.

   **Návratová hodnota:**

   Slovník dat jednotlivých změn stavu pro zobrazení v historii.


.. py:function:: get_detail_template_shows(projekt, user)

   Funkce pro získaní dictionary uživatelských akcí které mají být zobrazeny uživately.

   **Parametry:**

   - ``projekt``: Parametr ``projekt`` předává se do volání ``get_show_oznamovatel()``, ``check_permissions()``, pracuje se s atributy ``typ_projektu``, ``ident_cely``, ovlivňuje větvení podmínek.
   - ``user``: Parametr ``user`` se předává do volání ``get_show_oznamovatel()``, ``check_permissions()``, pracuje se s atributy ``organizace``.

   **Návratová hodnota:**

   Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.


.. py:function:: get_required_fields(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu projektu.

   **Parametry:**

   - ``zaznam``: Parametr ``zaznam`` pracuje se s atributy ``stav``, ovlivňuje větvení podmínek.
   - ``next``: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).

   **Návratová hodnota:**

   Seznam názvů polí, která mají být v daném stavu povinná.


.. py:function:: katastr_text_to_id(request)

   Funkce podlehu pro získaní ID katastru podle názvu katastru.

   **Parametry:**

   - ``request``: Parametr ``request`` pracuje se s atributy ``POST``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``copy()``, proměnná ``post``.

