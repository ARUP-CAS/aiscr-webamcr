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

   .. py:method:: check_locality_arch_z_conflict()

   .. py:method:: get_context_data()

      Metoda pro získaní contextu akci pro template.


.. py:class:: ArcheologickyZaznamDetailView

   Třída pohledu pro zobrazení detailu akce.

   **Metody:**

   .. py:method:: get_archeologicky_zaznam()

      Metoda pro získani záznamu akce z db podle ident_cely.

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde.


.. py:class:: DokumentacniJednotkaRelatedUpdateView

   Třida, která se dedí a která obsahuje metody pro získaní relací DJ.

   **Metody:**

   .. py:method:: dispatch()

   .. py:method:: get_dokumentacni_jednotka()

      Metoda pro získani záznamu DJ z db podle ident_cely.

   .. py:method:: get_context_data()

      Metoda pro získaní context dat DJ navíc oproti přepisované metóde, záznam DJ.

   .. py:method:: get()


.. py:class:: DokumentacniJednotkaCreateView

   Třída pohledu pro vytvoření dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření DJ.

   .. py:method:: get()


.. py:class:: DokumentacniJednotkaUpdateView

   Třída pohledu pro zobrazení detailu dokumentační jednotky s možností její úpravy.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat DJ navíc oproti přepisované metóde, pro zobrazení správneho detailu.


.. py:class:: KomponentaCreateView

   Třida pohledu pro vytvoření komponenty dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář na vytvoření komponenty.


.. py:class:: KomponentaUpdateView

   Třida pohledu pro editaci komponenty dokumentační jednotky.

   **Metody:**

   .. py:method:: dispatch()

   .. py:method:: get_komponenta()

      Metoda pro získani záznamu komponenty z db podle ident_cely.

   .. py:method:: get_dokumentacni_jednotka()

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro úpravu komponenty,
      případně data poslaného chybného formuláře.


.. py:class:: PianCreateView

   Třida pohledu pro vytvoření PIANu dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření PIANu.

   .. py:method:: get()


.. py:class:: PianUpdateView

   Třida pohledu pro editaci PIANu dokumentační jednotky.

   **Metody:**

   .. py:method:: dispatch()

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro editaci PIANu.

   .. py:method:: get()


.. py:class:: AdbCreateView

   Třida pohledu pro vytvoření PIANu dokumentační jednotky.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní context dat navíc oproti přepisované metóde, formulář pro vytvoření ADB.


.. py:class:: GetAkceOtherKatastrView

   Popis není k dispozici.

   **Metody:**

   .. py:method:: post()

      Trida pohledu pro získaní souradnic dalších katastrů akce.


.. py:class:: AkceIndexView

   Třida pohledu pro zobrazení domovské stránky akcií s navigačními možnostmi.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní kontextu podlehu.


.. py:class:: AkceListView

   Třida pohledu pro zobrazení listu/tabulky s akcemi.

   **Metody:**

   .. py:method:: init_translations()

   .. py:method:: rename_field_for_ordering()

   .. py:method:: get_queryset()


.. py:class:: ProjektAkceChange

   Třida pohledu pro zmenu projektové akce na samostatnou.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní kontextu podlehu.

   .. py:method:: get()

      Metoda pro vrácení stránky pri voláni GET.

   .. py:method:: post()

      Metoda po potvrzení zmeny akce na samostatnou.
      Pri zavolíní se kontroluje, že akce nebyla změnena v mezičase potvrzení.
      Po úspešné kontrole se odebere projekt, nastaví typ akce na samostatnú a nastaví nový ident celý.
      Celá událost je zapsaná do historie.
      Uživatel je presmerován na detail akce.


.. py:class:: SamostatnaAkceChange

   Třida pohledu pro zmenu samostatní akce na projektovou.

   **Metody:**

   .. py:method:: get_context_data()

      Metoda pro získaní kontextu podlehu.

   .. py:method:: get()

      Metoda pro vrácení stránky pri voláni GET s formulářem pro výber projektu.

   .. py:method:: post()

      Metoda po potvrzení zmeny akce na projektovou.
      Pri zavolíní se kontroluje, že akce nebyla změnena v mezičase potvrzení.
      Po úspešné kontrole se napojí projekt, nastaví typ akce na projektovou a nastaví nový ident celý.
      Celá událost je zapsaná do historie.
      Uživatel je presmerován na detail akce.


