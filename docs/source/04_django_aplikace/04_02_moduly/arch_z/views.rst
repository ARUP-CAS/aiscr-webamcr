ARCH_Z views
============

Definice views.

Třídy
------

.. py:class:: AkceRelatedRecordUpdateView

   Třida, která se dedí a která obsahuje metody pro získaní relací akce.

   **Metody:**

   .. py:method:: get_shows()

      Metoda pro získaní informací které části stránky mají být zobrazeny.

      :return: Vrací výsledek volání ``get_detail_template_shows()``.

   .. py:method:: get_archeologicky_zaznam()

      Metoda pro získaní akce z db.

      :return: Vrací výsledek volání ``get_object_or_404()``.

   .. py:method:: get_jednotky()

      Metoda pro získaní dokumentační jednotky navázané na akci.

      :return: Vrací výsledek volání ``prefetch_related()``.

   .. py:method:: get_dokumenty()

      Metoda pro získaní dokumentů navázaných na akci.

      :return: Vrací výsledek volání ``order_by()``.

   .. py:method:: get_externi_odkazy()

      Metoda pro získaní externích odkazů navázaných na akci.

      :return: Vrací výsledek volání ``order_by()``.

   .. py:method:: get_vedouci()

      Metoda pro získaní dalších vedoucích navázaných na akci.

      :param context: Parametr ``context`` se předává do volání ``ostatni_vedouci_objekt_formset()``, ``filter()``.

   .. py:method:: check_locality_arch_z_conflict()

      Ověří locality arch z conflict.

      :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
      :raises Http404: Vyvolá se při splnění podmínky ``self.get_archeologicky_zaznam().lokalita``.

   .. py:method:: get_context_data()

      Metoda pro získaní contextu akci pro template.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.


.. py:class:: ArcheologickyZaznamDetailView

   Třída pohledu pro zobrazení detailu akce.

   **Metody:**

   .. py:method:: get_archeologicky_zaznam()

      Metoda pro získani záznamu akce z db podle ident_cely.

      :return: Vrací výsledek operace.

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.


.. py:class:: DokumentacniJednotkaRelatedUpdateView

   Třida, která se dedí a která obsahuje metody pro získaní relací DJ.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_dokumentacni_jednotka()

      Metoda pro získani záznamu DJ z db podle ident_cely.

      :return: Vrací proměnná ``objects``.

   .. py:method:: get_context_data()

      Metoda pro získaní context dat DJ navíc oproti přepisované metóde, záznam DJ.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``get()``.


.. py:class:: DokumentacniJednotkaCreateView

   Třída pohledu pro vytvoření dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření DJ.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``get()``.


.. py:class:: DokumentacniJednotkaUpdateView

   Třída pohledu pro zobrazení detailu dokumentační jednotky s možností její úpravy.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat DJ navíc oproti přepisované metóde, pro zobrazení správneho detailu.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.


.. py:class:: KomponentaCreateView

   Třida pohledu pro vytvoření komponenty dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář na vytvoření komponenty.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.


.. py:class:: KomponentaUpdateView

   Třida pohledu pro editaci komponenty dokumentační jednotky.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_komponenta()

      Metoda pro získani záznamu komponenty z db podle ident_cely.

      :return: Vrací proměnná ``object``.

   .. py:method:: get_dokumentacni_jednotka()

      Vrací dokumentacni jednotka.

      :return: Vrací proměnná ``object``.

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro úpravu komponenty,

      případně data poslaného chybného formuláře.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.


.. py:class:: PianCreateView

   Třida pohledu pro vytvoření PIANu dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření PIANu.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``get()``, ``str()``, pracuje se s atributy ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render_to_response()``.
      :raises Exception: Vyvolá se s textem "arch_z.views.PianCreateView.get.label_not_found"; nebo s textem "arch_z.views.PianCreateView.get.transormation_error".


.. py:class:: PianUpdateView

   Třida pohledu pro editaci PIANu dokumentační jednotky.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro editaci PIANu.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``get()``, ``str()``, pracuje se s atributy ``user``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render_to_response()``.
      :raises PermissionDenied: Vyvolá se při splnění podmínky ``context['j'].pian.stav == PIAN_POTVRZEN``.
      :raises Exception: Vyvolá se s textem "arch_z.views.PianUpdateView.get.label_not_found"; nebo s textem "arch_z.views.PianUpdateView.transormation_error".


.. py:class:: AdbCreateView

   Třida pohledu pro vytvoření PIANu dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření ADB.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.


.. py:class:: GetAkceOtherKatastrView

   Implementuje komponentu ``GetAkceOtherKatastrView`` v rámci aplikace.

   **Metody:**

   .. py:method:: post()

      Trida pohledu pro získaní souradnic dalších katastrů akce.

      :param request: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: AkceIndexView

   Třida pohledu pro zobrazení domovské stránky akcií s navigačními možnostmi.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní kontextu podlehu.

      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

      :return: Vrací proměnná ``context``.


