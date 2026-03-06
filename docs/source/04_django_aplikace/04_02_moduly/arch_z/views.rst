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

   .. py:method:: get_archeologicky_zaznam()

      Metoda pro získaní akce z db.

   .. py:method:: get_jednotky()

      Metoda pro získaní dokumentační jednotky navázané na akci.

   .. py:method:: get_dokumenty()

      Metoda pro získaní dokumentů navázaných na akci.

   .. py:method:: get_externi_odkazy()

      Metoda pro získaní externích odkazů navázaných na akci.

   .. py:method:: get_vedouci()

      Metoda pro získaní dalších vedoucích navázaných na akci.

      :param context: Popis parametru ``context``.

   .. py:method:: check_locality_arch_z_conflict()

      Ověří locality arch z conflict.

   .. py:method:: get_context_data()

      Metoda pro získaní contextu akci pro template.

      :param kwargs: Popis parametru ``kwargs``.


.. py:class:: ArcheologickyZaznamDetailView

   Třída pohledu pro zobrazení detailu akce.

   **Metody:**

   .. py:method:: get_archeologicky_zaznam()

      Metoda pro získani záznamu akce z db podle ident_cely.

      :return: Vrací výsledek operace.

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde.

      :param kwargs: Popis parametru ``kwargs``.


.. py:class:: DokumentacniJednotkaRelatedUpdateView

   Třida, která se dedí a která obsahuje metody pro získaní relací DJ.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_dokumentacni_jednotka()

      Metoda pro získani záznamu DJ z db podle ident_cely.

   .. py:method:: get_context_data()

      Metoda pro získaní context dat DJ navíc oproti přepisované metóde, záznam DJ.

      :param kwargs: Popis parametru ``kwargs``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DokumentacniJednotkaCreateView

   Třída pohledu pro vytvoření dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření DJ.

      :param kwargs: Popis parametru ``kwargs``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DokumentacniJednotkaUpdateView

   Třída pohledu pro zobrazení detailu dokumentační jednotky s možností její úpravy.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat DJ navíc oproti přepisované metóde, pro zobrazení správneho detailu.

      :param kwargs: Popis parametru ``kwargs``.


.. py:class:: KomponentaCreateView

   Třida pohledu pro vytvoření komponenty dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář na vytvoření komponenty.

      :param kwargs: Popis parametru ``kwargs``.


.. py:class:: KomponentaUpdateView

   Třida pohledu pro editaci komponenty dokumentační jednotky.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_komponenta()

      Metoda pro získani záznamu komponenty z db podle ident_cely.

   .. py:method:: get_dokumentacni_jednotka()

      Vrací dokumentacni jednotka.

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro úpravu komponenty,

      případně data poslaného chybného formuláře.

      :param kwargs: Popis parametru ``kwargs``.


.. py:class:: PianCreateView

   Třida pohledu pro vytvoření PIANu dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření PIANu.

      :param kwargs: Popis parametru ``kwargs``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: PianUpdateView

   Třida pohledu pro editaci PIANu dokumentační jednotky.

   **Metody:**

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro editaci PIANu.

      :param kwargs: Popis parametru ``kwargs``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: AdbCreateView

   Třida pohledu pro vytvoření PIANu dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření ADB.

      :param kwargs: Popis parametru ``kwargs``.


.. py:class:: GetAkceOtherKatastrView

   Implementuje komponentu ``GetAkceOtherKatastrView`` v rámci aplikace.

   **Metody:**

   .. py:method:: post()

      Trida pohledu pro získaní souradnic dalších katastrů akce.

      :param request: Popis parametru ``request``.


.. py:class:: AkceIndexView

   Třida pohledu pro zobrazení domovské stránky akcií s navigačními možnostmi.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní kontextu podlehu.

      :param kwargs: Popis parametru ``kwargs``.


.. py:class:: AkceListView

   Třida pohledu pro zobrazení listu/tabulky s akcemi.

   **Metody:**

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: rename_field_for_ordering()

      Provádí operaci rename field for ordering.

      :param field: Vstupní hodnota ``field`` pro danou operaci.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