.. py:class:: ArchZAutocomplete

   Třida pohledu pro vrácení výsledku pro autocomplete arch záznamů.

   **Metody:**

   .. py:method:: get_result_label()

   .. py:method:: get_queryset()


.. py:class:: ArchZTableRowView

   Třida pohledu pro vrácení řádku tabulky s arch záznamem.

   **Metody:**

   .. py:method:: get()


Funkce
------

.. py:function:: get_obdobi_choices()

   Funkce která vrací dvou stupňový heslař pro období.

.. py:function:: get_areal_choices()

   Funkce která vrací dvou stupňový heslař pro areál.

.. py:function:: edit(request, ident_cely)

   Funkce pohledu pro zobrazení a spracováni editace akce.
   Na začátku se kontroluje jestli stav není archivovaný.
   Zobrazení pozostáva ze 3 formulářů: CreateArchZForm, CreateAkceForm, formset na další vedoucí.

.. py:function:: odeslat(request, ident_cely)

   Funkce pohledu pro zobrazení a spracováni odeslání akce.
   Na začátku se kontroluje jestli stav není jiný než zapsaný nebo nekdo nezmenil stav akce během odesílaní.
   Při get volání se kontrolují vyplnená pole akce a její relaci pomoci metody na modelu.
   Po post volání se volá metoda na modelu pro posun stavu do odeslaná.

.. py:function:: archivovat(request, ident_cely)

   Funkce pohledu pro zobrazení a spracováni archivace akce.
   Na začátku se kontroluje jestli stav není jiný než odeslaný nebo nekdo nezmenil stav akce během archivace.
   Při get volání se kontrolují vyplnená pole akce a její relaci pomoci metody na modelu.
   Po post volání se volá metoda na modelu pro posun stavu do odeslaná.

.. py:function:: vratit(request, ident_cely)

   Funkce pohledu pro zobrazení a spracováni vrácení stacu akce o jedno naspátek.
   Na začátku se kontroluje jestli nekdo nezmenil stav akce během vrácení.
   Pro vrácení se používa formulář pro vrácení, který je jednotný napríč aplikací.
   Po post volání se volá metoda na modelu pro posun stavu naspátek.
   Pokud se jedná o projektovou akci, tak se vrací i stav projektu ze stavu uzavřený nebo archivovaný.

.. py:function:: zapsat(request, projekt_ident_cely)

   Funkce pohledu pro vytvoření akce.
   Na začátku se kontroluje jestli jde o vytvoření projektové nebo samostatné akce a případně zda je možné vytvořit projektovou akci.
   Zobrazení pozostáva ze 3 formulářů: CreateArchZForm, CreateAkceForm, formset na další vedoucí.

.. py:function:: smazat(request, ident_cely)

   Funkce pohledu pro zobrazení a spracováni smazání akce.
   Na začátku se kontroluje jestli nekdo nezmenil stav akce během smazání.
   Po post volání se volá metoda na modelu pro smazání akce.

.. py:function:: pripojit_dokument(request, arch_z_ident_cely, proj_ident_cely)

   Funkce pohledu pro připojení dokumentu do akce.
   Funkce volá další funkci pro připojení s parametrem třídou modelu navíc.

.. py:function:: odpojit_dokument(request, ident_cely, arch_z_ident_cely)

   Funkce pohledu pro odpojení dokumentu do akce.
   Funkce volá další funkci pro odpojení s parametrem navíc - arch záznamem.

.. py:function:: post_ajax_get_pians(request)

   Vypada nepouzito check s J. Bartos

.. py:function:: post_akce2kat(request)

   Funkce pohledu pro získaní souradnic katastru akce.

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

.. py:function:: get_dj_form_detail(app, jednotka, jednotky, show, old_adb_post, user)

   Funkce pro získaní dictionary contextu dokumentační jednotky.


   **Argumenty:**

   - ``app`` (*string*): druh archeologického záznamu ro který se daný context počítá.
   - ``jednotka`` (*DokumentacniJednotka*): model DokumentacniJednotka pro který se daný context počítá.
   - ``jednotky`` (*DokumentacniJednotka*): list modelů DokumentacniJednotka použit pro správně zobrazení možnosti zmeny typu DJ.
   - ``show`` (*dictionary*): dictionary pro zobrazení možnosti uživatele na stránce.
   - ``old_adb_post`` (*CreateADBForm*): staré volání CreateADBForm pro správně zobrazení chyb formuláře.

   **Návratová hodnota:**

   *dj_form_detail*: dictionary kontextu DJ pro správné zobrazení stránky.
