CORE views
==========

Definice views.

Třídy
------

.. py:class:: DownloadFile

   Popis není k dispozici.

   **Metody:**

   .. py:method:: _preprocess_image()

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

   Abstraktní třída pro zpracování nahrávání souborů.

   Poskytuje společnou logiku pro upload nového souboru i nahrazení existujícího souboru.
   Implementuje kompletní workflow pro validaci nahrávaných souborů včetně kontroly MIME typů,
   antivirové kontroly a detekce šifrovaných souborů. Potomci musí implementovat metodu
   handle_upload() pro specifické zpracování.


   **Popis procesu:**

   1. Kontrola přítomnosti souboru v requestu
   2. Validace MIME typu a detekce šifrování
   3. Antivirová kontrola nahrávaného obsahu
   4. Předání validovaného souboru potomkům pro konkrétní zpracování

   **Atributy:**

   - ``http_method_names`` (*list*): Povolené HTTP metody - pouze POST
   - ``source_url`` (*str*): URL zdroje souboru (pokud je specifikována)
   - ``fedora_transaction`` (*FedoraTransaction*): Instance transakce pro práci s Fedora repository
   - ``original_filename`` (*str*): Původní název nahrávaného souboru

   **Metody:**

   .. py:method:: post()

      Zpracuje POST request s nahrávaným souborem.

      Metoda provádí kompletní validaci nahrávaného souboru před jeho uložením:
      - Kontroluje přítomnost souboru v requestu
      - Validuje MIME typ a detekuje šifrované soubory
      - Provádí antivirovou kontrolu obsahu
      - Deleguje finální zpracování na potomky prostřednictvím handle_upload()


      **Argumenty:**

      - ``request`` (*HttpRequest*): Django HTTP request objekt obsahující nahrávaný soubor
      - ``*args``: Poziční argumenty předané z URL dispatcheru
      - ``**kwargs``: Klíčové argumenty z URL patternu (např. ident_cely, typ_vazby)

      **Návratová hodnota:**

      *JsonResponse*: JSON odpověď s výsledkem operace

      **Stavové kódy odpovědi:**

      - ``200``: Soubor byl úspěšně validován a zpracován
      - ``400``: Validační chyba (chybějící soubor, šifrovaný, virus, neplatný MIME typ)
      - ``500``: Neznámá chyba při zpracování

   .. py:method:: handle_upload()

      Abstraktní metoda pro implementaci konkrétního zpracování nahraného souboru.

      Tato metoda musí být implementována potomky třídy. Je volána z post() metody
      po úspěšné validaci souboru (MIME typ, antivirus). Potomci zde implementují
      specifickou logiku pro nové nahrání nebo aktualizaci existujícího souboru.


      **Argumenty:**

      - ``request`` (*HttpRequest*): Django HTTP request objekt s informacemi o uživateli a sessions
      - ``soubor`` (*TemporaryUploadedFile*): Nahraný soubor z requestu
      - ``soubor_data`` (*BytesIO*): Binární obsah souboru jako BytesIO objekt
      - ``*args``: Poziční argumenty z URL dispatcheru
      - ``**kwargs``: Klíčové argumenty z URL (např. ident_cely, typ_vazby, file_id)

      **Návratová hodnota:**

      *JsonResponse*: JSON odpověď s výsledkem operace nahrání

      **Výjimky:**

      *NotImplementedError*: Pokud potomek tuto metodu neimplementuje

   .. py:method:: _append_duplicate_message()

      Přidá informaci o duplicitním souboru do odpovědi.

      Kontroluje, zda v systému již existuje soubor se stejným SHA-512 hashem.
      Pokud ano, přidá do response_data varovnou zprávu s informací o duplicitě
      včetně identifikátoru záznamu, ke kterému je duplicitní soubor připojen.


      **Argumenty:**

      - ``response_data`` (*dict*): Slovník s daty odpovědi, do kterého bude přidána zpráva
      - ``duplikat`` (*QuerySet*): QuerySet s duplicitními soubory (Soubor objekty)

      **Návratová hodnota:**

      *dict*: Upravený response_data slovník s přidanou duplicitní zprávou.
      Pokud není nalezen žádný duplikát, vrací nezměněný slovník.

      **Klíče odpovědi:**


      **duplicate (tuple): Tuple obsahující zprávu o duplicitě ve formátu:**


   .. py:method:: _append_rename_message()

      Přidá informaci o přejmenování souboru do odpovědi.

      Pokud byl soubor během uploadu přejmenován (typicky kvůli úpravě přípony
      pro soulad s MIME typem), přidá do response_data informační zprávu.


      **Argumenty:**

      - ``response_data`` (*dict*): Slovník s daty odpovědi, do kterého bude přidána zpráva
      - ``renamed`` (*bool*): True pokud došlo k přejmenování, False jinak
      - ``new_name`` (*str*): Nový název souboru po přejmenování

      **Návratová hodnota:**

      *dict*: Upravený response_data slovník s přidanou zprávou o přejmenování.
      Pokud nedošlo k přejmenování (renamed=False), vrací nezměněný slovník.

      **Klíče odpovědi:**


      **file_renamed (tuple): Tuple obsahující zprávu o přejmenování ve formátu:**


   .. py:method:: _unknown_error_response()

      Vrátí JSON odpověď s chybovou zprávou a HTTP status 500 pro neočekávané chyby
      při zpracování souboru, které nejsou pokryty specifickými error handlery.


      **Návratová hodnota:**

      *JsonResponse*: JSON odpověď s chybovou zprávou a HTTP status 500


