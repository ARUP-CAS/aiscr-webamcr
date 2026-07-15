CORE views
==========

Definice views.

Třídy
------

.. py:class:: _SuffixNoLongerFreeError

   Zvolený suffix byl mezi načtením formuláře a uložením obsazen jiným požadavkem.


.. py:class:: DownloadFile

   Implementuje komponentu ``DownloadFile`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrátí požadovaný soubor nebo jeho náhled po ověření vazby k záznamu.

      :param request: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek.
      :param typ_vazby: Typ vazby souboru na doménový záznam.
      :param ident_cely: Identifikátor záznamu, ke kterému soubor patří.
      :param pk: Primární klíč souboru.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.
      :return: Odpověď s obsahem souboru, náhledem nebo redirect při chybě vazby.

      :raises Http404: Vyvolá se v konkrétních chybových větvích této funkce.


.. py:class:: DownloadThumbnailDZ

   Třída pohledu pro nahrání miniatury do DropZone při obnovení stránky.

   **Metody:**

   .. py:method:: get()

      Vrátí miniaturu souboru z dočasného uploadu po kontrole oprávnění a vazby.

      :param request: Parametr ``request`` předává se do volání ``SessionIdentifier()``, pracuje se s atributy ``session``, ovlivňuje větvení podmínek.
      :param typ_vazby: Typ vazby souboru na doménový záznam.
      :param ident_cely: Identifikátor záznamu, ke kterému soubor patří.
      :param pk: Primární klíč souboru.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.
      :return: Odpověď s miniaturou souboru.

      :raises PermissionDenied: Vyvolá se při splnění podmínky ``not request.session.get('session_uuid')``; nebo při splnění podmínky ``cache_ident is None or ident_cely != cache_ident or (not file_can_download)``.
      :raises Http404: Vyvolá se v konkrétních chybových větvích této funkce.


.. py:class:: DownloadThumbnailSmall

   Implementuje komponentu ``DownloadThumbnailSmall`` v rámci aplikace.


.. py:class:: DownloadThumbnailLarge

   Implementuje komponentu ``DownloadThumbnailLarge`` v rámci aplikace.


.. py:class:: UpdateFileView

   Třída pohledu pro zobrazení stránky pro nahrazení souboru.

   **Metody:**

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      :param request: Parametr ``request`` předává se do volání ``error()``, ``get()``, pracuje se s atributy ``GET``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``get()``.

   .. py:method:: post()

      Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

      :param request: Parametr ``request`` pracuje se s atributy ``GET``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``redirect()``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: dispatch()

      Inicializuje identifikaci session pro práci s cache nahraných souborů.

      :param request: Parametr ``request`` předává se do volání ``SessionIdentifier()``, ``dispatch()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      :return: Výsledek standardního zpracování dispatch.


.. py:class:: UploadFileView

   Třída pohledu pro zobrazení stránky s uploadem souboru.

   **Metody:**

   .. py:method:: get_zaznam()

      Načte doménový záznam, ke kterému se budou soubory nahrávat.

      :return: Vrací výsledek volání ``get_object_or_404()``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

      :return: Vrací proměnná ``context``.

   .. py:method:: dispatch()

      Zpracuje HTTP požadavek na nahrání souboru s ověřením přístupu.

      :param request: HTTP požadavek.
      :param args: Poziční argumenty.
      :param kwargs: Pojmenované argumenty.
      :return: HTTP odpověď.

   .. py:method:: post()

      Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``post``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``redirect()``.


.. py:class:: BasePostUploadView

   Abstraktní třída pro zpracování nahrávání souborů.

   Poskytuje společnou logiku pro upload nového souboru i nahrazení existujícího souboru.
   Implementuje kompletní workflow pro validaci nahrávaných souborů včetně kontroly MIME typů,
   antivirové kontroly a detekce šifrovaných souborů. Workflow zahrnuje: kontrolu přítomnosti
   souboru, validaci MIME typu a detekci šifrování, antivirovou kontrolu a předání validovaného
   souboru potomkům přes handle_upload(). Potomci musí tuto metodu implementovat.

   :ivar http_method_names: Povolené HTTP metody — pouze POST.
   :ivar source_url: URL zdroje souboru, pokud je specifikována.
   :ivar fedora_transaction: Instance transakce pro práci s Fedora repository.
   :ivar original_filename: Původní název nahrávaného souboru.

   **Metody:**

   .. py:method:: post()

      Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

      Metoda provádí kompletní validaci nahrávaného souboru před jeho uložením:
      - Kontroluje přítomnost souboru v requestu
      - Validuje MIME typ a detekuje šifrované soubory
      - Provádí antivirovou kontrolu obsahu
      - Deleguje finální zpracování na potomky prostřednictvím handle_upload()

      Response Status Codes:
          200: Soubor byl úspěšně validován a zpracován
          400: Validační chyba (chybějící soubor, šifrovaný, virus, neplatný MIME typ)
          500: Neznámá chyba při zpracování

      :param request: Parametr ``request`` předává se do volání ``warning()``, ``handle_upload()``, pracuje se s atributy ``POST``, ``FILES``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``handle_upload()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``handle_upload()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``_unknown_error_response()``, výsledek volání ``JsonResponse()``, výsledek volání ``handle_upload()``.

   .. py:method:: handle_upload()

      Abstraktní metoda pro implementaci konkrétního zpracování nahraného souboru.

      Tato metoda musí být implementována potomky třídy. Je volána z post() metody
      po úspěšné validaci souboru (MIME typ, antivirus). Potomci zde implementují
      specifickou logiku pro nové nahrání nebo aktualizaci existujícího souboru.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``handle_upload``.
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
      :param response_data: Slovník s daty odpovědi, který se případně rozšíří o varování.
      :param duplikat: QuerySet duplicitních souborů podle hashe.
      :return: Upravený slovník odpovědi (beze změny, pokud duplicita není nalezena).

   .. py:method:: _append_rename_message()

      Přidá informaci o přejmenování souboru do odpovědi.

      Pokud byl soubor během uploadu přejmenován (typicky kvůli úpravě přípony
      pro soulad s MIME typem), přidá do response_data informační zprávu.
      :param response_data: Slovník s daty odpovědi, který se případně doplní o zprávu.
      :param renamed: Parametr ``renamed`` ovlivňuje větvení podmínek.
      :param new_name: Nově přidělený název souboru.
      :return: Upravený slovník odpovědi (beze změny, pokud k přejmenování nedošlo).

   .. py:method:: _unknown_error_response()

      Vrátí JSON odpověď s chybovou zprávou a HTTP status 500 pro neočekávané chyby
      při zpracování souboru, které nejsou pokryty specifickými error handlery.
      :return: JSON odpověď s obecnou chybou a HTTP statusem 500.


.. py:class:: NewFileUploadView

   Pohled pro nahrání nového souboru k záznamu (projekt, dokument, samostatný nález).

   Zpracovává workflow vytvoření nového souboru: kontrolu oprávnění (vč. anonymního přístupu
   pro projekty), rozlišení typu záznamu, validaci a úpravu přípony podle MIME typu, odstranění
   GPS dat z obrázků, uložení do Fedora repository, vytvoření databázového záznamu s metadaty,
   detekci duplicit podle SHA-512 hashe a zaznamenání události do historie.

   :ivar ident_cely: Identifikátor záznamu, ke kterému má být soubor nahrán.
   :ivar typ_vazby: Typ vazby — ``"projekt"``, ``"dokument"``, ``"model3d"`` nebo ``"pas"``.

   **Metody:**

   .. py:method:: handle_upload()

      Implementuje nahrání nového souboru k záznamu.

      Provádí workflow vytvoření nového souboru včetně kontroly oprávnění,
      generování názvu, uložení do repository a založení databázového záznamu.
      Podporuje anonymní upload pro oznámení a automaticky zpracovává metadata obrázků.

      Response Status Codes:
          200: Soubor úspěšně nahrán
          400: Chyba při nahrávání (transakční konflikt, MIME typ, atd.)
          403: Nedostatečná oprávnění nebo překročen limit souborů
          500: Neexistující záznam nebo jiná interní chyba

      :param request: HTTP request s informacemi o uživateli a session.
      :param soubor: Nahraný soubor z requestu.
      :param soubor_data: Binární obsah souboru.
      :param args: Dodatečné poziční argumenty z URL.
      :param kwargs: Klíčové argumenty včetně ``ident_cely`` a ``typ_vazby``.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, proměnná ``resolved``.

   .. py:method:: _resolve_object_and_name()

      Rozliší typ záznamu, zkontroluje oprávnění a vygeneruje standardizovaný název souboru.

      Na základě ident_cely a typ_vazby načte odpovídající záznam z databáze,
      ověří konzistenci mezi typ_vazby a skutečným typem objektu, zkontroluje
      oprávnění uživatele k nahrání souboru a vygeneruje standardizovaný název
      souboru podle příslušných konvencí.
      :param request: HTTP request s kontextem aktuálního uživatele.
      :param ident_cely: Úplný identifikátor cílového záznamu.
      :param filename: Původní název nahrávaného souboru.
      :param typ_vazby: Typ vazby (``projekt``, ``dokument``, ``model3d`` nebo ``pas``).
      :return: Při úspěchu dvojice ``(objekt, new_name)``, jinak ``JsonResponse`` s chybou.


.. py:class:: UpdateExistingFileUploadView

   Pohled pro nahrazení existujícího souboru novou verzí.

   Rozdíly oproti NewFileUploadView:
   - Vždy vyžaduje přihlášení uživatele (LoginRequiredMixin)
   - Nepodporuje projekty (pouze dokument, model3d, pas)
   - Zachovává původní název souboru, aktualizuje pouze příponu
   - Aktualizuje existující záznam v Fedora repository místo vytváření nového
   - V historii zaznamenává jako novou verzi, ne nový soubor

   :param typ_vazby: Typ vazby - "dokument", "model3d", nebo "pas"
   :type typ_vazby: str
   :param ident_cely: Identifikátor záznamu, ke kterému soubor patří
   :type ident_cely: str
   :param file_id: Primary key existujícího Soubor objektu
   :type file_id: int

   **Metody:**

   .. py:method:: handle_upload()

      Implementuje aktualizaci existujícího souboru novou verzí.

      Nahrazuje obsah existujícího souboru, zachovává název (s případnou úpravou
      přípony), aktualizuje repository a zapisuje novou verzi do historie.

      Response Status Codes:
          200: Soubor úspěšně aktualizován
          400: Chyba vazby, transakční konflikt, MIME typ nebo neplatný typ_vazby
          403: Nedostatečná oprávnění k nahrazení souboru
          500: Chybějící vazba nebo jiná interní chyba

      :param request: HTTP request s informacemi o přihlášeném uživateli.
      :param soubor: Nový nahraný soubor z requestu.
      :param soubor_data: Binární obsah nového souboru.
      :param args: Dodatečné poziční argumenty z URL.
      :param kwargs: Klíčové argumenty včetně ``typ_vazby``, ``ident_cely`` a ``file_id``.
      :raises Http404: Pokud soubor s daným ``file_id`` neexistuje.
      :raises ZaznamSouborNotmatching: Pokud soubor nepatří k uvedenému záznamu.

      :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``permission_check``, výsledek volání ``JsonResponse()``, výsledek volání ``_unknown_error_response()``.

   .. py:method:: _check_update_permissions()

      Zkontroluje platnost typu vazby a oprávnění uživatele k nahrazení souboru.

      Na základě typ_vazby ověří, zda je nahrazení souboru povoleno pro daný typ
      záznamu, a zkontroluje oprávnění uživatele pomocí check_permissions.
      :param request: HTTP request s informacemi o přihlášeném uživateli.
      :param typ_vazby: Typ vazby (``dokument``, ``model3d`` nebo ``pas``).
      :param ident_cely: Úplný identifikátor záznamu.
      :param file_id: Primární klíč nahrazovaného souboru.
      :return: ``True`` při úspěchu, jinak ``JsonResponse`` s chybovým popisem.


.. py:class:: ExportMixinDate

   Mixin pro získaní názvu exportovaného souboru.

   **Metody:**

   .. py:method:: get_export_filename()

      Sestaví název exportního souboru s časovým razítkem.

      :param export_format: Cílový formát exportu (např. ``csv``, ``xlsx``).
      :param export_name: Volitelný základ názvu; pokud není zadán, použije ``self.export_name``.

      :return: Vrací výsledek volání ``format()``.


.. py:class:: PermissionFilterMixin

   Implementuje komponentu ``PermissionFilterMixin`` v rámci aplikace.

   **Metody:**

   .. py:method:: check_filter_permission()

      Ověří filter permission.

      :param qs: Parametr ``qs`` předává se do volání ``filter_by_permission()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      :param action: Identifikátor akce, která se má provést.

      :return: Vrací proměnná ``qs``.

   .. py:method:: filter_by_permission()

      Filtruje by permission.

      :param qs: Parametr ``qs`` předává se do volání ``filter()``, ``add_ownership_lookup()``, pracuje se s atributy ``annotate``, ``none``, vstupuje do návratové hodnoty.
      :param permission: Parametr ``permission`` předává se do volání ``filter()``, ``add_status_lookup()``, pracuje se s atributy ``base``, ``status``, ovlivňuje větvení podmínek.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``none()``, proměnná ``qs``.

   .. py:method:: add_status_lookup()

      Provádí operaci add status lookup.

      :param permission: Parametr ``permission`` předává se do volání ``sub()``, pracuje se s atributy ``status``.

      :return: Vrací proměnná ``filterdoc``.

   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      :param ownership: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
      :param qs: Parametr ``qs`` slouží jako vstup pro logiku funkce ``add_ownership_lookup``.

      :return: Vrací výsledek volání ``Q()``.

   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      :param permission: Parametr ``permission`` předává se do volání ``filter()``, ``add_ownership_lookup()``, pracuje se s atributy ``accessibility``, vstupuje do návratové hodnoty.
      :param qs: Parametr ``qs`` předává se do volání ``filter()``, ``add_ownership_lookup()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``filter()``.


.. py:class:: SearchListView

   Třída pohledu pro tabulky záznamů, která je použita jako základ pro jednotlivé pohledy.

   **Metody:**

   .. py:method:: create_export()

      Vytvoří export výsledků vyhledávání v požadovaném formátu.

      :param export_format: Parametr ``export_format`` předává se do volání ``debug()``, ovlivňuje větvení podmínek.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``HttpResponse()``, proměnná ``response``.

   .. py:method:: postprocess_export_dataframe()

      Hook pro post-processing exportního DataFrame před přejmenováním sloupců.

      Metoda je volána v ``create_export`` po sestavení DataFramu z Redis snapshotů
      a po aplikaci ``filtered_column_order``, ale před přejmenováním sloupců na verbose names.
      Sloupce jsou v tuto chvíli identifikovány strojovými názvy (shodné s názvy v tabulce).

      Výchozí implementace vrací DataFrame beze změny. Podtřídy mohou přepsat tuto metodu
      pro aplikaci oprávnění nebo jiné úpravy dat.

      :param df: DataFrame sestavený z Redis snapshotů se strojovými názvy sloupců.
      :return: Upravený (nebo nezměněný) DataFrame.

   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: _get_sort_params()

      Vrací sort params.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: _is_query_cacheable()

      Vrací, zda je bezpečné zapnout cacheops cache pro aktuální filtr.

      Spočítá součin počtů hodnot u vícehodnotových GET parametrů. Tento součin
      odpovídá řádové velikosti invalidační DNF, kterou cacheops staví – u velkých
      kombinací hlubokých M2M filtrů by její sestavení vyčerpalo paměť a shodilo
      worker. Stránkovací a řadicí parametry se do součinu nezapočítávají.

      :return: ``True`` pokud součin nepřekročí ``cache_filter_value_product_limit``.

   .. py:method:: get_queryset()

      Vrací queryset výsledků vyhledávání podle zadaných filtrů.

      :return: Vrací proměnná ``qs``.

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      :param request: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``get()``.


.. py:class:: StahnoutDataHistorickaView

   Třída pohledu pro stažení historické verze souboru nebo metadat z Fedory

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      :param model_name: Název modelu používaný pro cílení operace.
      :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get()``.
      :param timestamp: Časový údaj použitý při filtrování nebo výpočtu.

      :return: Vrací proměnná ``response``.
      :raises Http404: Vyvolá se při splnění podmínky ``Model is None``.


.. py:class:: CheckUserAuthentication

   Implementuje komponentu ``CheckUserAuthentication`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      :param request: Parametr ``request`` předává se do volání ``JsonResponse()``, pracuje se s atributy ``user``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: ReadTempValueView

   Implementuje komponentu ``ReadTempValueView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` pracuje se s atributy ``GET``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: DeleteTempValueView

   Implementuje komponentu ``DeleteTempValueView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` pracuje se s atributy ``GET``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: AbortDownloadUpdateTempValueView

   Implementuje komponentu ``AbortDownloadUpdateTempValueView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` pracuje se s atributy ``GET``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: RosettaFileLevelMixinWithBackup

   Třída podledu pro práci s prekladmi doplnena o backup osubory.

   **Metody:**

   .. py:method:: po_file_path()

      Podle URL parametrů `kwargs` odvodí a vrátí cestu k `.po` souboru,

      který se má zobrazit nebo upravit.

      Pokud soubor neexistuje, vyvolá chybu 404.

      :return: Vrací proměnná ``path``.
      :raises Http404: Vyvolá se při zpracování zachycené výjimky typu ``IndexError``.


.. py:class:: TranslationImportView

   Třída pohledu pro import překladových souborů.

   **Metody:**

   .. py:method:: form_valid()

      Provádí operaci form valid.

      :param form: Parametr ``form`` pracuje se s atributy ``cleaned_data``.

      :return: Vrací výsledek volání ``redirect()``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.

   .. py:method:: handle_uploaded_file()

      Zpracuje uploaded file.

      :param f: Pomocný stream/objekt používaný interně funkcí.


.. py:class:: TranslationFileListWithBackupView

   Třída pohledu pro zobrazení prekladových souboru s backup souborami.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.


.. py:class:: TranslationFormWithBackupView

   Třída pohledu pro zobrazení formulaře s prekladmi i pro backup soubory

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      :return: Vrací proměnná ``context``.


.. py:class:: TranslationFileDownloadBackup

   Třída pohledu pro stahování prekladových souboru is backup souborami.

   **Metody:**

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``response``, výsledek volání ``HttpResponseRedirect()``.


.. py:class:: TranslationFileSmazatBackup

   Třída pohledu pro smazání backup prekladových souboru.

   **Metody:**

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      :return: Vrací výsledek volání ``render_to_response()``.

   .. py:method:: post()

      Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``post``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: PrometheusMetricsView

   Třída pohledu pro zobrazení prometheus metrik doplněna o mixin pro filtrování IP adres.

   **Metody:**

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      :param request: Parametr ``request`` předává se do volání ``ExportToDjangoView()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      :return: Vrací výsledek volání ``ExportToDjangoView()``.


.. py:class:: ApplicationRestartView

   Třída pohledu pro restartovani uwsgi aplikace.

   **Metody:**

   .. py:method:: post()

      Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

      :param request: Parametr ``request`` pracuje se s atributy ``user``, ``META``, ovlivňuje větvení podmínek.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      :return: Vrací výsledek volání ``redirect()``.
      :raises PermissionDenied: Vyvolá se při splnění podmínky ``request.user.hlavni_role.id != ROLE_ADMIN_ID``.


.. py:class:: DataImportProgress

   Implementuje komponentu ``DataImportProgress`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
      :param kwargs: Parametr ``kwargs`` pracuje se s atributy ``get``.

      :return: Vrací výsledek volání ``JsonResponse()``.
      :raises PermissionDenied: Vyvolá se při splnění podmínky ``not request.user.is_superuser``.