.. py:class:: ProjektAkceChange

   Třida pohledu pro zmenu projektové akce na samostatnou.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní kontextu podlehu.

      :param kwargs: Popis parametru ``kwargs``.

   .. py:method:: get()

      Metoda pro vrácení stránky při volání GET.

      :param request: Popis parametru ``request``.
      :param args: Popis parametru ``args``.
      :param kwargs: Popis parametru ``kwargs``.

   .. py:method:: post()

      Metoda po potvrzení zmeny akce na samostatnou.

      Pri zavolíní se kontroluje, že akce nebyla změnena v mezičase potvrzení.
      Po úspešné kontrole se odebere projekt, nastaví typ akce na samostatnú a nastaví nový ident celý.
      Celá událost je zapsaná do historie.
      Uživatel je presmerován na detail akce.

      :param request: Popis parametru ``request``.
      :param args: Popis parametru ``args``.
      :param kwargs: Popis parametru ``kwargs``.


.. py:class:: SamostatnaAkceChange

   Třida pohledu pro zmenu samostatní akce na projektovou.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní kontextu podlehu.

      :param kwargs: Popis parametru ``kwargs``.

   .. py:method:: get()

      Metoda pro vrácení stránky při volání GET s formulářem pro výběr projektu.

      :param request: Popis parametru ``request``.
      :param args: Popis parametru ``args``.
      :param kwargs: Popis parametru ``kwargs``.

   .. py:method:: post()

      Metoda po potvrzení zmeny akce na projektovou.

      Pri zavolíní se kontroluje, že akce nebyla změnena v mezičase potvrzení.
      Po úspešné kontrole se napojí projekt, nastaví typ akce na projektovou a nastaví nový ident celý.
      Celá událost je zapsaná do historie.
      Uživatel je presmerován na detail akce.

      :param request: Popis parametru ``request``.
      :param args: Popis parametru ``args``.
      :param kwargs: Popis parametru ``kwargs``.


.. py:class:: ArchZAutocomplete

   Třida pohledu pro vrácení výsledku pro autocomplete arch záznamů.

   **Metody:**

   .. py:method:: get_result_label()

      Vrací result label.

      :param result: Vstupní hodnota ``result`` pro danou operaci.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.


.. py:class:: ArchZTableRowView

   Třida pohledu pro vrácení řádku tabulky s arch záznamem.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.


Funkce
------

.. py:function:: get_obdobi_choices()

   Funkce která vrací dvou stupňový heslař pro období.

.. py:function:: get_areal_choices()

   Funkce která vrací dvou stupňový heslař pro areál.

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro zobrazení a zpracování editace akce.

   Na začátku se kontroluje, jestli stav není archivovaný.
   Zobrazení se skládá ze 3 formulářů: CreateArchZForm, CreateAkceForm a formsetu pro další vedoucí.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: odeslat(request, ident_cely)

   Funkce pohledu pro zobrazení a zpracování odeslání akce.

   Na začátku se kontroluje, jestli stav není jiný než zapsaný nebo někdo nezměnil stav akce během odesílání.
   Při GET volání se kontrolují vyplněná pole akce a její relace pomocí metody na modelu.
   Po POST volání se volá metoda na modelu pro posun stavu do odeslaného.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: archivovat(request, ident_cely)

   Funkce pohledu pro zobrazení a zpracování archivace akce.

   Na začátku se kontroluje, jestli stav není jiný než odeslaný nebo někdo nezměnil stav akce během archivace.
   Při GET volání se kontrolují vyplněná pole akce a její relace pomocí metody na modelu.
   Po POST volání se volá metoda na modelu pro posun stavu do odeslaného.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: vratit(request, ident_cely)

   Funkce pohledu pro zobrazení a zpracování vrácení stavu akce o jeden krok zpět.

   Na začátku se kontroluje, jestli někdo nezměnil stav akce během vrácení.
   Pro vrácení se používá formulář pro vrácení, který je jednotný napříč aplikací.
   Po POST volání se volá metoda na modelu pro posun stavu zpět.
   Pokud se jedná o projektovou akci, tak se vrací i stav projektu ze stavu uzavřený nebo archivovaný.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: zapsat(request, projekt_ident_cely)

   Funkce pohledu pro vytvoření akce.

   Na začátku se kontroluje, jestli jde o vytvoření projektové nebo samostatné akce a zda je možné projektovou akci vytvořit.
   Zobrazení se skládá ze 3 formulářů: CreateArchZForm, CreateAkceForm a formsetu pro další vedoucí.

   :param request: Popis parametru ``request``.
   :param projekt_ident_cely: Popis parametru ``projekt_ident_cely``.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro zobrazení a zpracování smazání akce.

   Na začátku se kontroluje, jestli někdo nezměnil stav akce během smazání.
   Po POST volání se volá metoda na modelu pro smazání akce.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.

