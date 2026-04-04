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

      **Návratová hodnota:**

      Vrací výsledek volání ``get_detail_template_shows()``.


   .. py:method:: get_archeologicky_zaznam()

      Metoda pro získaní akce z db.

      **Návratová hodnota:**

      Vrací výsledek volání ``get_object_or_404()``.


   .. py:method:: get_jednotky()

      Metoda pro získaní dokumentační jednotky navázané na akci.

      **Návratová hodnota:**

      Vrací výsledek volání ``prefetch_related()``.


   .. py:method:: get_dokumenty()

      Metoda pro získaní dokumentů navázaných na akci.

      **Návratová hodnota:**

      Vrací výsledek volání ``order_by()``.


   .. py:method:: get_externi_odkazy()

      Metoda pro získaní externích odkazů navázaných na akci.

      **Návratová hodnota:**

      Vrací výsledek volání ``order_by()``.


   .. py:method:: get_vedouci()

      Metoda pro získaní dalších vedoucích navázaných na akci.

      **Parametry:**

      - ``context``: Parametr ``context`` se předává do volání ``ostatni_vedouci_objekt_formset()``, ``filter()``.


   .. py:method:: check_locality_arch_z_conflict()

      Ověří locality arch z conflict.

      **Návratová hodnota:**

      Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

      **Výjimky:**

      - ``Http404``: Vyvolá se při splnění podmínky ``self.get_archeologicky_zaznam().lokalita``.


   .. py:method:: get_context_data()

      Metoda pro získaní contextu akci pro template.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací kontext šablony



.. py:class:: ArcheologickyZaznamDetailView

   Třída pohledu pro zobrazení detailu akce.

   **Metody:**

   .. py:method:: get_archeologicky_zaznam()

      Metoda pro získani záznamu akce z db podle ident_cely.

      **Návratová hodnota:**

      Vrací výsledek operace.


   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.



.. py:class:: DokumentacniJednotkaRelatedUpdateView

   Třida, která se dedí a která obsahuje metody pro získaní relací DJ.

   **Metody:**

   .. py:method:: dispatch()

      Ověří správnost vazby mezi dokumentační jednotkou a archeologickým záznamem před zpracováním požadavku.

      **Parametry:**

      - ``request``: HTTP požadavek; při nesprávné vazbě se použije k přesměrování na bezpečnou URL.
      - ``args``: Poziční argumenty předávané nadřazené metodě dispatch.
      - ``kwargs``: Klíčové argumenty obsahující ``dj_ident_cely`` a ``ident_cely`` pro načtení objektů.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: get_dokumentacni_jednotka()

      Metoda pro získani záznamu DJ z db podle ident_cely.

      **Návratová hodnota:**

      Vrací proměnná ``objects``.


   .. py:method:: get_context_data()

      Metoda pro získaní context dat DJ navíc oproti přepisované metóde, záznam DJ.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
      - ``args``: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``get()``.



.. py:class:: DokumentacniJednotkaCreateView

   Třída pohledu pro vytvoření dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření DJ.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
      - ``args``: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``get()``.



.. py:class:: DokumentacniJednotkaUpdateView

   Třída pohledu pro zobrazení detailu dokumentační jednotky s možností její úpravy.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat DJ navíc oproti přepisované metóde, pro zobrazení správneho detailu.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.



.. py:class:: KomponentaCreateView

   Třida pohledu pro vytvoření komponenty dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář na vytvoření komponenty.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.



.. py:class:: KomponentaUpdateView

   Třida pohledu pro editaci komponenty dokumentační jednotky.

   **Metody:**

   .. py:method:: dispatch()

      Ověří správnost vazby mezi komponentou a dokumentační jednotkou před zpracováním požadavku.

      **Parametry:**

      - ``request``: HTTP požadavek; při nesprávné vazbě se použije k přesměrování na bezpečnou URL.
      - ``args``: Poziční argumenty předávané nadřazené metodě dispatch.
      - ``kwargs``: Klíčové argumenty obsahující ``dj_ident_cely`` a ``komponenta_ident_cely`` pro načtení objektů.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: get_komponenta()

      Metoda pro získani záznamu komponenty z db podle ident_cely.

      **Návratová hodnota:**

      Vrací proměnná ``object``.


   .. py:method:: get_dokumentacni_jednotka()

      Vrací dokumentacni jednotka.

      **Návratová hodnota:**

      Vrací proměnná ``object``.


   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro úpravu komponenty,

      případně data poslaného chybného formuláře.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.



.. py:class:: PianCreateView

   Třida pohledu pro vytvoření PIANu dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření PIANu.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get()``, ``str()``, pracuje se s atributy ``user``.
      - ``args``: Poziční argumenty předávané nadřazené metodě get.
      - ``kwargs``: Klíčové argumenty předávané do ``get_context_data()``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render_to_response()``.

      **Výjimky:**

      - ``Exception``: Vyvolá se s textem "arch_z.views.PianCreateView.get.label_not_found"; nebo s textem "arch_z.views.PianCreateView.get.transormation_error".



