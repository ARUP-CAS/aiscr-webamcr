CORE views
==========

Definice views.

Třídy
------

.. py:class:: DownloadFile

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get()


.. py:class:: DownloadThumbnailSmall

   Popis není k dispozici.


.. py:class:: DownloadThumbnailLarge

   Popis není k dispozici.


.. py:class:: UpdateFileView

   Třída pohledu pro zobrazení stránky pro nahrazení souboru.

   **Metody:**

   .. py:method:: get()

   .. py:method:: post()

   .. py:method:: get_context_data()


.. py:class:: UploadFileView

   Třída pohledu pro zobrazení stránky s uploadem souboru.

   **Metody:**

   .. py:method:: get_zaznam()

   .. py:method:: get_context_data()

   .. py:method:: dispatch()

   .. py:method:: post()


.. py:class:: BasePostUploadView

   Základní třída pro zpracování nahrávání souborů.

Poskytuje společnou logiku pro upload nového souboru i nahrazení existujícího souboru.
Tato třída implementuje kompletní workflow pro validaci a zpracování nahrávaných souborů,
včetně kontroly MIME typů, antivirové kontroly a detekce šifrovaných souborů.

Proces nahrávání souboru:
1. Kontrola přítomnosti souboru v requestu
2. Validace MIME typu a detekce šifrování
3. Antivirová kontrola nahrávaného obsahu
4. Předání validovaného souboru potomkům pro konkrétní zpracování

Atributy:
    http_method_names (list): Povolené HTTP metody - pouze POST
    source_url (str): URL zdroje souboru (pokud je specifikována)
    fedora_transaction (FedoraTransaction): Instance transakce pro práci s Fedora repository
    original_filename (str): Původní název nahrávaného souboru

Poznámky:
    - Tato třída je abstraktní a měla by být použita jako základ pro konkrétní implementace
    - Potomci musí implementovat metodu handle_upload()
    - Všechny nahrané soubory procházejí automatickou antivirovou kontrolou
    - Kontroluje se soulad MIME typu se skutečným obsahem souboru

   **Metody:**

   .. py:method:: post()

      Zpracuje POST request s nahrávaným souborem.
      
      Metoda provádí kompletní validaci nahrávaného souboru před jeho uložením:
      - Kontroluje přítomnost souboru v requestu
      - Validuje MIME typ a detekuje šifrované soubory
      - Provádí antivirovou kontrolu obsahu
      - Deleguje finální zpracování na potomky prostřednictvím handle_upload()
      
      Args:
          request (HttpRequest): Django HTTP request objekt obsahující nahrávaný soubor
          *args: Poziční argumenty předané z URL dispatcheru
          **kwargs: Klíčové argumenty z URL patternu (např. ident_cely, typ_vazby)
      
      Returns:
          JsonResponse: JSON odpověď s výsledkem operace:
              - V případě úspěchu: výsledek z handle_upload() metody potomka
              - V případě chyby: {"error": <chybová zpráva>} se status kódem 400/500
      
      Raises:
          Žádné výjimky nejsou vyvolány přímo, všechny chyby jsou vráceny jako JSON response
      
      Response Status Codes:
          200: Soubor byl úspěšně validován a zpracován
          400: Validační chyba (chybějící soubor, šifrovaný, virus, neplatný MIME typ)
          500: Neznámá chyba při zpracování
      
      Příklad:
          V případě detekce viru:
          {"error": "V nahraném souboru byl detekován virus", status: 400}
      
      Poznámky:
          - Metoda nastavuje instanční atributy: source_url, fedora_transaction, original_filename
          - Soubor je automaticky převeden do BytesIO pro další zpracování
          - Všechny chyby jsou logovány s příslušným severity levelem
          - Po antivirové kontrole je soubor vrácen na začátek (seek(0))

   .. py:method:: handle_upload()

      Abstraktní metoda pro implementaci konkrétního zpracování nahraného souboru.
      
      Tato metoda musí být implementována potomky třídy. Je volána z post() metody
      po úspěšné validaci souboru (MIME typ, antivirus). Potomci zde implementují
      specifickou logiku pro nové nahrání nebo aktualizaci existujícího souboru.
      
      Args:
          request (HttpRequest): Django HTTP request objekt s informacemi o uživateli a sessions
          soubor (TemporaryUploadedFile): Nahraný soubor z requestu
          soubor_data (BytesIO): Binární obsah souboru jako BytesIO objekt
          *args: Poziční argumenty z URL dispatcheru
          **kwargs: Klíčové argumenty z URL (např. ident_cely, typ_vazby, file_id)
      
      Returns:
          JsonResponse: JSON odpověď s výsledkem operace nahrání
      
      Raises:
          NotImplementedError: Pokud potomek tuto metodu neimplementuje
      
      Poznámky:
          - V okamžiku volání této metody je soubor již validovaný
          - Fedora transakce je dostupná přes self.fedora_transaction
          - Původní název souboru je dostupný přes self.original_filename
          - URL zdroje je dostupná přes self.source_url