.. py:class:: AkceListView

   Třida pohledu pro zobrazení listu/tabulky s akcemi.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Parametr ``field`` předává se do volání ``get()``, pracuje se s atributy ``replace``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``get()``.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací výsledek volání ``check_filter_permission()``.


.. py:class:: ProjektAkceChange

   Třida pohledu pro zmenu projektové akce na samostatnou.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní kontextu podlehu.

      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Metoda pro vrácení stránky při volání GET.

      :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ovlivňuje větvení podmínek.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render_to_response()``.

   .. py:method:: post()

      Metoda po potvrzení zmeny akce na samostatnou.

      Pri zavolíní se kontroluje, že akce nebyla změnena v mezičase potvrzení.
      Po úspešné kontrole se odebere projekt, nastaví typ akce na samostatnú a nastaví nový ident celý.
      Celá událost je zapsaná do historie.
      Uživatel je presmerován na detail akce.

      :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ``create_transaction()``, pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: SamostatnaAkceChange

   Třida pohledu pro zmenu samostatní akce na projektovou.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní kontextu podlehu.

      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

      :return: Vrací proměnná ``context``.

   .. py:method:: get()

      Metoda pro vrácení stránky při volání GET s formulářem pro výběr projektu.

      :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ovlivňuje větvení podmínek.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render_to_response()``.

   .. py:method:: post()

      Metoda po potvrzení zmeny akce na projektovou.

      Pri zavolíní se kontroluje, že akce nebyla změnena v mezičase potvrzení.
      Po úspešné kontrole se napojí projekt, nastaví typ akce na projektovou a nastaví nový ident celý.
      Celá událost je zapsaná do historie.
      Uživatel je presmerován na detail akce.

      :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ``PripojitProjektForm()``, pracuje se s atributy ``POST``, ``user``, ovlivňuje větvení podmínek.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``redirect()``.


.. py:class:: ArchZAutocomplete

   Třida pohledu pro vrácení výsledku pro autocomplete arch záznamů.

   **Metody:**

   .. py:method:: get_result_label()

      Vrací result label.

      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``none()``, výsledek volání ``check_filter_permission()``.


.. py:class:: ArchZTableRowView

   Třida pohledu pro vrácení řádku tabulky s arch záznamem.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``get()``, pracuje se s atributy ``GET``.

      :return: Vrací výsledek volání ``HttpResponse()``.


Funkce
------

.. py:function:: get_obdobi_choices()

   Funkce která vrací dvou stupňový heslař pro období.

   :return: Vrací výsledek volání ``heslar_12()``.

.. py:function:: get_areal_choices()

   Funkce která vrací dvou stupňový heslař pro areál.

   :return: Vrací výsledek volání ``heslar_12()``.

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro zobrazení a zpracování editace akce.

   Na začátku se kontroluje, jestli stav není archivovaný.
   Zobrazení se skládá ze 3 formulářů: CreateArchZForm, CreateAkceForm a formsetu pro další vedoucí.

   :param request: Parametr ``request`` se předává do volání ``CreateArchZForm()``, ``CreateAkceForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``redirect()``, vstupuje do návratové hodnoty.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
   :raises PermissionDenied: Vyvolá se při splnění podmínky ``zaznam.stav == AZ_STAV_ARCHIVOVANY``.

.. py:function:: odeslat(request, ident_cely)

   Funkce pohledu pro zobrazení a zpracování odeslání akce.

   Na začátku se kontroluje, jestli stav není jiný než zapsaný nebo někdo nezměnil stav akce během odesílání.
   Při GET volání se kontrolují vyplněná pole akce a její relace pomocí metody na modelu.
   Po POST volání se volá metoda na modelu pro posun stavu do odeslaného.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``debug()``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: archivovat(request, ident_cely)

   Funkce pohledu pro zobrazení a zpracování archivace akce.

   Na začátku se kontroluje, jestli stav není jiný než odeslaný nebo někdo nezměnil stav akce během archivace.
   Při GET volání se kontrolují vyplněná pole akce a její relace pomocí metody na modelu.
   Po POST volání se volá metoda na modelu pro posun stavu do odeslaného.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``debug()``, ``get_object_or_404()``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: vratit(request, ident_cely)

   Funkce pohledu pro zobrazení a zpracování vrácení stavu akce o jeden krok zpět.

   Na začátku se kontroluje, jestli někdo nezměnil stav akce během vrácení.
   Pro vrácení se používá formulář pro vrácení, který je jednotný napříč aplikací.
   Po POST volání se volá metoda na modelu pro posun stavu zpět.
   Pokud se jedná o projektovou akci, tak se vrací i stav projektu ze stavu uzavřený nebo archivovaný.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``debug()``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.
   :raises PermissionDenied: Vyvolá se při splnění podmínky ``dokument.stav != D_STAV_ODESLANY``.
   :raises StateChangedError: Vyvolá se při splnění podmínky ``check_stav_changed(request, dokument)``.