.. py:class:: PianUpdateView

   Třida pohledu pro editaci PIANu dokumentační jednotky.

   **Metody:**

   .. py:method:: dispatch()

      Ověří správnost vazby mezi PIAN a dokumentační jednotkou před zpracováním požadavku.

      **Parametry:**

      - ``request``: HTTP požadavek; při nesprávné vazbě se použije k přesměrování na bezpečnou URL.
      - ``args``: Poziční argumenty předávané nadřazené metodě dispatch.
      - ``kwargs``: Klíčové argumenty obsahující ``dj_ident_cely`` a ``pian_ident_cely`` pro načtení objektů.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro editaci PIANu.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get()``, ``str()``, pracuje se s atributy ``user``.
      - ``args``: Poziční argumenty předávané nadřazené metodě get.
      - ``kwargs``: Klíčové argumenty předávané do ``get_context_data()``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render_to_response()``.

      **Výjimky:**

      - ``PermissionDenied``: Vyvolá se při splnění podmínky ``context['j'].pian.stav == PIAN_POTVRZEN``.
      - ``Exception``: Vyvolá se s textem "arch_z.views.PianUpdateView.get.label_not_found"; nebo s textem "arch_z.views.PianUpdateView.transormation_error".



.. py:class:: AdbCreateView

   Třida pohledu pro vytvoření PIANu dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření ADB.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.



.. py:class:: GetAkceOtherKatastrView

   Implementuje komponentu ``GetAkceOtherKatastrView`` v rámci aplikace.

   **Metody:**

   .. py:method:: post()

      Trida pohledu pro získaní souradnic dalších katastrů akce.

      **Parametry:**

      - ``request``: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: AkceIndexView

   Třida pohledu pro zobrazení domovské stránky akcií s navigačními možnostmi.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní kontextu podlehu.

      **Parametry:**

      - ``kwargs``: Klíčové argumenty; nejsou předávány nadřazené metodě, kontext se sestavuje přímo.

      **Návratová hodnota:**

      Vrací proměnná ``context``.



.. py:class:: AkceListView

   Třida pohledu pro zobrazení listu/tabulky s akcemi.

   **Metody:**

   .. py:method:: init_translations()

      Nastaví přeložené texty pro nadpisy, popisky a záhlaví přehledu akcí.

   .. py:method:: rename_field_for_ordering()

      Převede název pole z URL parametru na odpovídající databázový název pro řazení querysetu akcí.

      **Parametry:**

      - ``field``: Název pole z požadavku (může začínat znaménkem ``-`` pro sestupné řazení).

      **Návratová hodnota:**

      Vrací výsledek volání ``get()``.


   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      **Návratová hodnota:**

      Vrací výsledek volání ``check_filter_permission()``.



.. py:class:: ProjektAkceChange

   Třida pohledu pro zmenu projektové akce na samostatnou.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní kontextu podlehu.

      **Parametry:**

      - ``kwargs``: Klíčové argumenty předávané do sestavení kontextu.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: get()

      Metoda pro vrácení stránky při volání GET.

      **Parametry:**

      - ``request``: Parametr ``request`` se předává do volání ``check_stav_changed()``, ovlivňuje větvení podmínek.
      - ``args``: Poziční argumenty předávané nadřazené metodě get.
      - ``kwargs``: Klíčové argumenty předávané do ``get_context_data()``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render_to_response()``.


   .. py:method:: post()

      Metoda po potvrzení zmeny akce na samostatnou.

      Pri zavolíní se kontroluje, že akce nebyla změnena v mezičase potvrzení.
      Po úspešné kontrole se odebere projekt, nastaví typ akce na samostatnú a nastaví nový ident celý.
      Celá událost je zapsaná do historie.
      Uživatel je presmerován na detail akce.

      **Parametry:**

      - ``request``: Parametr ``request`` se předává do volání ``check_stav_changed()``, ``create_transaction()``, pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
      - ``args``: Poziční argumenty předávané nadřazené metodě post.
      - ``kwargs``: Klíčové argumenty předávané do ``get_context_data()``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: SamostatnaAkceChange

   Třida pohledu pro zmenu samostatní akce na projektovou.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní kontextu podlehu.

      **Parametry:**

      - ``kwargs``: Klíčové argumenty předávané do sestavení kontextu.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: get()

      Metoda pro vrácení stránky při volání GET s formulářem pro výběr projektu.

      **Parametry:**

      - ``request``: Parametr ``request`` se předává do volání ``check_stav_changed()``, ovlivňuje větvení podmínek.
      - ``args``: Poziční argumenty předávané nadřazené metodě get.
      - ``kwargs``: Klíčové argumenty předávané do ``get_context_data()``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render_to_response()``.


   .. py:method:: post()

      Metoda po potvrzení zmeny akce na projektovou.

      Pri zavolíní se kontroluje, že akce nebyla změnena v mezičase potvrzení.
      Po úspešné kontrole se napojí projekt, nastaví typ akce na projektovou a nastaví nový ident celý.
      Celá událost je zapsaná do historie.
      Uživatel je presmerován na detail akce.

      **Parametry:**

      - ``request``: Objekt HTTP požadavku s POST daty
      - ``args``: Další poziční argumenty dědězité z nadřazené třídy, nepoužívané.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``redirect()``.