.. py:class:: NewFileUploadView

   Třída pohledu pro nahrání nového souboru k záznamu.

Rozšiřuje BasePostUploadView o specifickou logiku pro upload nových souborů
k různým typům záznamů (projekt, dokument, samostatný nález). Implementuje
kompletní workflow pro vytvoření nového souboru včetně generování názvu,
uložení do Fedora repository a vytvoření záznamu v databázi.

Proces nahrání nového souboru:
1. Kontrola oprávnění uživatele (nebo anonymního přístupu pro projekty)
2. Rozlišení typu záznamu a generování názvu souboru
3. Validace a případná úprava přípony souboru podle MIME typu
4. Odstranění GPS dat z obrázků samostatných nálezů
5. Uložení do Fedora repository
6. Vytvoření záznamu v databázi s metadaty
7. Detekce duplicit podle SHA-512 hashe
8. Zaznamenání události nahrání do historie

URL parametry:
    ident_cely (str): Identifikátor záznamu, ke kterému má být soubor nahrán
    typ_vazby (str): Typ vazby - "projekt", "dokument", "model3d", nebo "pas"

Atributy:
    Dědí všechny atributy z BasePostUploadView

Poznámky:
    - Podporuje anonymní nahrávání souborů pouze pro projekty
    - Automaticky odstraňuje GPS metadata z obrázků u samostatných nálezů
    - Generuje unikátní názvy souborů podle typu záznamu
    - Detekuje duplicity na základě SHA-512 hashe
    - Ukládá referenci na soubor do session pro možnost rollbacku
    - Každé nahrání je logováno do historie s informací o uživateli

   **Metody:**

   .. py:method:: handle_upload()

      Implementuje nahrání nového souboru k záznamu.
      
      Provádí kompletní workflow pro vytvoření nového souboru včetně kontroly oprávnění,
      generování názvu, uložení do repository a vytvoření databázového záznamu.
      Podporuje anonymní upload pro projekty a automaticky zpracovává metadata obrázků.
      
      Args:
          request (HttpRequest): HTTP request s informacemi o uživateli a session
          soubor (TemporaryUploadedFile): Nahraný soubor z requestu
          soubor_data (BytesIO): Binární obsah souboru
          *args: Poziční argumenty z URL
          **kwargs: Obsahuje 'ident_cely' (identifikátor záznamu) a 'typ_vazby' (typ vazby)
      
      Returns:
          JsonResponse: JSON odpověď s výsledkem operace:
              - Při úspěchu (200): {
                  "filename": str,  # Název nahraného souboru
                  "id": int,  # Primary key nového Soubor objektu
                  "duplicate": str (optional),  # Zpráva o duplicitě
                  "file_renamed": str (optional)  # Zpráva o přejmenování
                }
              - Při chybě (400/403/500): {"error": str}
      
      Response Status Codes:
          200: Soubor úspěšně nahrán
          400: Chyba při nahrávání (transakční konflikt, MIME typ, atd.)
          403: Nedostatečná oprávnění nebo překročen limit souborů
          500: Neexistující záznam nebo jiná interní chyba
      
      Raises:
          Žádné výjimky nejsou vyvolány přímo, všechny chyby jsou vráceny jako JSON
      
      Poznámky:
          - Anonymní uživatelé mohou nahrávat pouze k projektům s vlastnictvím v session
          - GPS metadata jsou automaticky odstraňována z obrázků samostatných nálezů
          - Přípona souboru je upravena, pokud neodpovídá MIME typu
          - Soubor je zařazen do Fedora transakce, která je uzavřena po save()
          - Reference na soubor je uložena do session pro možnost smazání při odchodu
          - Při anonymním uploadu je jako autor zaznamenán admin uživatel


.. py:class:: UpdateExistingFileUploadView

   Třída pohledu pro nahrazení existujícího souboru novou verzí.

