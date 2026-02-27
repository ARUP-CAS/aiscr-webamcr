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

      :return: Vrací výsledek provedené operace.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Vstupní hodnota ``field`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_queryset()

      Vrací queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: DokumentIndexView

   Třida pohledu pro zobrazení domovské stránky dokumentů s navigačními možnostmi.


.. py:class:: DokumentListView

   Třida pohledu pro zobrazení listu/tabulky s dokumentama.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Vstupní hodnota ``field`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_queryset()

      Vrací queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: RelatedContext

   Třida, která se dedí a která obsahuje metody pro získaní relací dokumentů.

   **Metody:**

   .. py:method:: get_cast()

      Metoda pro získaní informací ohlědně části dokumentu.

   .. py:method:: get_context_data()

      Metoda pro získaní contextu dokumentu pro template.

   .. py:method:: render_to_response()

      Metoda pro render response, kvúli správnemu zobrazení zpět možnosti.


.. py:class:: DokumentDetailView

   Třida pohledu pro zobrazení detailu dokumentu.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: DokumentCastDetailView

   Třida pohledu pro zobrazení detailu části dokumentu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: DokumentCastEditView

   Třida pohledu pro editaci části dokumentu pomocí modalu.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_success_url()

      Vrací success url.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_object()

      Vrací object.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: form_invalid()

      Provádí operaci form invalid.

      :param form: Vstupní hodnota ``form`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: KomponentaDokumentDetailView

   Třida pohledu pro zobrazení detailu komponenty části dokumentu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: KomponentaDokumentCreateView

   Třida pohledu pro vytvoření komponenty části dokumentu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: TvarEditView

   Třida pohledu pro uložení zmeny tvaru z formuláře.

   **Metody:**

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: TvarSmazatView

   Třida pohledu pro smazání tvaru dokumentu pomocí modalu.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_zaznam()

      Vrací zaznam.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: VytvoritCastView

   Třida pohledu pro vytvoření části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: TransakceView

   Třida pohledu pro změnu stavu a práci s dokumentama cez modal, která se dedí pro jednotlivá změny.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_zaznam()

      Vrací zaznam.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: DokumentCastPripojitAkciView

   Třida pohledu pro připojení akce do části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: DokumentCastPripojitProjektView

   Třida pohledu pro připojení projektu do části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: DokumentCastOdpojitView

   Třida pohledu pro odpojení části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: DokumentCastSmazatView

   Třida pohledu pro smazání části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

      :return: Vrací výsledek provedené operace.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: DokumentNeidentAkceSmazatView

   Třida pohledu pro smazání neident akce z části dokumentu pomoci modalu.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

      :return: Vrací výsledek provedené operace.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.


.. py:class:: DokumentAutocomplete

   Třída pohledu pro autocomplete dokumentů.

   **Metody:**

   .. py:method:: get_result_label()

      Vrací result label.

      :param result: Vstupní hodnota ``result`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_queryset()

      Vrací queryset.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: DokumentyAzTableView

   Třída pohledu pro zobrazení tabulky dokumentů.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param typ_vazby: Vstupní hodnota ``typ_vazby`` pro danou operaci.
      :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.


Funkce
------

.. py:function:: index_model_3D(request)

   Funkce pohledu pro zobrazení domovské stránky modelu 3D s navigačními možnostmi.

.. py:function:: detail_model_3D(request, ident_cely)

   Třida pohledu pro zobrazení detailu modelu 3D.

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro editaci dokumentu.

.. py:function:: edit_model_3D(request, ident_cely)

   Funkce pohledu pro editaci modelu 3D.

.. py:function:: zapsat_do_akce(request, arch_z_ident_cely)

   Funkce pohledu pro zapsání dokumentu do akce.

.. py:function:: zapsat_do_projektu(request, proj_ident_cely)

   Funkce pohledu pro zapsání dokumentu do projektu.

.. py:function:: create_model_3D(request)

   Funkce pohledu pro vytvoření modelu 3D.

.. py:function:: odeslat(request, ident_cely)

   Funkce pohledu pro odeslání dokumentu cez modal.

.. py:function:: archivovat(request, ident_cely)

   Funkce pohledu pro archivaci dokumentu cez modal.

.. py:function:: vratit(request, ident_cely)

   Funkce pohledu pro vrácení dokumentu cez modal.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro smazání dokumentu cez modal.

.. py:function:: get_hierarchie_dokument_typ()

   Funkce pro získaní hierarchie pro heslař.

.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní historických datumu.

.. py:function:: get_detail_template_shows(dokument, user)

   Funkce pro získaní kontextu pro zobrazování možností na stránkách.

.. py:function:: zapsat(request, zaznam)

   Funkce pohledu pro zapsání dokumentu.

.. py:function:: odpojit(request, ident_doku, ident_zaznamu, zaznam)

   Funkce pohledu pro odpojení dokumentu cez modal.

.. py:function:: pripojit(request, ident_zaznam, proj_ident_cely, typ)

   Funkce pohledu pro pripojení dokumentu cez modal.

.. py:function:: get_dokument_table_row(request)

   Funkce pohledu pro získaní řádku dokumentu pro vykreslení v modalu.

.. py:function:: get_dokument_table_row_vratit(request)

   AJAX pohled pro načtení jednoho řádku dokumentu do tabulky pro "vrácení dokumentu".

.. py:function:: get_detail_view(ident_cely)

   Funkce pohledu pro redirect podle identu na model 3D nebo dokument detail.

.. py:function:: get_detail_json_view(ident_cely)

   Funkce pohledu pro vrácení url pro redirect podle identu na model 3D nebo dokument detail.

.. py:function:: get_required_fields_model3D(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu modelu 3D.


   **Argumenty:**

   - ``zaznam`` (*Dokument*): model Dokument pro který se dané pole počítají.
   - ``next`` (*int*): pokud je poskytnuto číslo tak se jedná o povinné pole pro příští stav.

   **Návratová hodnota:**

   *required_fields*: list polí.

.. py:function:: get_required_fields_dokument(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu dokumentu.


   **Argumenty:**

   - ``zaznam`` (*Dokument*): model Dokument pro který se dané pole počítají.
   - ``next`` (*int*): pokud je poskytnuto číslo tak se jedná o povinné pole pro příští stav.

   **Návratová hodnota:**

   *required_fields*: list polí.

.. py:function:: get_komponenta_form_detail(komponenta, show, old_nalez_post, komp_ident_cely)

   Funkce pro získaní formsetu predmetu a objektu pro komponentu.

.. py:function:: get_obdobi_choices()

   Funkce která vrací dvou stupňový heslař pro období.

.. py:function:: get_areal_choices()

   Funkce která vrací dvou stupňový heslař pro areál.

.. py:function:: post_ajax_get_3d_limit(request)

   Funkce pohledu pro získaní 3D.

.. py:function:: zjisti_licenci_organizace(request)

   Funkce pohledu pro zjištení licence organizace.