.. py:class:: ArchZAutocomplete

   Třida pohledu pro vrácení výsledku pro autocomplete arch záznamů.

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



.. py:class:: ArchZTableRowView

   Třida pohledu pro vrácení řádku tabulky s arch záznamem.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get()``, pracuje se s atributy ``GET``.

      **Návratová hodnota:**

      Vrací výsledek volání ``HttpResponse()``.



Funkce
------

.. py:function:: get_obdobi_choices()

   Funkce která vrací dvou stupňový heslař pro období.

   **Návratová hodnota:**

   Vrací výsledek volání ``heslar_12()``.


.. py:function:: get_areal_choices()

   Funkce která vrací dvou stupňový heslař pro areál.

   **Návratová hodnota:**

   Vrací výsledek volání ``heslar_12()``.


.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro zobrazení a zpracování editace akce.

   Na začátku se kontroluje, jestli stav není archivovaný.
   Zobrazení se skládá ze 3 formulářů: CreateArchZForm, CreateAkceForm a formsetu pro další vedoucí.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``CreateArchZForm()``, ``CreateAkceForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``redirect()``, vstupuje do návratové hodnoty.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.

   **Výjimky:**

   - ``PermissionDenied``: Vyvolá se při splnění podmínky ``zaznam.stav == AZ_STAV_ARCHIVOVANY``.


.. py:function:: odeslat(request, ident_cely)

   Funkce pohledu pro zobrazení a zpracování odeslání akce.

   Na začátku se kontroluje, jestli stav není jiný než zapsaný nebo někdo nezměnil stav akce během odesílání.
   Při GET volání se kontrolují vyplněná pole akce a její relace pomocí metody na modelu.
   Po POST volání se volá metoda na modelu pro posun stavu do odeslaného.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``debug()``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: archivovat(request, ident_cely)

   Funkce pohledu pro zobrazení a zpracování archivace akce.

   Na začátku se kontroluje, jestli stav není jiný než odeslaný nebo někdo nezměnil stav akce během archivace.
   Při GET volání se kontrolují vyplněná pole akce a její relace pomocí metody na modelu.
   Po POST volání se volá metoda na modelu pro posun stavu do odeslaného.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``debug()``, ``get_object_or_404()``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: vratit(request, ident_cely)

   Funkce pohledu pro zobrazení a zpracování vrácení stavu akce o jeden krok zpět.

   Na začátku se kontroluje, jestli někdo nezměnil stav akce během vrácení.
   Pro vrácení se používá formulář pro vrácení, který je jednotný napříč aplikací.
   Po POST volání se volá metoda na modelu pro posun stavu zpět.
   Pokud se jedná o projektovou akci, tak se vrací i stav projektu ze stavu uzavřený nebo archivovaný.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``check_stav_changed()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``debug()``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

   **Výjimky:**

   - ``PermissionDenied``: Vyvolá se při splnění podmínky ``dokument.stav != D_STAV_ODESLANY``.
   - ``StateChangedError``: Vyvolá se při splnění podmínky ``check_stav_changed(request, dokument)``.


.. py:function:: zapsat(request, projekt_ident_cely)

   Funkce pohledu pro vytvoření akce.

   Na začátku se kontroluje, jestli jde o vytvoření projektové nebo samostatné akce a zda je možné projektovou akci vytvořit.
   Zobrazení se skládá ze 3 formulářů: CreateArchZForm, CreateAkceForm a formsetu pro další vedoucí.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``CreateArchZForm()``, ``CreateAkceForm()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``projekt_ident_cely``: Identifikátor ``projekt_ident_cely`` používaný pro dohledání cílového záznamu.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``render()``.

   **Výjimky:**

   - ``PermissionDenied``: Vyvolá se při splnění podmínky ``not PROJEKT_STAV_ZAPSANY < projekt.stav < PROJEKT_STAV_ARCHIVOVANY``; nebo při splnění podmínky ``projekt.typ_projektu.id == TYP_PROJEKTU_PRUZKUM_ID``.


