CORE views
==========

Definice views.

Třídy
------

.. py:class:: DownloadFile

   Implementuje komponentu ``DownloadFile`` v rámci aplikace.

   **Metody:**

   .. py:method:: _preprocess_image()

      Připraví binární obsah obrázku před odesláním klientovi.

      :param file_content: Obsah souboru načtený z repository.
      :return: Upravený nebo původní obsah obrázku.

   .. py:method:: get()

      Vrátí požadovaný soubor nebo jeho náhled po ověření vazby k záznamu.

      :param request: Django HTTP požadavek.
      :param typ_vazby: Typ vazby souboru na doménový záznam.
      :param ident_cely: Identifikátor záznamu, ke kterému soubor patří.
      :param pk: Primární klíč souboru.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Odpověď s obsahem souboru, náhledem nebo redirect při chybě vazby.


.. py:class:: DownloadThumbnailSmall

   Implementuje komponentu ``DownloadThumbnailSmall`` v rámci aplikace.


.. py:class:: DownloadThumbnailLarge

   Implementuje komponentu ``DownloadThumbnailLarge`` v rámci aplikace.


.. py:class:: UpdateFileView

   Třída pohledu pro zobrazení stránky pro nahrazení souboru.

   **Metody:**

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      :param request: Django HTTP požadavek.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

      :param request: Django HTTP požadavek.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: UploadFileView

   Třída pohledu pro zobrazení stránky s uploadem souboru.

   **Metody:**

   .. py:method:: get_zaznam()

      Načte doménový záznam, ke kterému se budou soubory nahrávat.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: dispatch()

      Provádí operaci dispatch.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

      :param request: Django HTTP požadavek.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


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

      Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

      :param request: Django HTTP požadavek.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: handle_upload()

      Abstraktní metoda pro implementaci konkrétního zpracování nahraného souboru.

      Potomci implementují vlastní workflow nahrání po úspěšné validaci souboru.

      :param request: Django HTTP požadavek s kontextem uživatele a session.
      :param soubor: Nahraný soubor z requestu připravený k uložení.
      :param soubor_data: Binární obsah souboru v objektu ``BytesIO``.
      :param args: Dodatečné poziční argumenty z URL dispatcheru.
      :param kwargs: Dodatečné klíčové argumenty z URL (např. ``ident_cely``).
      :raises NotImplementedError: Pokud potomek metodu nepřepíše.

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

      **Klíče odpovědi:**

      - ``duplicate`` (*tuple*): Tuple obsahující zprávu o duplicitě ve formátu:

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

      **Klíče odpovědi:**

      - ``file_renamed`` (*tuple*): Tuple obsahující zprávu o přejmenování ve formátu:

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

      Provádí workflow vytvoření nového souboru včetně kontroly oprávnění,
      generování názvu, uložení do repository a založení databázového záznamu.

      :param request: HTTP request s informacemi o uživateli a session.
      :param soubor: Nahraný soubor z requestu.
      :param soubor_data: Binární obsah souboru.
      :param args: Dodatečné poziční argumenty z URL.
      :param kwargs: Klíčové argumenty včetně ``ident_cely`` a ``typ_vazby``.

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

      *tuple | JsonResponse*: Při úspěchu vrací tuple (objekt, new_name):


.. py:class:: UpdateExistingFileUploadView

   Pohled pro nahrazení existujícího souboru novou verzí.

   Rozdíly oproti NewFileUploadView:
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

      Nahrazuje obsah existujícího souboru, zachovává název (s případnou úpravou
      přípony), aktualizuje repository a zapisuje novou verzi do historie.

      :param request: HTTP request s informacemi o přihlášeném uživateli.
      :param soubor: Nový nahraný soubor z requestu.
      :param soubor_data: Binární obsah nového souboru.
      :param args: Dodatečné poziční argumenty z URL.
      :param kwargs: Klíčové argumenty včetně ``typ_vazby``, ``ident_cely`` a ``file_id``.
      :raises Http404: Pokud soubor s daným ``file_id`` neexistuje.
      :raises ZaznamSouborNotmatching: Pokud soubor nepatří k uvedenému záznamu.

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


