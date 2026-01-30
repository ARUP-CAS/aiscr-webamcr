PROJEKT views
=============

Definice views.

Třídy
------

.. py:class:: ProjectPasFromEnvelopeView

   Trida pohledu pro získaní heatmapy pas.
   @jiri-bartos presunuto z post_ajax_get_project_pas_limit

   **Metody:**

   .. py:method:: post()


.. py:class:: ProjectPianFromEnvelopeView

   Trida pohledu pro získaní heatmapy pianu.
   @jiri-bartos presunuto z post_ajax_get_project_pian_limit upraveno na queryset

   **Metody:**

   .. py:method:: post()


.. py:class:: ProjektPermissionFilterMixin

   Popis není k dispozici.

   **Metody:**

   .. py:method:: add_ownership_lookup()

   .. py:method:: add_accessibility_lookup()


.. py:class:: ProjektListView

   Třida pohledu pro zobrazení listu/tabulky s projektami.

   **Metody:**

   .. py:method:: init_translations()

   .. py:method:: get_context_data()

   .. py:method:: get_queryset()


.. py:class:: GenerovatOznameniView

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get_redirect_url()


.. py:class:: ProjektAutocompleteBezZrusenych

   Třída pohledu získaní projektů pro autocomplete pro připojení do dokumentu.

   **Metody:**

   .. py:method:: get_result_label()

   .. py:method:: get_queryset()

   .. py:method:: check_filter_permission()


.. py:class:: ProjectTableRowView

   Třída pohledu pro zobrazení řádku tabulky projektů pri připájení.

   **Metody:**

   .. py:method:: get()


.. py:class:: UpravitDatumOznameniView

   Popis není k dispozici.

   **Metody:**

   .. py:method:: _get_existing_record()

   .. py:method:: get_context_data()

   .. py:method:: get()

   .. py:method:: post()


.. py:class:: ZadostUdajeOznamovatelView

   Třida pohledu pro odeslání žádosti o údaje o oznamovateli.

   **Metody:**

   .. py:method:: get_zaznam()

   .. py:method:: get()

   .. py:method:: post()


.. py:class:: ZadostOdhlaseniProjektuView

   Třida pohledu pro odeslání žádosti pro odhlášení projektu.

   **Metody:**

   .. py:method:: get_zaznam()

   .. py:method:: get()

   .. py:method:: post()


.. py:class:: ZadostZruseniProjektuView

   Třida pohledu pro odeslání žádosti pro zrušení projektu.

   **Metody:**

   .. py:method:: get_zaznam()

   .. py:method:: get()

   .. py:method:: post()


Funkce
------

.. py:function:: index(request)

   Funkce pohledu pro zobrazení indexu s navigací projektu.

.. py:function:: detail(request, ident_cely)

   Funkce pohledu pro zobrazení detailu projektu.

.. py:function:: post_ajax_get_projects_limit(request)

   Funkce pohledu pro získaní heatmapy projektu.

.. py:function:: post_ajax_get_project_one(request)

   Funkce pohledu pro získaní geometrie projektu.

.. py:function:: create(request)

   Funkce pohledu pro vytvoření projektu.

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci projektu.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání projektu pomoci modalu.

.. py:function:: schvalit(request, ident_cely)

   Funkce pohledu pro schválení projektu pomoci modalu.

.. py:function:: prihlasit(request, ident_cely)

   Funkce pohledu pro přihlášení projektu pomoci modalu.

.. py:function:: zahajit_v_terenu(request, ident_cely)

   Funkce pohledu pro zahájení v terenu projektu pomoci modalu.

.. py:function:: ukoncit_v_terenu(request, ident_cely)

   Funkce pohledu pro ukončení v terenu projektu pomoci modalu.

.. py:function:: uzavrit(request, ident_cely)

   Funkce pohledu pro uzavření projektu pomoci modalu.

.. py:function:: archivovat(request, ident_cely)

   Funkce pohledu pro archivaci projektu pomoci modalu.

.. py:function:: navrhnout_ke_zruseni(request, ident_cely)

   Funkce pohledu pro navržení projektu ke zrušení pomoci modalu.

.. py:function:: zrusit(request, ident_cely)

   Funkce pohledu pro zrušení projektu pomoci modalu.

.. py:function:: vratit(request, ident_cely)

   Funkce pohledu pro vrácení projektu pomoci modalu.

.. py:function:: vratit_navrh_zruseni(request, ident_cely)

   Funkce pohledu pro vrácení návrhu na zrušení projektu pomoci modalu.

.. py:function:: odpojit_dokument(request, ident_cely, proj_ident_cely)

   Funkce pohledu pro odpojení dokumentu z projektu pomoci modalu.

.. py:function:: pripojit_dokument(request, proj_ident_cely)

   Funkce pohledu pro pripojení dokumentu z projektu pomoci modalu.

.. py:function:: generovat_oznameni(request, ident_cely)

   Funkce pohledu pro generování oznámení projektu pomoci modalu.

.. py:function:: generovat_expertni_list(request, ident_cely)

   Funkce pohledu pro generování expertního listu projektu pomoci modalu.

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

   Popis není k dispozici.

.. py:function:: get_required_fields(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu projektu.


   **Argumenty:**

   - ``zaznam`` (*Projekt*): model projekt pro který se dané pole počítají.
   - ``next`` (*int*): pokud je poskytnuto číslo tak se jedná o povinné pole pro příští stav.

   **Návratová hodnota:**

   *required_fields*: list polí.

.. py:function:: katastr_text_to_id(request)

   Funkce podlehu pro získaní ID katastru podle názvu katastru.
