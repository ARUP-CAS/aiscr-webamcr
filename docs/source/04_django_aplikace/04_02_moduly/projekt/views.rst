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

      :param request: Django HTTP požadavek použitý při zpracování.


.. py:class:: ProjectPianFromEnvelopeView

   @jiri-bartos presunuto z post_ajax_get_project_pas_limit

   Trida pohledu pro získaní heatmapy pianu.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.


.. py:class:: ProjektPermissionFilterMixin

   Implementuje komponentu ``ProjektPermissionFilterMixin`` v rámci aplikace.

   **Metody:**

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Vstupní hodnota ``ownership`` pro danou operaci.
      :param qs: Vstupní hodnota ``qs`` pro danou operaci.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Vstupní hodnota ``permission`` pro danou operaci.
      :param qs: Vstupní hodnota ``qs`` pro danou operaci.


.. py:class:: ProjektListView

   Třida pohledu pro zobrazení listu/tabulky s projektami.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


.. py:class:: GenerovatOznameniView

   Implementuje komponentu ``GenerovatOznameniView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_redirect_url()

      Vrací redirect url.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ProjektAutocompleteBezZrusenych

   Třída pohledu získaní projektů pro autocomplete pro připojení do dokumentu.

   **Metody:**

   .. py:method:: get_result_label()

      Vrací result label.

      :param result: Vstupní hodnota ``result`` pro danou operaci.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

   .. py:method:: check_filter_permission()

      Ověří filter permission.

      :param qs: Vstupní hodnota ``qs`` pro danou operaci.


.. py:class:: ProjectTableRowView

   Třída pohledu pro zobrazení řádku tabulky projektů pri připájení.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.


.. py:class:: UpravitDatumOznameniView

   Implementuje komponentu ``UpravitDatumOznameniView`` v rámci aplikace.

   **Metody:**

   .. py:method:: _get_existing_record()

      Vrací existing record.

      :param projekt: Vstupní hodnota ``projekt`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

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


.. py:class:: ZadostUdajeOznamovatelView

   Třida pohledu pro odeslání žádosti o údaje o oznamovateli.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

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


.. py:class:: ZadostOdhlaseniProjektuView

   Třida pohledu pro odeslání žádosti pro odhlášení projektu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

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


.. py:class:: ZadostZruseniProjektuView

   Třida pohledu pro odeslání žádosti pro zrušení projektu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

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


Funkce
------

.. py:function:: index(request)

   Funkce pohledu pro zobrazení indexu s navigací projektu.

   :param request: Popis parametru ``request``.

.. py:function:: detail(request, ident_cely)

   Funkce pohledu pro zobrazení detailu projektu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: post_ajax_get_projects_limit(request)

   Funkce pohledu pro získaní heatmapy projektu.

   :param request: Popis parametru ``request``.

.. py:function:: post_ajax_get_project_one(request)

   Funkce pohledu pro získaní geometrie projektu.

   :param request: Popis parametru ``request``.

.. py:function:: create(request)

   @jiri-bartos presunuto z post_ajax_get_project_pian_limit upraveno na queryset

   Funkce pohledu pro vytvoření projektu.

   :param request: Popis parametru ``request``.

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci projektu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání projektu pomoci modalu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: schvalit(request, ident_cely)

   Funkce pohledu pro schválení projektu pomoci modalu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: prihlasit(request, ident_cely)

   Funkce pohledu pro přihlášení projektu pomoci modalu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: zahajit_v_terenu(request, ident_cely)

   Funkce pohledu pro zahájení v terenu projektu pomoci modalu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: ukoncit_v_terenu(request, ident_cely)

   Funkce pohledu pro ukončení v terenu projektu pomoci modalu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: uzavrit(request, ident_cely)

   Funkce pohledu pro uzavření projektu pomoci modalu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: archivovat(request, ident_cely)

   Funkce pohledu pro archivaci projektu pomoci modalu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: navrhnout_ke_zruseni(request, ident_cely)

   Funkce pohledu pro navržení projektu ke zrušení pomoci modalu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: zrusit(request, ident_cely)

   Funkce pohledu pro zrušení projektu pomoci modalu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: vratit(request, ident_cely)

   Funkce pohledu pro vrácení projektu pomoci modalu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: vratit_navrh_zruseni(request, ident_cely)

   Funkce pohledu pro vrácení návrhu na zrušení projektu pomoci modalu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: odpojit_dokument(request, ident_cely, proj_ident_cely)

   Funkce pohledu pro odpojení dokumentu z projektu pomoci modalu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.
   :param proj_ident_cely: Popis parametru ``proj_ident_cely``.

.. py:function:: pripojit_dokument(request, proj_ident_cely)

   Funkce pohledu pro pripojení dokumentu z projektu pomoci modalu.

   :param request: Popis parametru ``request``.
   :param proj_ident_cely: Popis parametru ``proj_ident_cely``.

.. py:function:: generovat_oznameni(request, ident_cely)

   Funkce pohledu pro generování oznámení projektu pomoci modalu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: generovat_expertni_list(request, ident_cely)

   Funkce pohledu pro generování expertního listu projektu pomoci modalu.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní dátumů pro historii.


   **Argumenty:**

   - ``historie_vazby`` (*HistorieVazby*): model historieVazby daného projektu.

   **Návratová hodnota:**

   *historie*: dictionary dátumů k historii.

.. py:function:: get_detail_template_shows(projekt, user)

   Funkce pro získaní dictionary uživatelských akcí které mají být zobrazeny uživately.


   **Argumenty:**

   - ``projekt`` (*Projekt*): model projekt pro který se dané akce počítají.
   - ``user`` (*AuthUser*): uživatel pro kterého se dané akce počítají.

   **Návratová hodnota:**

   *show*: dictionary možností pro zobrazení.

.. py:function:: get_show_oznamovatel(projekt, user)

   Vrací show oznamovatel.

   :param projekt: Vstupní hodnota ``projekt`` pro danou operaci.
   :param user: Vstupní hodnota ``user`` pro danou operaci.

.. py:function:: get_required_fields(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu projektu.


   **Argumenty:**

   - ``zaznam`` (*Projekt*): model projekt pro který se dané pole počítají.
   - ``next`` (*int*): pokud je poskytnuto číslo tak se jedná o povinné pole pro příští stav.

   **Návratová hodnota:**

   *required_fields*: list polí.

.. py:function:: katastr_text_to_id(request)

   Funkce podlehu pro získaní ID katastru podle názvu katastru.

   :param request: Popis parametru ``request``.