.. py:class:: NewFileUploadView

   Pohled pro nahrání nového souboru k záznamu (projekt, dokument, samostatný nález).


   **Popis procesu:**

   1. Kontrola oprávnění uživatele (nebo anonymního přístupu pro projekty)
   2. Rozlišení typu záznamu a generování názvu souboru
   3. Validace a případná úprava přípony souboru podle MIME typu
   4. Odstranění GPS dat z obrázků samostatných nálezů
   5. Uložení do Fedora repository
   6. Vytvoření záznamu v databázi s metadaty
   7. Detekce duplicit podle SHA-512 hashe
   8. Zaznamenání události nahrání do historie

   **URL parametry:**

   - ``ident_cely`` (*str*): Identifikátor záznamu, ke kterému má být soubor nahrán
   - ``typ_vazby`` (*str*): Typ vazby - "projekt", "dokument", "model3d", nebo "pas"

   **Metody:**

   .. py:method:: handle_upload()

      Implementuje nahrání nového souboru k záznamu.

      Provádí kompletní workflow pro vytvoření nového souboru včetně kontroly oprávnění,
      generování názvu, uložení do repository a vytvoření databázového záznamu.
      Podporuje anonymní upload pro oznámení a automaticky zpracovává metadata obrázků.


      **Argumenty:**

      - ``request`` (*HttpRequest*): HTTP request s informacemi o uživateli a session
      - ``soubor`` (*TemporaryUploadedFile*): Nahraný soubor z requestu
      - ``soubor_data`` (*BytesIO*): Binární obsah souboru
      - ``*args``: Poziční argumenty z URL
      - ``**kwargs``: Obsahuje 'ident_cely' (identifikátor záznamu) a 'typ_vazby' (typ vazby)

      **Návratová hodnota:**

      *JsonResponse*: JSON odpověď s výsledkem operace

      **Stavové kódy odpovědi:**

      - ``200``: Soubor úspěšně nahrán
      - ``400``: Chyba při nahrávání (transakční konflikt, MIME typ, atd.)
      - ``403``: Nedostatečná oprávnění nebo překročen limit souborů
      - ``500``: Neexistující záznam nebo jiná interní chyba

   .. py:method:: _resolve_object_and_name()

      Rozliší typ záznamu, zkontroluje oprávnění a vygeneruje standardizovaný název souboru.

      Na základě ident_cely a typ_vazby načte odpovídající záznam z databáze,
      ověří konzistenci mezi typ_vazby a skutečným typem objektu, zkontroluje
      oprávnění uživatele k nahrání souboru a vygeneruje standardizovaný název
      souboru podle příslušných konvencí.


      **Argumenty:**

      - ``request`` (*HttpRequest*): HTTP request s informacemi o uživateli
      - ``ident_cely`` (*str*): Úplný identifikátor záznamu (např. "C-202400001")
      - ``filename`` (*str*): Původní název nahrávaného souboru
      - ``typ_vazby`` (*str*): Typ vazby - "projekt", "dokument", "model3d", nebo "pas"

      **Návratová hodnota:**


      **tuple | JsonResponse: Při úspěchu vrací tuple (objekt, new_name):**

      - objekt (Projekt|Dokument|SamostatnyNalez): Instance nalezeného záznamu
      - new_name (str): Vygenerovaný standardizovaný název souboru
        Při chybě vrací JsonResponse s chybovou zprávou a status kódem 403/500