.. py:class:: ExportMixinDate

   Mixin pro získaní názvu exportovaného souboru.

   **Metody:**

   .. py:method:: get_export_filename()

      Sestaví název exportního souboru s časovým razítkem.

      :param export_format: Cílový formát exportu (např. ``csv``, ``xlsx``).
      :param export_name: Volitelný základ názvu; pokud není zadán, použije ``self.export_name``.


.. py:class:: PermissionFilterMixin

   Implementuje komponentu ``PermissionFilterMixin`` v rámci aplikace.

   **Metody:**

   .. py:method:: check_filter_permission()

      Ověří filter permission.

      :param qs: Vstupní hodnota ``qs`` pro danou operaci.
      :param action: Vstupní hodnota ``action`` pro danou operaci.

   .. py:method:: filter_by_permission()

      Filtruje by permission.

      :param qs: Vstupní hodnota ``qs`` pro danou operaci.
      :param permission: Vstupní hodnota ``permission`` pro danou operaci.

   .. py:method:: add_status_lookup()

      Provádí operaci add status lookup.

      :param permission: Vstupní hodnota ``permission`` pro danou operaci.

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Vstupní hodnota ``ownership`` pro danou operaci.
      :param qs: Vstupní hodnota ``qs`` pro danou operaci.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Vstupní hodnota ``permission`` pro danou operaci.
      :param qs: Vstupní hodnota ``qs`` pro danou operaci.


.. py:class:: SearchListView

   Třída pohledu pro tabulky záznamů, která je použita jako základ pro jednotlivé pohledy.

   **Metody:**

   .. py:method:: create_export()

      Vytvoří export výsledků vyhledávání v požadovaném formátu.

      :param export_format: Vstupní hodnota ``export_format`` pro danou operaci.

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: _get_sort_params()

      Vrací sort params.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_queryset()

      Vrací queryset výsledků vyhledávání podle zadaných filtrů.

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      :param request: Django HTTP požadavek.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: StahnoutDataHistorickaView

   Třída pohledu pro stažení historické verze souboru nebo metadat z Fedory

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param model_name: Vstupní hodnota ``model_name`` pro danou operaci.
      :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.
      :param timestamp: Vstupní hodnota ``timestamp`` pro danou operaci.


.. py:class:: CheckUserAuthentication

   Implementuje komponentu ``CheckUserAuthentication`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      :param request: Django HTTP požadavek.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ReadTempValueView

   Implementuje komponentu ``ReadTempValueView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.


.. py:class:: DeleteTempValueView

   Implementuje komponentu ``DeleteTempValueView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.


.. py:class:: AbortDownloadUpdateTempValueView

   Implementuje komponentu ``AbortDownloadUpdateTempValueView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.


.. py:class:: RosettaFileLevelMixinWithBackup

   Třída podledu pro práci s prekladmi doplnena o backup osubory.

   **Metody:**

   .. py:method:: po_file_path()

      Podle URL parametrů `kwargs` odvodí a vrátí cestu k `.po` souboru,

      který se má zobrazit nebo upravit.

      Pokud soubor neexistuje, vyvolá chybu 404.


.. py:class:: TranslationImportView

   Třída pohledu pro import překladových souborů.

   **Metody:**

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Vstupní hodnota ``form`` pro danou operaci.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: handle_uploaded_file()

      Zpracuje uploaded file.

      :param f: Vstupní hodnota ``f`` pro danou operaci.


.. py:class:: TranslationFileListWithBackupView

   Třída pohledu pro zobrazení prekladových souboru s backup souborami.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: TranslationFormWithBackupView

   Třída pohledu pro zobrazení formulaře s prekladmi i pro backup soubory

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: TranslationFileDownloadBackup

   Třída pohledu pro stahování prekladových souboru is backup souborami.

   **Metody:**

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      :param request: Django HTTP požadavek.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: TranslationFileSmazatBackup

   Třída pohledu pro smazání backup prekladových souboru.

   **Metody:**

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      :param request: Django HTTP požadavek.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: post()

      Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

      :param request: Django HTTP požadavek.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: PrometheusMetricsView

   Třída pohledu pro zobrazení prometheus metrík doplňena o mixin pro filtrování IP adres.

   **Metody:**

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      :param request: Django HTTP požadavek.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ApplicationRestartView

   Třída pohledu pro restartovani uwsgi aplikace.

   **Metody:**

   .. py:method:: post()

      Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

      :param request: Django HTTP požadavek.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DataImportProgress

   Implementuje komponentu ``DataImportProgress`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DataImportStop

   Implementuje komponentu ``DataImportStop`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: DataImportStart

   Implementuje komponentu ``DataImportStart`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