Rozšiřuje BasePostUploadView o specifickou logiku pro aktualizaci již existujících
souborů. Na rozdíl od NewFileUploadView zachovává původní název souboru (pouze
aktualizuje příponu) a vytváří novou verzi souboru v Fedora repository. Vyžaduje
přihlášení uživatele.

Proces aktualizace souboru:
1. Kontrola oprávnění (vyžaduje LoginRequiredMixin)
2. Validace vazby mezi souborem a záznamem
3. Načtení existujícího Soubor objektu z databáze
4. Validace a případná úprava přípony podle MIME typu
5. Odstranění GPS dat z obrázků u samostatných nálezů
6. Aktualizace binárních dat v Fedora repository
7. Aktualizace metadat v databázi (velikost, SHA-512, MIME typ)
8. Zaznamenání události do historie jako nová verze
9. Detekce duplicit podle SHA-512 hashe

URL parametry:
    typ_vazby (str): Typ vazby - "projekt", "dokument", "model3d", nebo "pas"
    ident_cely (str): Identifikátor záznamu, ke kterému soubor patří
    file_id (int): Primary key existujícího Soubor objektu

Atributy:
    Dědí všechny atributy z BasePostUploadView

Poznámky:
    - VYŽADUJE přihlášeného uživatele (LoginRequiredMixin)
    - Nahrazení souborů NENÍ podporováno pro projekty (pouze dokument, model3d, pas)
    - Kontroluje oprávnění pomocí check_permissions s akcemi soubor_nahradit_*
    - Zachovává základní název souboru, aktualizuje pouze příponu
    - Aktualizuje repository_uuid existujícího souboru, nevytváří nový
    - Automaticky odstraňuje GPS metadata z obrázků samostatných nálezů
    - Validuje vazbu mezi souborem a záznamem před aktualizací
    - Historie zaznamenává aktualizaci jako novou verzi, ne nový soubor
    - Detekuje duplicity i po aktualizaci

   **Metody:**

   .. py:method:: handle_upload()

      Implementuje aktualizaci existujícího souboru novou verzí.
      
      Provádí kompletní workflow pro nahrazení obsahu existujícího souboru včetně
      validace vazeb, aktualizace v repository a databázi. Zachovává původní název
      souboru (s možnou úpravou přípony) a vytváří novou verzi v historii.
      
      Args:
          request (HttpRequest): HTTP request s informacemi o přihlášeném uživateli
          soubor (TemporaryUploadedFile): Nový nahraný soubor z requestu
          soubor_data (BytesIO): Binární obsah nového souboru
          *args: Poziční argumenty z URL
          **kwargs: Obsahuje 'typ_vazby', 'ident_cely' a 'file_id'
      
      Returns:
          JsonResponse: JSON odpověď s výsledkem operace:
              - Při úspěchu (200): {
                  "filename": str,  # Aktuální název souboru
                  "id": int,  # Primary key aktualizovaného Soubor objektu
                  "duplicate": str (optional),  # Zpráva o duplicitě
                  "file_renamed": str (optional)  # Zpráva o změně přípony
                }
              - Při chybě (400/500): {"error": str}
      
      Response Status Codes:
          200: Soubor úspěšně aktualizován
          400: Chyba vazby, transakční konflikt, MIME typ nebo neplatný typ_vazby
          403: Nedostatečná oprávnění k nahrazení souboru
          500: Chybějící vazba nebo jiná interní chyba
      
      Raises:
          Http404: Pokud soubor s daným file_id neexistuje (get_object_or_404)
          ZaznamSouborNotmatching: Pokud soubor nepatří k danému záznamu
      
      Poznámky:
          - Kontroluje oprávnění před nahrazením souboru
          - Nahrazení není podporováno pro projekty
          - Vyžaduje platnou vazbu mezi souborem a záznamem
          - Zachovává základní část názvu, aktualizuje pouze příponu
          - GPS metadata jsou odstraňována pouze u obrázků samostatných nálezů
          - Přípona je upravena podle MIME typu nového souboru
          - Historie zaznamenává jako 'nahrání nové verze', ne nový soubor
          - Soubor musí mít repository_uuid pro úspěšnou aktualizaci
          - Fedora transakce je automaticky uzavřena nebo rollbackována


.. py:class:: ExportMixinDate

   Mixin pro získaní názvu exportovaného souboru.

   **Metody:**

   .. py:method:: get_export_filename()


