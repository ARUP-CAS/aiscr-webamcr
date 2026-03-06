DOKUMENT views
==============

Definice views.

Třídy
------

.. py:class:: Model3DListView

   Třida pohledu pro zobrazení listu/tabulky s modelama 3D.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Záznam/objekt ``field``, který funkce čte, validuje nebo upravuje.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


.. py:class:: DokumentIndexView

   Třida pohledu pro zobrazení domovské stránky dokumentů s navigačními možnostmi.


.. py:class:: DokumentListView

   Třida pohledu pro zobrazení listu/tabulky s dokumentama.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Záznam/objekt ``field``, který funkce čte, validuje nebo upravuje.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


.. py:class:: RelatedContext

   Třida, která se dedí a která obsahuje metody pro získaní relací dokumentů.

   **Metody:**

   .. py:method:: get_cast()

      Metoda pro získaní informací ohlědně části dokumentu.

      :param context: Kontextová data používaná při serializaci nebo renderování.
      :param cast: Typ nebo hodnota použitá při převodu datového typu.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_context_data()

      Metoda pro získaní contextu dokumentu pro template.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: render_to_response()

      Metoda pro render response, kvúli správnemu zobrazení zpět možnosti.

      :param context: Kontextová data používaná při serializaci nebo renderování.
      :param response_kwargs: Dodatečné argumenty předané voláním.


.. py:class:: DokumentDetailView

   Třida pohledu pro zobrazení detailu dokumentu.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DokumentCastDetailView

   Třida pohledu pro zobrazení detailu části dokumentu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DokumentCastEditView

   Třida pohledu pro editaci části dokumentu pomocí modalu.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_success_url()

      Vrací success url.

   .. py:method:: get_object()

      Vrací object. v aplikaci.

      :param queryset: Vstupní queryset, který má být dále zpracován.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: form_invalid()

      Provádí operaci form invalid.

      :param form: Formulářová instance zpracovávaná funkcí.


.. py:class:: KomponentaDokumentDetailView

   Třida pohledu pro zobrazení detailu komponenty části dokumentu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: KomponentaDokumentCreateView

   Třida pohledu pro vytvoření komponenty části dokumentu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: TvarEditView

   Třida pohledu pro uložení zmeny tvaru z formuláře.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: TvarSmazatView

   Třida pohledu pro smazání tvaru dokumentu pomocí modalu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

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


.. py:class:: VytvoritCastView

   Třida pohledu pro vytvoření části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

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


.. py:class:: TransakceView

   Třida pohledu pro změnu stavu a práci s dokumentama cez modal, která se dedí pro jednotlivá změny.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
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


.. py:class:: DokumentCastPripojitAkciView

   Třida pohledu pro připojení akce do části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DokumentCastPripojitProjektView

   Třida pohledu pro připojení projektu do části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DokumentCastOdpojitView

   Třida pohledu pro odpojení části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DokumentCastSmazatView

   Třida pohledu pro smazání části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DokumentNeidentAkceSmazatView

   Třida pohledu pro smazání neident akce z části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DokumentAutocomplete

   Třída pohledu pro autocomplete dokumentů.

   **Metody:**

   .. py:method:: get_result_label()

      Vrací result label.

      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


.. py:class:: DokumentyAzTableView

   Třída pohledu pro zobrazení tabulky dokumentů.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param typ_vazby: Název nebo typ ``typ_vazby`` používaný pro volbu cílové logiky.
      :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.


Funkce
------

.. py:function:: index_model_3D(request)

   Funkce pohledu pro zobrazení domovské stránky modelu 3D s navigačními možnostmi.

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: detail_model_3D(request, ident_cely)

   Třida pohledu pro zobrazení detailu modelu 3D.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci dokumentu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: edit_model_3D(request, ident_cely)

   Funkce pohledu pro editaci modelu 3D.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: zapsat_do_akce(request, arch_z_ident_cely)

   Funkce pohledu pro zapsání dokumentu do akce.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param arch_z_ident_cely: Identifikátor ``arch_z_ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: zapsat_do_projektu(request, proj_ident_cely)

   Funkce pohledu pro zapsání dokumentu do projektu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param proj_ident_cely: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: create_model_3D(request)

   Funkce pohledu pro vytvoření modelu 3D.

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: odeslat(request, ident_cely)

   Funkce pohledu pro odeslání dokumentu cez modal.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: archivovat(request, ident_cely)

   Funkce pohledu pro archivaci dokumentu cez modal.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: vratit(request, ident_cely)

   Funkce pohledu pro vrácení dokumentu cez modal.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání dokumentu cez modal.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: get_hierarchie_dokument_typ()

   Funkce pro získaní hierarchie pro heslař.