.. py:function:: zapsat(request, projekt_ident_cely)

   Funkce pohledu pro vytvoření akce.

   Na začátku se kontroluje, jestli jde o vytvoření projektové nebo samostatné akce a zda je možné projektovou akci vytvořit.
   Zobrazení se skládá ze 3 formulářů: CreateArchZForm, CreateAkceForm a formsetu pro další vedoucí.

   :param request: Parametr ``request`` se předává do volání ``CreateArchZForm()``, ``CreateAkceForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param projekt_ident_cely: Identifikátor ``projekt_ident_cely`` používaný pro dohledání cílového záznamu.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.
   :raises PermissionDenied: Vyvolá se při splnění podmínky ``not PROJEKT_STAV_ZAPSANY < projekt.stav < PROJEKT_STAV_ARCHIVOVANY``; nebo při splnění podmínky ``projekt.typ_projektu.id == TYP_PROJEKTU_PRUZKUM_ID``.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro zobrazení a zpracování smazání akce.

   Na začátku se kontroluje, jestli někdo nezměnil stav akce během smazání.
   Po POST volání se volá metoda na modelu pro smazání akce.

   :param request: Parametr ``request`` se předává do volání ``check_stav_changed()``, ``create_transaction()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``debug()``.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: pripojit_dokument(request, arch_z_ident_cely, proj_ident_cely)

   Funkce pohledu pro připojení dokumentu do akce.

   Funkce volá další funkci pro připojení s parametrem třídou modelu navíc.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``pripojit()``, vstupuje do návratové hodnoty.
   :param arch_z_ident_cely: Identifikátor ``arch_z_ident_cely`` používaný pro dohledání cílového záznamu.
   :param proj_ident_cely: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``pripojit()``.

.. py:function:: odpojit_dokument(request, ident_cely, arch_z_ident_cely)

   Funkce pohledu pro odpojení dokumentu do akce.

   Funkce volá další funkci pro odpojení s parametrem navíc - arch záznamem.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``odpojit()``, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``filter()``, ``odpojit()``, vstupuje do návratové hodnoty.
   :param arch_z_ident_cely: Identifikátor ``arch_z_ident_cely`` používaný pro dohledání cílového záznamu.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``odpojit()``.

.. py:function:: post_ajax_get_pians(request)

   Vypada nepouzito check s J. Bartos

   :param request: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

   :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: post_akce2kat(request)

   Funkce pohledu pro získaní souradnic katastru akce.

   :param request: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

   :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní dátumů pro historii.

   :param historie_vazby: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
   :param request_user: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.
   :return: Slovník dat jednotlivých změn stavu pro zobrazení v historii.

.. py:function:: get_detail_template_shows(archeologicky_zaznam, dok_jednotky, user, app)

   Funkce pro získaní dictionary uživatelských akcí které mají být zobrazeny uživately.

   :param archeologicky_zaznam: Parametr ``archeologicky_zaznam`` předává se do volání ``check_permissions()``, pracuje se s atributy ``ident_cely``, ``stav``, ovlivňuje větvení podmínek.
   :param dok_jednotky: Kolekce ``dok_jednotky`` zpracovávaná touto funkcí.
   :param user: Parametr ``user`` se předává do volání ``check_permissions()``, ovlivňuje větvení podmínek.
   :param app: Parametr ``app`` předává se do volání ``check_permissions()``.
   :return: Slovník příznaků určujících, které akce se mají v detailu zobrazit.

.. py:function:: get_required_fields(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu arch záznamů.

   :param zaznam: Parametr ``zaznam`` pracuje se s atributy ``stav``, ovlivňuje větvení podmínek.
   :param next: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).
   :return: Seznam názvů polí, která mají být v daném stavu povinná.

.. py:function:: smazat_akce_vedoucí(request, ident_cely, akce_vedouci_id)

   Funkce pohledu pro smazání dalšího vedoucího akce.

   :param request: Parametr ``request`` se předává do volání ``add_message()``, ``create_transaction()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param ident_cely: Parametr ``ident_cely`` se předává do volání ``debug()``, ``get_object_or_404()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   :param akce_vedouci_id: Identifikátor ``akce_vedouci_id`` používaný pro dohledání cílového záznamu.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: get_dj_form_detail(app, jednotka, jednotky, show, old_adb_post, user, session)

   Funkce pro získaní dictionary contextu dokumentační jednotky.

   :param app: druh archeologického záznamu ro který se daný context počítá.
   :param jednotka: model DokumentacniJednotka pro který se daný context počítá.
   :param jednotky: list modelů DokumentacniJednotka použit pro správně zobrazení možnosti zmeny typu DJ.
   :param show: dictionary pro zobrazení možnosti uživatele na stránce.
   :param old_adb_post: staré volání CreateADBForm pro správně zobrazení chyb formuláře.
   :param user: Parametr ``user`` se předává do volání ``check_permissions()``, pracuje se s atributy ``hlavni_role``, ovlivňuje větvení podmínek.
   :param session: Volitelná Django session pro načtení dat souběžné editace ADB formuláře.

   :return: dictionary kontextu DJ pro správné zobrazení stránky.