.. py:class:: PermissionFilterMixin

   Popis není k dispozici.

   **Metody:**

   .. py:method:: check_filter_permission()

   .. py:method:: filter_by_permission()

   .. py:method:: add_status_lookup()

   .. py:method:: add_ownership_lookup()

   .. py:method:: add_accessibility_lookup()


.. py:class:: SearchListView

   Třída pohledu pro tabulky záznamů, která je použita jako základ pro jednotlivé pohledy.

   **Metody:**

   .. py:method:: create_export()

   .. py:method:: init_translations()

   .. py:method:: get_paginate_by()

   .. py:method:: get_context_data()

   .. py:method:: get_queryset()

   .. py:method:: get()


.. py:class:: StahnoutDataHistorickaView

   Třída pohledu pro stažení historické verze souboru nebo metadat z Fedory

   **Metody:**

   .. py:method:: get()


.. py:class:: CheckUserAuthentication

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get()


.. py:class:: ReadTempValueView

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get()


.. py:class:: DeleteTempValueView

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get()


.. py:class:: AbortDownloadUpdateTempValueView

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get()


.. py:class:: RosettaFileLevelMixinWithBackup

   Třída podledu pro práci s prekladmi doplnena o backup osubory.

   **Metody:**

   .. py:method:: po_file_path()

      Based on the url kwargs, infer and return the path to the .po file to
      be shown/updated.
      
      Throw a 404 if a file isn't found.


.. py:class:: TranslationImportView

   Třída pohledu pro import prekladových souboru.

   **Metody:**

   .. py:method:: form_valid()

   .. py:method:: get_context_data()

   .. py:method:: handle_uploaded_file()


.. py:class:: TranslationFileListWithBackupView

   Třída pohledu pro zobrazení prekladových souboru s backup souborami.

   **Metody:**

   .. py:method:: get_context_data()


.. py:class:: TranslationFormWithBackupView

   Třída pohledu pro zobrazení formulaře s prekladmi i pro backup soubory

   **Metody:**

   .. py:method:: get_context_data()


.. py:class:: TranslationFileDownloadBackup

   Třída pohledu pro stahování prekladových souboru is backup souborami.

   **Metody:**

   .. py:method:: get()


.. py:class:: TranslationFileSmazatBackup

   Třída pohledu pro smazání backup prekladových souboru.

   **Metody:**

   .. py:method:: get()

   .. py:method:: post()


.. py:class:: PrometheusMetricsView

   Třída pohledu pro zobrazení prometheus metrík doplňena o mixin pro filtrování IP adres.

   **Metody:**

   .. py:method:: get()


.. py:class:: ApplicationRestartView

   Třída pohledu pro restartovani uwsgi aplikace.

   **Metody:**

   .. py:method:: post()


.. py:class:: DataImportProgress

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get()


.. py:class:: DataImportStop

   Popis není k dispozici.

   **Metody:**

   .. py:method:: get()


Funkce
------

.. py:function:: index(request)

   Funkce podledu pro zobrazení hlavní stránky.

.. py:function:: delete_file_DZ(request, typ_vazby, ident_cely, pk)

   Funkce pohledu pro smazání souboru z dropzone. Funkce maže jak záznam v DB tak i soubor na disku.

.. py:function:: delete_file(request, typ_vazby, ident_cely, pk)

   Funkce pohledu pro smazání souboru. Funkce maže jak záznam v DB tak i soubor na disku.

.. py:function:: get_finds_soubor_name(find, filename, add_to_index)

   Funkce pro získaní jména souboru pro samostatný nález.

.. py:function:: get_projekt_soubor_name(projekt, file_name)

   Funkce pro získaní jména souboru pro projekt.

.. py:function:: check_stav_changed(request, zaznam)

   Funkce pro oveření jestli se zmenil stav záznamu pri uložení formuláře oproti jeho načtení.

.. py:function:: redirect_ident_view(request, ident_cely)

   Funkce pro získaní správneho redirectu na záznam podle ident%cely záznamu.

.. py:function:: prolong_session(request)

   Funkce pohledu pro prodloužení prihlášení.

.. py:function:: post_ajax_get_pas_and_pian_limit(request)

   Funkce pohledu pro získaní heatmapy.

.. py:function:: check_soubor_vazba(typ_vazby, ident, id_zaznamu)

   Popis není k dispozici.