.. py:class:: DataImportStop

   Implementuje komponentu ``DataImportStop`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
      :param kwargs: Parametr ``kwargs`` pracuje se s atributy ``get``.

      :return: Vrací výsledek volání ``JsonResponse()``.
      :raises PermissionDenied: Vyvolá se při splnění podmínky ``not request.user.is_superuser``.


.. py:class:: DataImportProgressReportView

   Exportuje výsledky importu dat jako soubor Excel.

   **Metody:**

   .. py:method:: get()

      Sestaví a vrátí Excel report s výsledky validace a průběhu importu.

      :param request: HTTP požadavek, ověřuje se právo superuživatele.
      :param kwargs: Obsahuje ``job_id`` identifikující danou importní úlohu.
      :return: Soubor Excel (``application/vnd.openxmlformats-officedocument.spreadsheetml.sheet``) ke stažení.
      :raises PermissionDenied: Vyvolá se, pokud přihlášený uživatel není superuživatel.


.. py:class:: DataImportStart

   Implementuje komponentu ``DataImportStart`` v rámci aplikace.

   **Metody:**

   .. py:method:: post()

      Spustí Celery task pro import dat.

      :param request: Parametr ``request`` předává se do volání ``delay()``, pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
      :param kwargs: Parametr ``kwargs`` pracuje se s atributy ``get``.

      :return: Vrací výsledek volání ``JsonResponse()``.
      :raises PermissionDenied: Vyvolá se při splnění podmínky ``not request.user.is_superuser``.


Funkce
------

.. py:function:: index(request)

   Zobrazí hlavní stránku aplikace po přihlášení uživatele.

   :param request: HTTP požadavek aktuálního uživatele.

   :return: Vrací výsledek volání ``render()``.

.. py:function:: delete_file_DZ(request, typ_vazby, ident_cely, pk)

   Smaže soubor nahraný přes dropzone včetně záznamu v databázi i ve Fedora úložišti.

   :param request: HTTP požadavek obsahující session identifikátor dropzone uploadu.
   :param typ_vazby: Typ vazby souboru na doménový objekt (např. dokument, projekt, PAS).
   :param ident_cely: Identifikátor záznamu, ke kterému je soubor navázán.
   :param pk: Primární klíč mazaného souboru.

   :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: delete_file(request, typ_vazby, ident_cely, pk)

   Smaže existující soubor, jeho databázový záznam i binární obsah v repozitáři.

   :param request: HTTP požadavek s metodou GET/POST a případnou návratovou URL.
   :param typ_vazby: Typ vazby souboru na navázaný doménový objekt.
   :param ident_cely: Identifikátor záznamu, u kterého se soubor odstraňuje.
   :param pk: Primární klíč mazaného souboru.

   :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``JsonResponse()``, výsledek volání ``render()``.

.. py:function:: _rename_file_safe_redirect(request)

   Vrátí bezpečnou návratovou URL z parametru ``next`` požadavku na přejmenování.

   :param request: HTTP požadavek s parametrem ``next`` v GET nebo POST.
   :return: Bezpečná návratová URL nebo domovská stránka.

.. py:function:: _rename_file_messages_response(request, message, status)

   Vrátí ``JsonResponse`` s frontovanými django zprávami pro AJAX modal (vzor ``delete_file``).

   :param request: HTTP požadavek, do jehož zpráv se přidá chybová hláška.
   :param message: Chybová zpráva k zobrazení uživateli.
   :param status: HTTP status odpovědi.
   :return: ``JsonResponse`` se seznamem zpráv v klíči ``messages``.

.. py:function:: rename_file(request, typ_vazby, ident_cely, pk)

   Přejmenuje existující soubor změnou suffixu na volnou povolenou hodnotu.

   Mění název v databázi (``soubor.nazev``), ve Fedoře (``ebucore:filename`` souboru i jeho potomků)
   a vyvolá přegenerování XML metadat navázaného záznamu. Dostupné pro dokumenty (včetně 3D modelů)
   a samostatné nálezy, které mají suffixové schéma názvů.

   :param request: HTTP požadavek s metodou GET (modal) nebo POST (provedení).
   :param typ_vazby: Typ vazby souboru na navázaný doménový objekt.
   :param ident_cely: Identifikátor záznamu, u kterého se soubor přejmenovává.
   :param pk: Primární klíč přejmenovávaného souboru.
   :return: Vrací modal (GET) nebo ``JsonResponse`` s přesměrováním či chybou (POST).

.. py:function:: get_finds_soubor_name(find, filename, add_to_index)

   Funkce pro získaní jména souboru pro samostatný nález.

   Název se přiděluje navýšením podle nejvyššího obsazeného suffixu (``F01`` … ``F99``). Toto výchozí
   chování se záměrně nemění – uvolnění či změnu pozice řeší přejmenování souboru.

   :param find: Textový název, klíč nebo výraz ``find`` používaný v rámci operace.
   :param filename: Parametr ``filename`` se předává do volání ``splitext()``, ``warning()``, vstupuje do návratové hodnoty.
   :param add_to_index: Číselná hodnota ``add_to_index`` použitá při výpočtu nebo transformaci.

   :return: Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, bool.

.. py:function:: _obsazene_suffixy(navazany_objekt, base, current_soubor)

   Vrátí množinu suffixů (částí názvu mezi identem a příponou) obsazených soubory záznamu.

   :param navazany_objekt: Navázaný objekt (dokument nebo samostatný nález) s vazbou ``soubory``.
   :param base: Identifikátor záznamu bez pomlček, kterým názvy souborů začínají.
   :param current_soubor: Soubor, který se přejmenovává a do obsazených suffixů se nezapočítává.
   :return: Množina řetězců suffixů obsazených ostatními soubory.

.. py:function:: get_dokument_free_suffixes(dokument, current_soubor)

   Vrátí seznam volných suffixů pro soubory dokumentu (3D modelu).

   Suffix je část názvu mezi identem (bez pomlček) a příponou. Možné hodnoty jsou prázdný řetězec
   (základní soubor ``{ident}.{ext}``) a písmena ``A``–``Z``. Suffix přejmenovávaného souboru se
   považuje za volný, aby jej bylo možné v nabídce ponechat.

   :param dokument: Dokument, jehož soubory se zkoumají.
   :param current_soubor: Přejmenovávaný soubor (vyloučen z obsazených suffixů).
   :return: Seznam volných suffixů v pořadí prázdný slot, ``A`` … ``Z``.

.. py:function:: get_finds_free_suffixes(find, current_soubor)

   Vrátí seznam volných suffixů pro soubory samostatného nálezu.

   Suffix má tvar ``F01`` … ``F99``. Suffix přejmenovávaného souboru se považuje za volný.

   :param find: Samostatný nález, jehož soubory se zkoumají.
   :param current_soubor: Přejmenovávaný soubor (vyloučen z obsazených suffixů).
   :return: Seznam volných suffixů v pořadí ``F01`` … ``F99``.

.. py:function:: get_soubor_suffix(soubor)

   Vrátí aktuální suffix souboru (část názvu mezi identem záznamu bez pomlček a příponou).

   :param soubor: Soubor, jehož suffix se zjišťuje.
   :return: Řetězec suffixu (může být prázdný); ``None`` pokud název neodpovídá očekávanému vzoru.

.. py:function:: get_projekt_soubor_name(projekt, file_name)

   Vygeneruje bezpečný název souboru pro upload do projektu.

   :param projekt: Projekt, ke kterému se soubor nahrává.
   :param file_name: Původní název nahrávaného souboru.

   :return: Vrací hodnotu podle větve zpracování, typicky: bool, hodnotu podle větve zpracování.

.. py:function:: check_stav_changed(request, zaznam, prefix)

   Ověří, zda se stav záznamu mezitím změnil oproti hodnotě odeslané ve formuláři.

   :param request: Parametr ``request`` předává se do volání ``CheckStavNotChangedForm()``, ``add_message()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek.
   :param zaznam: Ukládaný záznam, jehož stav se porovnává.
   :param prefix: Volitelný prefix formuláře použitý při renderování, nutný pro správné načtení ``old_stav`` z POST dat.

   :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

.. py:function:: redirect_ident_view(request, ident_cely)

   Přesměruje uživatele na detail záznamu nalezeného podle identifikátoru.
   Pokud identifikátor není nalezen mezi aktuálními, pokusí se hledat mezi dočasnými v historii.

   :param request: Parametr ``request`` předává se do volání ``redirect()``, ``get_absolute_url()``, vstupuje do návratové hodnoty.
   :param ident_cely: Hledaný identifikátor záznamu.

   :return: Vrací výsledek volání ``redirect()``.

.. py:function:: prolong_session(request)

   Vrátí zbývající čas relace pro AJAX prodloužení přihlášení.

   :param request: Parametr ``request`` předává se do volání ``seconds_until_idle_time_end()``.

   :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: post_ajax_get_pas_and_pian_limit(request)

   Funkce pohledu pro získaní heatmapy.

   :param request: Parametr ``request`` se předává do volání ``loads()``, ``get_pas_from_envelope()``, pracuje se s atributy ``body``.

   :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: post_ajax_get_list_map_data(request, layer)

   Funkce pohledu pro datovou vrstvu mapy v záložce filtru výpisu.

   Vrací prvky daného workflow (``layer``) v aktuálním výřezu mapy ve stejném kontraktu jako
   :func:`post_ajax_get_pas_and_pian_limit` – tj. ``{"points"|"heat", "algorithm", "count"}`` –
   aby klient mohl znovupoužít stávající vykreslování. Nad ``LIMIT_PRVKU_ZOBRAZENI_HEATMAP`` se
   přepíná na heatmapu. Vrstva je pouze orientační; vlastní filtrování tabulky zajišťuje
   serverový filtr ``geom_filter``.

   :param request: HTTP požadavek s tělem ``{"bounds": {...}, "zoom": int}``.
   :param layer: Identifikátor datové vrstvy (``"pas"`` | ``"projekt"`` | ``"akce"`` | ``"lokalita"`` | ``"3d"``).

   :return: Vrací výsledek volání ``JsonResponse()``.

.. py:function:: check_soubor_vazba(typ_vazby, ident, id_zaznamu)

   Ověří soubor vazba.

   :param typ_vazby: Parametr ``typ_vazby`` ovlivňuje větvení podmínek.
   :param ident: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.
   :param id_zaznamu: Parametr ``id_zaznamu`` předává se do volání ``filter()``.

   :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
   :raises ZaznamSouborNotmatching: Vyvolá se při splnění podmínky ``soubor.count() > 0``.