.. py:function:: pripojit_dokument(request, arch_z_ident_cely, proj_ident_cely)

   Funkce pohledu pro připojení dokumentu do akce.

   Funkce volá další funkci pro připojení s parametrem třídou modelu navíc.

   :param request: Popis parametru ``request``.
   :param arch_z_ident_cely: Popis parametru ``arch_z_ident_cely``.
   :param proj_ident_cely: Popis parametru ``proj_ident_cely``.

.. py:function:: odpojit_dokument(request, ident_cely, arch_z_ident_cely)

   Funkce pohledu pro odpojení dokumentu do akce.

   Funkce volá další funkci pro odpojení s parametrem navíc - arch záznamem.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.
   :param arch_z_ident_cely: Popis parametru ``arch_z_ident_cely``.

.. py:function:: post_ajax_get_pians(request)

   Vypada nepouzito check s J. Bartos

   :param request: Popis parametru ``request``.

.. py:function:: post_akce2kat(request)

   Funkce pohledu pro získaní souradnic katastru akce.

   :param request: Popis parametru ``request``.

.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní dátumů pro historii.


   **Argumenty:**

   - ``historie_vazby`` (*HistorieVazby*): model historieVazby dané akce.

   **Návratová hodnota:**

   *historie*: dictionary dátumů k historii.

.. py:function:: get_detail_template_shows(archeologicky_zaznam, dok_jednotky, user, app)

   Funkce pro získaní dictionary uživatelských akcí které mají být zobrazeny uživately.


   **Argumenty:**

   - ``archeologicky_zaznam`` (*ArcheologickyZaznam*): model ArcheologickyZaznam pro který se dané akce počítají.
   - ``dok_jednotky`` (*DokumentacniJednotka*): model DokumentacniJednotka pro který se dané akce počítají.
   - ``user`` (*AuthUser*): uživatel pro kterého se dané akce počítají.
   - ``app`` (*string*): druh archeologického záznamu ro který se dané akce počítají.

   **Návratová hodnota:**

   *historie*: dictionary možností pro zobrazení.

.. py:function:: get_required_fields(zaznam, next)

   Funkce pro získaní dictionary povinných polí podle stavu arch záznamů.


   **Argumenty:**

   - ``zaznam`` (*ArcheologickyZaznam*): model ArcheologickyZaznam pro který se dané pole počítají.
   - ``next`` (*int*): pokud je poskytnuto číslo tak se jedná o povinné pole pro příští stav.

   **Návratová hodnota:**

   *required_fields*: list polí.

.. py:function:: smazat_akce_vedoucí(request, ident_cely, akce_vedouci_id)

   Funkce pohledu pro smazání dalšího vedoucího akce.

   :param request: Popis parametru ``request``.
   :param ident_cely: Popis parametru ``ident_cely``.
   :param akce_vedouci_id: Popis parametru ``akce_vedouci_id``.

.. py:function:: get_dj_form_detail(app, jednotka, jednotky, show, old_adb_post, user)

   Funkce pro získaní dictionary contextu dokumentační jednotky.

   :param app: druh archeologického záznamu ro který se daný context počítá.
   :param jednotka: model DokumentacniJednotka pro který se daný context počítá.
   :param jednotky: list modelů DokumentacniJednotka použit pro správně zobrazení možnosti zmeny typu DJ.
   :param show: dictionary pro zobrazení možnosti uživatele na stránce.
   :param old_adb_post: staré volání CreateADBForm pro správně zobrazení chyb formuláře.
   :param user: Popis parametru ``user``.

   :return: dictionary kontextu DJ pro správné zobrazení stránky.