.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní historických datumu.

   :param historie_vazby: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
   :param request_user: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.
   :return: Slovník dat jednotlivých změn stavu pro zobrazení v historii.

.. py:function:: get_detail_template_shows(dokument, user)

   Funkce pro získaní kontextu pro zobrazování možností na stránkách.

   :param dokument: Doménový objekt `dokument`, se kterým funkce pracuje.
   :param user: Uživatel, v jehož kontextu se operace provádí.
   :return: Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.

.. py:function:: zapsat(request, zaznam)

   Funkce pohledu pro zapsání dokumentu.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param zaznam: Záznam/objekt ``zaznam``, který funkce čte, validuje nebo upravuje.

.. py:function:: odpojit(request, ident_doku, ident_zaznamu, zaznam)

   Funkce pohledu pro odpojení dokumentu cez modal.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_doku: Identifikátor ``ident_doku`` používaný pro dohledání cílového záznamu.
   :param ident_zaznamu: Identifikátor ``ident_zaznamu`` používaný pro dohledání cílového záznamu.
   :param zaznam: Záznam/objekt ``zaznam``, který funkce čte, validuje nebo upravuje.

.. py:function:: pripojit(request, ident_zaznam, proj_ident_cely, typ)

   Funkce pohledu pro pripojení dokumentu cez modal.

   :param request: Aktuální HTTP request předaný view/funkci.
   :param ident_zaznam: Identifikátor ``ident_zaznam`` používaný pro dohledání cílového záznamu.
   :param proj_ident_cely: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.
   :param typ: Název nebo typ ``typ`` používaný pro volbu cílové logiky.

.. py:function:: get_dokument_table_row(request)

   Funkce pohledu pro získaní řádku dokumentu pro vykreslení v modalu.

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: get_dokument_table_row_vratit(request)

   AJAX pohled pro načtení jednoho řádku dokumentu do tabulky pro "vrácení dokumentu".

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: get_detail_view(ident_cely)

   Funkce pohledu pro redirect podle identu na model 3D nebo dokument detail.

   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: get_detail_json_view(ident_cely)

   Funkce pohledu pro vrácení url pro redirect podle identu na model 3D nebo dokument detail.

   :param ident_cely: Identifikátor ``ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: get_required_fields_model3D(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu modelu 3D.

   :param zaznam: Záznam/objekt ``zaznam``, který funkce čte, validuje nebo upravuje.
   :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
   :return: Seznam názvů polí, která mají být v daném stavu povinná.

.. py:function:: get_required_fields_dokument(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu dokumentu.

   :param zaznam: Záznam/objekt ``zaznam``, který funkce čte, validuje nebo upravuje.
   :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
   :return: Seznam názvů polí, která mají být v daném stavu povinná.

.. py:function:: get_komponenta_form_detail(komponenta, show, old_nalez_post, komp_ident_cely)

   Funkce pro získaní formsetu predmetu a objektu pro komponentu.

   :param komponenta: Komponenta, se kterou funkce pracuje.
   :param show: Číselná nebo geometrická hodnota `show` použitá při výpočtu nebo transformaci.
   :param old_nalez_post: Číselná nebo geometrická hodnota `old_nalez_post` použitá při výpočtu nebo transformaci.
   :param komp_ident_cely: Identifikátor ``komp_ident_cely`` používaný pro dohledání cílového záznamu.

.. py:function:: get_obdobi_choices()

   Funkce která vrací dvou stupňový heslař pro období.

.. py:function:: get_areal_choices()

   Funkce která vrací dvou stupňový heslař pro areál.

.. py:function:: post_ajax_get_3d_limit(request)

   Funkce pohledu pro získaní 3D.

   :param request: Aktuální HTTP request předaný view/funkci.

.. py:function:: zjisti_licenci_organizace(request)

   Funkce pohledu pro zjištení licence organizace.

   :param request: Aktuální HTTP request předaný view/funkci.