.. py:class:: UpdateExistingFileUploadView

   Pohled pro nahrazení existujícího souboru novou verzí.


   **Rozdíly oproti NewFileUploadView:**

   - Vždy vyžaduje přihlášení uživatele (LoginRequiredMixin)
   - Nepodporuje projekty (pouze dokument, model3d, pas)
   - Zachovává původní název souboru, aktualizuje pouze příponu
   - Aktualizuje existující záznam v Fedora repository místo vytváření nového
   - V historii zaznamenává jako novou verzi, ne nový soubor

   **URL parametry:**

   - ``typ_vazby`` (*str*): Typ vazby - "dokument", "model3d", nebo "pas"
   - ``ident_cely`` (*str*): Identifikátor záznamu, ke kterému soubor patří
   - ``file_id`` (*int*): Primary key existujícího Soubor objektu

   **Metody:**

   .. py:method:: handle_upload()

      Implementuje aktualizaci existujícího souboru novou verzí.

      Provádí kompletní workflow pro nahrazení obsahu existujícího souboru včetně
      validace vazeb, aktualizace v repository a databázi. Zachovává původní název
      souboru (s možnou úpravou přípony) a vytváří novou verzi v historii.


      **Argumenty:**

      - ``request`` (*HttpRequest*): HTTP request s informacemi o přihlášeném uživateli
      - ``soubor`` (*TemporaryUploadedFile*): Nový nahraný soubor z requestu
      - ``soubor_data`` (*BytesIO*): Binární obsah nového souboru
      - ``*args``: Poziční argumenty z URL
      - ``**kwargs``: Obsahuje 'typ_vazby', 'ident_cely' a 'file_id'

      **Návratová hodnota:**

      *JsonResponse*: JSON odpověď s výsledkem operace

      **Stavové kódy odpovědi:**

      - ``200``: Soubor úspěšně aktualizován
      - ``400``: Chyba vazby, transakční konflikt, MIME typ nebo neplatný typ_vazby
      - ``403``: Nedostatečná oprávnění k nahrazení souboru
      - ``500``: Chybějící vazba nebo jiná interní chyba

      **Výjimky:**

      *Http404*: Pokud soubor s daným file_id neexistuje (get_object_or_404)
      *ZaznamSouborNotmatching*: Pokud soubor nepatří k danému záznamu

   .. py:method:: _check_update_permissions()

      Zkontroluje platnost typu vazby a oprávnění uživatele k nahrazení souboru.

      Na základě typ_vazby ověří, zda je nahrazení souboru povoleno pro daný typ
      záznamu, a zkontroluje oprávnění uživatele pomocí check_permissions.


      **Argumenty:**

      - ``request`` (*HttpRequest*): HTTP request s informacemi o uživateli
      - ``typ_vazby`` (*str*): Typ vazby - "dokument", "model3d", nebo "pas"
      - ``ident_cely`` (*str*): Úplný identifikátor záznamu
      - ``file_id`` (*int*): Primary key existujícího souboru

      **Návratová hodnota:**

      *bool | JsonResponse*: True pokud je vše v pořádku,
      JsonResponse s chybovou zprávou při problému


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

   .. py:method:: _get_sort_params()

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