.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro zobrazení a zpracování smazání akce.

   Na začátku se kontroluje, jestli někdo nezměnil stav akce během smazání.
   Po POST volání se volá metoda na modelu pro smazání akce.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``check_stav_changed()``, ``create_transaction()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get_object_or_404()``, ``debug()``.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: pripojit_dokument(request, arch_z_ident_cely, proj_ident_cely)

   Funkce pohledu pro připojení dokumentu do akce.

   Funkce volá další funkci pro připojení s parametrem třídou modelu navíc.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``pripojit()``, vstupuje do návratové hodnoty.
   - ``arch_z_ident_cely``: Identifikátor ``arch_z_ident_cely`` používaný pro dohledání cílového záznamu.
   - ``proj_ident_cely``: Identifikátor ``proj_ident_cely`` používaný pro dohledání cílového záznamu.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``pripojit()``.


.. py:function:: odpojit_dokument(request, ident_cely, arch_z_ident_cely)

   Funkce pohledu pro odpojení dokumentu do akce.

   Funkce volá další funkci pro odpojení s parametrem navíc - arch záznamem.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``odpojit()``, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``filter()``, ``odpojit()``, vstupuje do návratové hodnoty.
   - ``arch_z_ident_cely``: Identifikátor ``arch_z_ident_cely`` používaný pro dohledání cílového záznamu.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``odpojit()``.


.. py:function:: post_ajax_get_pians(request)

   Vypada nepouzito check s J. Bartos

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

   **Návratová hodnota:**

   Vrací výsledek volání ``JsonResponse()``.


.. py:function:: post_akce2kat(request)

   Funkce pohledu pro získaní souradnic katastru akce.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``loads()``, pracuje se s atributy ``body``.

   **Návratová hodnota:**

   Vrací výsledek volání ``JsonResponse()``.


.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní dátumů pro historii.

   **Parametry:**

   - ``historie_vazby``: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
   - ``request_user``: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.

   **Návratová hodnota:**

   Slovník dat jednotlivých změn stavu pro zobrazení v historii.


.. py:function:: get_detail_template_shows(archeologicky_zaznam, dok_jednotky, user, app)

   Funkce pro získaní dictionary uživatelských akcí které mají být zobrazeny uživately.

   **Parametry:**

   - ``archeologicky_zaznam``: Parametr ``archeologicky_zaznam`` předává se do volání ``check_permissions()``, pracuje se s atributy ``ident_cely``, ``stav``, ovlivňuje větvení podmínek.
   - ``dok_jednotky``: Kolekce ``dok_jednotky`` zpracovávaná touto funkcí.
   - ``user``: Parametr ``user`` se předává do volání ``check_permissions()``, ovlivňuje větvení podmínek.
   - ``app``: Parametr ``app`` předává se do volání ``check_permissions()``.

   **Návratová hodnota:**

   Slovník příznaků určujících, které akce se mají v detailu zobrazit.


.. py:function:: get_required_fields(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu arch záznamů.

   **Parametry:**

   - ``zaznam``: Parametr ``zaznam`` pracuje se s atributy ``stav``, ovlivňuje větvení podmínek.
   - ``next``: Posun vůči aktuálnímu stavu (pro kontrolu povinných polí v následujícím kroku).

   **Návratová hodnota:**

   Seznam názvů polí, která mají být v daném stavu povinná.


.. py:function:: smazat_akce_vedoucí(request, ident_cely, akce_vedouci_id)

   Funkce pohledu pro smazání dalšího vedoucího akce.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``add_message()``, ``create_transaction()``, pracuje se s atributy ``method``, ``user``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``debug()``, ``get_object_or_404()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
   - ``akce_vedouci_id``: Identifikátor ``akce_vedouci_id`` používaný pro dohledání cílového záznamu.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: get_dj_form_detail(app, jednotka, jednotky, show, old_adb_post, user, session)

   Funkce pro získaní dictionary contextu dokumentační jednotky.

   **Parametry:**

   - ``app``: druh archeologického záznamu ro který se daný context počítá.
   - ``jednotka``: model DokumentacniJednotka pro který se daný context počítá.
   - ``jednotky``: list modelů DokumentacniJednotka použit pro správně zobrazení možnosti zmeny typu DJ.
   - ``show``: dictionary pro zobrazení možnosti uživatele na stránce.
   - ``old_adb_post``: staré volání CreateADBForm pro správně zobrazení chyb formuláře.
   - ``user``: Parametr ``user`` se předává do volání ``check_permissions()``, pracuje se s atributy ``hlavni_role``, ovlivňuje větvení podmínek.
   - ``session``: Volitelná Django session pro načtení dat souběžné editace ADB formuláře.

   **Návratová hodnota:**

   dictionary kontextu DJ pro správné zobrazení stránky.