Funkce
------

.. py:function:: index(request)

   Zobrazí hlavní stránku aplikace po přihlášení uživatele.

   :param request: HTTP požadavek aktuálního uživatele.

.. py:function:: delete_file_DZ(request, typ_vazby, ident_cely, pk)

   Smaže soubor nahraný přes dropzone včetně záznamu v databázi i ve Fedora úložišti.

   :param request: HTTP požadavek obsahující session identifikátor dropzone uploadu.
   :param typ_vazby: Typ vazby souboru na doménový objekt (např. dokument, projekt, PAS).
   :param ident_cely: Identifikátor záznamu, ke kterému je soubor navázán.
   :param pk: Primární klíč mazaného souboru.

.. py:function:: delete_file(request, typ_vazby, ident_cely, pk)

   Smaže existující soubor, jeho databázový záznam i binární obsah v repozitáři.

   :param request: HTTP požadavek s metodou GET/POST a případnou návratovou URL.
   :param typ_vazby: Typ vazby souboru na navázaný doménový objekt.
   :param ident_cely: Identifikátor záznamu, u kterého se soubor odstraňuje.
   :param pk: Primární klíč mazaného souboru.

.. py:function:: get_finds_soubor_name(find, filename, add_to_index)

   Funkce pro získaní jména souboru pro samostatný nález.

   :param find: Hodnota parametru ``find`` použitého touto operací.
   :param filename: Hodnota parametru ``filename`` použitého touto operací.
   :param add_to_index: Hodnota parametru ``add_to_index`` použitého touto operací.

.. py:function:: get_projekt_soubor_name(projekt, file_name)

   Vygeneruje bezpečný název souboru pro upload do projektu.

   :param projekt: Projekt, ke kterému se soubor nahrává.
   :param file_name: Původní název nahrávaného souboru.

.. py:function:: check_stav_changed(request, zaznam)

   Ověří, zda se stav záznamu mezitím změnil oproti hodnotě odeslané ve formuláři.

   :param request: Django HTTP požadavek s daty odeslaného formuláře.
   :param zaznam: Ukládaný záznam, jehož stav se porovnává.

.. py:function:: redirect_ident_view(request, ident_cely)

   Přesměruje uživatele na detail záznamu nalezeného podle identifikátoru.

   :param request: Django HTTP požadavek.
   :param ident_cely: Hledaný identifikátor záznamu.

.. py:function:: prolong_session(request)

   Vrátí zbývající čas relace pro AJAX prodloužení přihlášení.

   :param request: Django HTTP požadavek aktuálního uživatele.

.. py:function:: post_ajax_get_pas_and_pian_limit(request)

   Funkce pohledu pro získaní heatmapy.

   :param request: Hodnota parametru ``request`` použitého touto operací.

.. py:function:: check_soubor_vazba(typ_vazby, ident, id_zaznamu)

   Ověří soubor vazba.

   :param typ_vazby: Vstupní hodnota ``typ_vazby`` pro danou operaci.
   :param ident: Vstupní hodnota ``ident`` pro danou operaci.
   :param id_zaznamu: Vstupní hodnota ``id_zaznamu`` pro danou operaci.
