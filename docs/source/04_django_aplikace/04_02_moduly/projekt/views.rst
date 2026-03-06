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

      :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
      :param qs: Vstupní queryset, který má být dále zpracován.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Typová nebo konfigurační hodnota `permission` určující cílovou logiku.
      :param qs: Vstupní queryset, který má být dále zpracován.


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

      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

   .. py:method:: check_filter_permission()

      Ověří filter permission.

      :param qs: Vstupní queryset, který má být dále zpracován.


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

      :param projekt: Doménový objekt `projekt`, se kterým funkce pracuje.
      :return: Načtená data odpovídající zadaným vstupům.

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

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: detail(request, ident_cely)

   Funkce pohledu pro zobrazení detailu projektu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: post_ajax_get_projects_limit(request)

   Funkce pohledu pro získaní heatmapy projektu.

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: post_ajax_get_project_one(request)

   Funkce pohledu pro získaní geometrie projektu.

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: create(request)

   @jiri-bartos presunuto z post_ajax_get_project_pian_limit upraveno na queryset

   Funkce pohledu pro vytvoření projektu.

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci projektu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání projektu pomoci modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: schvalit(request, ident_cely)

   Funkce pohledu pro schválení projektu pomoci modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: prihlasit(request, ident_cely)

   Funkce pohledu pro přihlášení projektu pomoci modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: zahajit_v_terenu(request, ident_cely)

   Funkce pohledu pro zahájení v terenu projektu pomoci modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: ukoncit_v_terenu(request, ident_cely)

   Funkce pohledu pro ukončení v terenu projektu pomoci modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: uzavrit(request, ident_cely)

   Funkce pohledu pro uzavření projektu pomoci modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: archivovat(request, ident_cely)

   Funkce pohledu pro archivaci projektu pomoci modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: navrhnout_ke_zruseni(request, ident_cely)

   Funkce pohledu pro navržení projektu ke zrušení pomoci modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: zrusit(request, ident_cely)

   Funkce pohledu pro zrušení projektu pomoci modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: vratit(request, ident_cely)

   Funkce pohledu pro vrácení projektu pomoci modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: vratit_navrh_zruseni(request, ident_cely)

   Funkce pohledu pro vrácení návrhu na zrušení projektu pomoci modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: odpojit_dokument(request, ident_cely, proj_ident_cely)

   Funkce pohledu pro odpojení dokumentu z projektu pomoci modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.
   :param proj_ident_cely: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: pripojit_dokument(request, proj_ident_cely)

   Funkce pohledu pro pripojení dokumentu z projektu pomoci modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param proj_ident_cely: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: generovat_oznameni(request, ident_cely)

   Funkce pohledu pro generování oznámení projektu pomoci modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: generovat_expertni_list(request, ident_cely)

   Funkce pohledu pro generování expertního listu projektu pomoci modalu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní dátumů pro historii.

   :param historie_vazby: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
   :param request_user: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.
   :return: Slovník dat jednotlivých změn stavu pro zobrazení v historii.

.. py:function:: get_detail_template_shows(projekt, user)

   Funkce pro získaní dictionary uživatelských akcí které mají být zobrazeny uživately.

   :param projekt: Doménový objekt `projekt`, se kterým funkce pracuje.
   :param user: Uživatel, v jehož kontextu se operace provádí.
   :return: Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.

.. py:function:: get_show_oznamovatel(projekt, user)

   Vrací show oznamovatel.

   :param projekt: Doménový objekt `projekt`, se kterým funkce pracuje.
   :param user: Uživatel, v jehož kontextu se operace provádí.
   :return: Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.

.. py:function:: get_required_fields(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu projektu.

   :param zaznam: Záznam/objekt ``zaznam``, který funkce čte, validuje nebo upravuje.
   :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
   :return: Seznam názvů polí, která mají být v daném stavu povinná.

.. py:function:: katastr_text_to_id(request)

   Funkce podlehu pro získaní ID katastru podle názvu katastru.

   :param request: Aktuální HTTP request předaný view/funkci.
