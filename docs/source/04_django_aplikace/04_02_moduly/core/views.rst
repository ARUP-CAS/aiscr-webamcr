CORE views
==========

Definice views.

Třídy
------

.. py:class:: DownloadFile

   Implementuje komponentu ``DownloadFile`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrátí požadovaný soubor nebo jeho náhled po ověření vazby k záznamu.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``add_message()``, ``url_has_allowed_host_and_scheme()``, pracuje se s atributy ``GET``, ovlivňuje větvení podmínek.
      - ``typ_vazby``: Typ vazby souboru na doménový záznam.
      - ``ident_cely``: Identifikátor záznamu, ke kterému soubor patří.
      - ``pk``: Primární klíč souboru.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      **Návratová hodnota:**

      Odpověď s obsahem souboru, náhledem nebo redirect při chybě vazby.

      **Výjimky:**

      - ``Http404``: Vyvolá se v konkrétních chybových větvích této funkce.



.. py:class:: DownloadThumbnailDZ

   Třída pohledu pro nahrání miniatury do DropZone při obnovení stránky.

   **Metody:**

   .. py:method:: get()

      Vrátí miniaturu souboru z dočasného uploadu po kontrole oprávnění a vazby.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``SessionIdentifier()``, pracuje se s atributy ``session``, ovlivňuje větvení podmínek.
      - ``typ_vazby``: Typ vazby souboru na doménový záznam.
      - ``ident_cely``: Identifikátor záznamu, ke kterému soubor patří.
      - ``pk``: Primární klíč souboru.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      **Návratová hodnota:**

      Odpověď s miniaturou souboru.

      **Výjimky:**

      - ``PermissionDenied``: Vyvolá se při splnění podmínky ``not request.session.get('session_uuid')``; nebo při splnění podmínky ``cache_ident is None or ident_cely != cache_ident or (not file_can_download)``.
      - ``Http404``: Vyvolá se v konkrétních chybových větvích této funkce.



.. py:class:: DownloadThumbnailSmall

   Implementuje komponentu ``DownloadThumbnailSmall`` v rámci aplikace.


.. py:class:: DownloadThumbnailLarge

   Implementuje komponentu ``DownloadThumbnailLarge`` v rámci aplikace.


.. py:class:: UpdateFileView

   Třída pohledu pro zobrazení stránky pro nahrazení souboru.

   **Metody:**

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``error()``, ``get()``, pracuje se s atributy ``GET``, vstupuje do návratové hodnoty.
      - ``args``: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``get()``.


   .. py:method:: post()

      Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

      **Parametry:**

      - ``request``: Parametr ``request`` pracuje se s atributy ``GET``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      **Návratová hodnota:**

      Vrací výsledek volání ``redirect()``.


   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: dispatch()

      Inicializuje identifikaci session pro práci s cache nahraných souborů.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``SessionIdentifier()``, ``dispatch()``, vstupuje do návratové hodnoty.
      - ``args``: Parametr ``args`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``dispatch()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Výsledek standardního zpracování dispatch.



.. py:class:: UploadFileView

   Třída pohledu pro zobrazení stránky s uploadem souboru.

   **Metody:**

   .. py:method:: get_zaznam()

      Načte doménový záznam, ke kterému se budou soubory nahrávat.

      **Návratová hodnota:**

      Vrací výsledek volání ``get_object_or_404()``.


   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get_context_data``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: dispatch()

      Zpracuje HTTP požadavek na nahrání souboru s ověřením přístupu.

      **Parametry:**

      - ``request``: HTTP požadavek.
      - ``args``: Poziční argumenty.
      - ``kwargs``: Pojmenované argumenty.

      **Návratová hodnota:**

      HTTP odpověď.


   .. py:method:: post()

      Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``post``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      **Návratová hodnota:**

      Vrací výsledek volání ``redirect()``.



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

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``warning()``, ``handle_upload()``, pracuje se s atributy ``POST``, ``FILES``, vstupuje do návratové hodnoty.
      - ``args``: Parametr ``args`` se předává do volání ``handle_upload()``, vstupuje do návratové hodnoty.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``handle_upload()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``_unknown_error_response()``, výsledek volání ``JsonResponse()``, výsledek volání ``handle_upload()``.


   .. py:method:: handle_upload()

      Abstraktní metoda pro implementaci konkrétního zpracování nahraného souboru.

      Tato metoda musí být implementována potomky třídy. Je volána z post() metody
      po úspěšné validaci souboru (MIME typ, antivirus). Potomci zde implementují
      specifickou logiku pro nové nahrání nebo aktualizaci existujícího souboru.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``handle_upload``.
      - ``soubor``: Nahraný soubor z requestu připravený k uložení.
      - ``soubor_data``: Binární obsah souboru v objektu ``BytesIO``.
      - ``args``: Dodatečné poziční argumenty z URL dispatcheru.
      - ``kwargs``: Dodatečné klíčové argumenty z URL (např. ``ident_cely``).

      **Výjimky:**

      - ``NotImplementedError``: Pokud potomek metodu nepřepíše.


   .. py:method:: _append_duplicate_message()

      Přidá informaci o duplicitním souboru do odpovědi.

      Kontroluje, zda v systému již existuje soubor se stejným SHA-512 hashem.
      Pokud ano, přidá do response_data varovnou zprávu s informací o duplicitě
      včetně identifikátoru záznamu, ke kterému je duplicitní soubor připojen.

      **Parametry:**

      - ``response_data``: Slovník s daty odpovědi, který se případně rozšíří o varování.
      - ``duplikat``: QuerySet duplicitních souborů podle hashe.

      **Návratová hodnota:**

      Upravený slovník odpovědi (beze změny, pokud duplicita není nalezena).


   .. py:method:: _append_rename_message()

      Přidá informaci o přejmenování souboru do odpovědi.

      Pokud byl soubor během uploadu přejmenován (typicky kvůli úpravě přípony
      pro soulad s MIME typem), přidá do response_data informační zprávu.

      **Parametry:**

      - ``response_data``: Slovník s daty odpovědi, který se případně doplní o zprávu.
      - ``renamed``: Parametr ``renamed`` ovlivňuje větvení podmínek.
      - ``new_name``: Nově přidělený název souboru.

      **Návratová hodnota:**

      Upravený slovník odpovědi (beze změny, pokud k přejmenování nedošlo).


   .. py:method:: _unknown_error_response()

      Vrátí JSON odpověď s chybovou zprávou a HTTP status 500 pro neočekávané chyby
      při zpracování souboru, které nejsou pokryty specifickými error handlery.

      **Návratová hodnota:**

      JSON odpověď s obecnou chybou a HTTP statusem 500.



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

      **Parametry:**

      - ``request``: HTTP request s informacemi o uživateli a session.
      - ``soubor``: Nahraný soubor z requestu.
      - ``soubor_data``: Binární obsah souboru.
      - ``args``: Dodatečné poziční argumenty z URL.
      - ``kwargs``: Klíčové argumenty včetně ``ident_cely`` a ``typ_vazby``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, proměnná ``resolved``.


   .. py:method:: _resolve_object_and_name()

      Rozliší typ záznamu, zkontroluje oprávnění a vygeneruje standardizovaný název souboru.

      Na základě ident_cely a typ_vazby načte odpovídající záznam z databáze,
      ověří konzistenci mezi typ_vazby a skutečným typem objektu, zkontroluje
      oprávnění uživatele k nahrání souboru a vygeneruje standardizovaný název
      souboru podle příslušných konvencí.

      **Parametry:**

      - ``request``: HTTP request s kontextem aktuálního uživatele.
      - ``ident_cely``: Úplný identifikátor cílového záznamu.
      - ``filename``: Původní název nahrávaného souboru.
      - ``typ_vazby``: Typ vazby (``projekt``, ``dokument``, ``model3d`` nebo ``pas``).

      **Návratová hodnota:**

      Při úspěchu dvojice ``(objekt, new_name)``, jinak ``JsonResponse`` s chybou.



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

      Response Status Codes:
      200: Soubor úspěšně aktualizován
      400: Chyba vazby, transakční konflikt, MIME typ nebo neplatný typ_vazby
      403: Nedostatečná oprávnění k nahrazení souboru
      500: Chybějící vazba nebo jiná interní chyba

      **Parametry:**

      - ``request``: HTTP request s informacemi o přihlášeném uživateli.
      - ``soubor``: Nový nahraný soubor z requestu.
      - ``soubor_data``: Binární obsah nového souboru.
      - ``args``: Dodatečné poziční argumenty z URL.
      - ``kwargs``: Klíčové argumenty včetně ``typ_vazby``, ``ident_cely`` a ``file_id``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``permission_check``, výsledek volání ``JsonResponse()``, výsledek volání ``_unknown_error_response()``.

      **Výjimky:**

      - ``Http404``: Pokud soubor s daným ``file_id`` neexistuje.
      - ``ZaznamSouborNotmatching``: Pokud soubor nepatří k uvedenému záznamu.


   .. py:method:: _check_update_permissions()

      Zkontroluje platnost typu vazby a oprávnění uživatele k nahrazení souboru.

      Na základě typ_vazby ověří, zda je nahrazení souboru povoleno pro daný typ
      záznamu, a zkontroluje oprávnění uživatele pomocí check_permissions.

      **Parametry:**

      - ``request``: HTTP request s informacemi o přihlášeném uživateli.
      - ``typ_vazby``: Typ vazby (``dokument``, ``model3d`` nebo ``pas``).
      - ``ident_cely``: Úplný identifikátor záznamu.
      - ``file_id``: Primární klíč nahrazovaného souboru.

      **Návratová hodnota:**

      ``True`` při úspěchu, jinak ``JsonResponse`` s chybovým popisem.



.. py:class:: ExportMixinDate

   Mixin pro získaní názvu exportovaného souboru.

   **Metody:**

   .. py:method:: get_export_filename()

      Sestaví název exportního souboru s časovým razítkem.

      **Parametry:**

      - ``export_format``: Cílový formát exportu (např. ``csv``, ``xlsx``).
      - ``export_name``: Volitelný základ názvu; pokud není zadán, použije ``self.export_name``.

      **Návratová hodnota:**

      Vrací výsledek volání ``format()``.



.. py:class:: PermissionFilterMixin

   Implementuje komponentu ``PermissionFilterMixin`` v rámci aplikace.

   **Metody:**

   .. py:method:: check_filter_permission()

      Ověří filter permission.

      **Parametry:**

      - ``qs``: Parametr ``qs`` předává se do volání ``filter_by_permission()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.
      - ``action``: Identifikátor akce, která se má provést.

      **Návratová hodnota:**

      Vrací proměnná ``qs``.


   .. py:method:: filter_by_permission()

      Filtruje by permission.

      **Parametry:**

      - ``qs``: Parametr ``qs`` předává se do volání ``filter()``, ``add_ownership_lookup()``, pracuje se s atributy ``annotate``, ``none``, vstupuje do návratové hodnoty.
      - ``permission``: Parametr ``permission`` předává se do volání ``filter()``, ``add_status_lookup()``, pracuje se s atributy ``base``, ``status``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``none()``, proměnná ``qs``.


   .. py:method:: add_status_lookup()

      Provádí operaci add status lookup.

      **Parametry:**

      - ``permission``: Parametr ``permission`` předává se do volání ``sub()``, pracuje se s atributy ``status``.

      **Návratová hodnota:**

      Vrací proměnná ``filterdoc``.


   .. py:method:: add_ownership_lookup()

      Provádí operaci add ownership lookup.

      **Parametry:**

      - ``ownership``: Uživatel nebo osoba ``ownership``, v jejímž kontextu se operace provádí.
      - ``qs``: Parametr ``qs`` slouží jako vstup pro logiku funkce ``add_ownership_lookup``.

      **Návratová hodnota:**

      Vrací výsledek volání ``Q()``.


   .. py:method:: add_accessibility_lookup()

      Provádí operaci add accessibility lookup.

      **Parametry:**

      - ``permission``: Parametr ``permission`` předává se do volání ``filter()``, ``add_ownership_lookup()``, pracuje se s atributy ``accessibility``, vstupuje do návratové hodnoty.
      - ``qs``: Parametr ``qs`` předává se do volání ``filter()``, ``add_ownership_lookup()``, pracuje se s atributy ``filter``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``filter()``.



.. py:class:: SearchListView

   Třída pohledu pro tabulky záznamů, která je použita jako základ pro jednotlivé pohledy.

   **Metody:**

   .. py:method:: create_export()

      Vytvoří export výsledků vyhledávání v požadovaném formátu.

      **Parametry:**

      - ``export_format``: Parametr ``export_format`` předává se do volání ``debug()``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``HttpResponse()``, proměnná ``response``.


   .. py:method:: postprocess_export_dataframe()

      Hook pro post-processing exportního DataFrame před přejmenováním sloupců.

      Metoda je volána v ``create_export`` po sestavení DataFramu z Redis snapshotů
      a po aplikaci ``filtered_column_order``, ale před přejmenováním sloupců na verbose names.
      Sloupce jsou v tuto chvíli identifikovány strojovými názvy (shodné s názvy v tabulce).

      Výchozí implementace vrací DataFrame beze změny. Podtřídy mohou přepsat tuto metodu
      pro aplikaci oprávnění nebo jiné úpravy dat.

      **Parametry:**

      - ``df``: DataFrame sestavený z Redis snapshotů se strojovými názvy sloupců.

      **Návratová hodnota:**

      Upravený (nebo nezměněný) DataFrame.


   .. py:method:: init_translations()

      Provádí operaci init translations.

   .. py:method:: _get_sort_params()

      Vrací sort params.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: get_queryset()

      Vrací queryset výsledků vyhledávání podle zadaných filtrů.

      **Návratová hodnota:**

      Vrací proměnná ``qs``.


   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
      - ``args``: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``get()``.



.. py:class:: StahnoutDataHistorickaView

   Třída pohledu pro stažení historické verze souboru nebo metadat z Fedory

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      - ``model_name``: Název modelu používaný pro cílení operace.
      - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get()``.
      - ``timestamp``: Časový údaj použitý při filtrování nebo výpočtu.

      **Návratová hodnota:**

      Vrací proměnná ``response``.

      **Výjimky:**

      - ``Http404``: Vyvolá se při splnění podmínky ``Model is None``.



.. py:class:: CheckUserAuthentication

   Implementuje komponentu ``CheckUserAuthentication`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``JsonResponse()``, pracuje se s atributy ``user``, vstupuje do návratové hodnoty.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: ReadTempValueView

   Implementuje komponentu ``ReadTempValueView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` pracuje se s atributy ``GET``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: DeleteTempValueView

   Implementuje komponentu ``DeleteTempValueView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` pracuje se s atributy ``GET``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: AbortDownloadUpdateTempValueView

   Implementuje komponentu ``AbortDownloadUpdateTempValueView`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` pracuje se s atributy ``GET``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: RosettaFileLevelMixinWithBackup

   Třída podledu pro práci s prekladmi doplnena o backup osubory.

   **Metody:**

   .. py:method:: po_file_path()

      Podle URL parametrů `kwargs` odvodí a vrátí cestu k `.po` souboru,

      který se má zobrazit nebo upravit.

      Pokud soubor neexistuje, vyvolá chybu 404.

      **Návratová hodnota:**

      Vrací proměnná ``path``.

      **Výjimky:**

      - ``Http404``: Vyvolá se při zpracování zachycené výjimky typu ``IndexError``.



.. py:class:: TranslationImportView

   Třída pohledu pro import překladových souborů.

   **Metody:**

   .. py:method:: form_valid()

      Provádí operaci form valid.

      **Parametry:**

      - ``form``: Parametr ``form`` pracuje se s atributy ``cleaned_data``.

      **Návratová hodnota:**

      Vrací výsledek volání ``redirect()``.


   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: handle_uploaded_file()

      Zpracuje uploaded file.

      **Parametry:**

      - ``f``: Pomocný stream/objekt používaný interně funkcí.



.. py:class:: TranslationFileListWithBackupView

   Třída pohledu pro zobrazení prekladových souboru s backup souborami.

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.



.. py:class:: TranslationFormWithBackupView

   Třída pohledu pro zobrazení formulaře s prekladmi i pro backup soubory

   **Metody:**

   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.



.. py:class:: TranslationFileDownloadBackup

   Třída pohledu pro stahování prekladových souboru is backup souborami.

   **Metody:**

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: proměnná ``response``, výsledek volání ``HttpResponseRedirect()``.



.. py:class:: TranslationFileSmazatBackup

   Třída pohledu pro smazání backup prekladových souboru.

   **Metody:**

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      **Návratová hodnota:**

      Vrací výsledek volání ``render_to_response()``.


   .. py:method:: post()

      Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

      **Parametry:**

      - ``request``: Parametr ``request`` slouží jako vstup pro logiku funkce ``post``.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: PrometheusMetricsView

   Třída pohledu pro zobrazení prometheus metrik doplněna o mixin pro filtrování IP adres.

   **Metody:**

   .. py:method:: get()

      Zobrazí formulář nahrazení souboru po kontrole vazby souboru k záznamu.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``ExportToDjangoView()``, vstupuje do návratové hodnoty.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      **Návratová hodnota:**

      Vrací výsledek volání ``ExportToDjangoView()``.



.. py:class:: ApplicationRestartView

   Třída pohledu pro restartovani uwsgi aplikace.

   **Metody:**

   .. py:method:: post()

      Po POST požadavku přesměruje uživatele na bezpečnou návratovou URL.

      **Parametry:**

      - ``request``: Parametr ``request`` pracuje se s atributy ``user``, ``META``, ovlivňuje větvení podmínek.
      - ``args``: Parametr ``args`` slouží jako vstup pro logiku funkce ``post``.
      - ``kwargs``: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``post``.

      **Návratová hodnota:**

      Vrací výsledek volání ``redirect()``.

      **Výjimky:**

      - ``PermissionDenied``: Vyvolá se při splnění podmínky ``request.user.hlavni_role.id != ROLE_ADMIN_ID``.



.. py:class:: DataImportProgress

   Implementuje komponentu ``DataImportProgress`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
      - ``kwargs``: Parametr ``kwargs`` pracuje se s atributy ``get``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.

      **Výjimky:**

      - ``PermissionDenied``: Vyvolá se při splnění podmínky ``not request.user.is_superuser``.



.. py:class:: DataImportStop

   Implementuje komponentu ``DataImportStop`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
      - ``kwargs``: Parametr ``kwargs`` pracuje se s atributy ``get``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.

      **Výjimky:**

      - ``PermissionDenied``: Vyvolá se při splnění podmínky ``not request.user.is_superuser``.



.. py:class:: DataImportStart

   Implementuje komponentu ``DataImportStart`` v rámci aplikace.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``delay()``, pracuje se s atributy ``user``, ovlivňuje větvení podmínek.
      - ``kwargs``: Parametr ``kwargs`` pracuje se s atributy ``get``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.

      **Výjimky:**

      - ``PermissionDenied``: Vyvolá se při splnění podmínky ``not request.user.is_superuser``.



Funkce
------

.. py:function:: index(request)

   Zobrazí hlavní stránku aplikace po přihlášení uživatele.

   **Parametry:**

   - ``request``: HTTP požadavek aktuálního uživatele.

   **Návratová hodnota:**

   Vrací výsledek volání ``render()``.


.. py:function:: delete_file_DZ(request, typ_vazby, ident_cely, pk)

   Smaže soubor nahraný přes dropzone včetně záznamu v databázi i ve Fedora úložišti.

   **Parametry:**

   - ``request``: HTTP požadavek obsahující session identifikátor dropzone uploadu.
   - ``typ_vazby``: Typ vazby souboru na doménový objekt (např. dokument, projekt, PAS).
   - ``ident_cely``: Identifikátor záznamu, ke kterému je soubor navázán.
   - ``pk``: Primární klíč mazaného souboru.

   **Návratová hodnota:**

   Vrací výsledek volání ``JsonResponse()``.


.. py:function:: delete_file(request, typ_vazby, ident_cely, pk)

   Smaže existující soubor, jeho databázový záznam i binární obsah v repozitáři.

   **Parametry:**

   - ``request``: HTTP požadavek s metodou GET/POST a případnou návratovou URL.
   - ``typ_vazby``: Typ vazby souboru na navázaný doménový objekt.
   - ``ident_cely``: Identifikátor záznamu, u kterého se soubor odstraňuje.
   - ``pk``: Primární klíč mazaného souboru.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``redirect()``, výsledek volání ``JsonResponse()``, výsledek volání ``render()``.


.. py:function:: get_finds_soubor_name(find, filename, add_to_index)

   Funkce pro získaní jména souboru pro samostatný nález.

   **Parametry:**

   - ``find``: Textový název, klíč nebo výraz ``find`` používaný v rámci operace.
   - ``filename``: Parametr ``filename`` se předává do volání ``splitext()``, ``warning()``, vstupuje do návratové hodnoty.
   - ``add_to_index``: Číselná hodnota ``add_to_index`` použitá při výpočtu nebo transformaci.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, bool.


.. py:function:: get_projekt_soubor_name(projekt, file_name)

   Vygeneruje bezpečný název souboru pro upload do projektu.

   **Parametry:**

   - ``projekt``: Projekt, ke kterému se soubor nahrává.
   - ``file_name``: Původní název nahrávaného souboru.

   **Návratová hodnota:**

   Vrací hodnotu podle větve zpracování, typicky: bool, hodnotu podle větve zpracování.


.. py:function:: check_stav_changed(request, zaznam)

   Ověří, zda se stav záznamu mezitím změnil oproti hodnotě odeslané ve formuláři.

   **Parametry:**

   - ``request``: Parametr ``request`` předává se do volání ``CheckStavNotChangedForm()``, ``add_message()``, pracuje se s atributy ``method``, ``POST``, ovlivňuje větvení podmínek.
   - ``zaznam``: Ukládaný záznam, jehož stav se porovnává.

   **Návratová hodnota:**

   Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.


.. py:function:: redirect_ident_view(request, ident_cely)

   Přesměruje uživatele na detail záznamu nalezeného podle identifikátoru.
   Pokud identifikátor není nalezen mezi aktuálními, pokusí se hledat mezi dočasnými v historii.

   **Parametry:**

   - ``request``: Parametr ``request`` předává se do volání ``redirect()``, ``get_absolute_url()``, vstupuje do návratové hodnoty.
   - ``ident_cely``: Hledaný identifikátor záznamu.

   **Návratová hodnota:**

   Vrací výsledek volání ``redirect()``.


.. py:function:: prolong_session(request)

   Vrátí zbývající čas relace pro AJAX prodloužení přihlášení.

   **Parametry:**

   - ``request``: Parametr ``request`` předává se do volání ``seconds_until_idle_time_end()``.

   **Návratová hodnota:**

   Vrací výsledek volání ``JsonResponse()``.


.. py:function:: post_ajax_get_pas_and_pian_limit(request)

   Funkce pohledu pro získaní heatmapy.

   **Parametry:**

   - ``request``: Parametr ``request`` se předává do volání ``loads()``, ``get_pas_from_envelope()``, pracuje se s atributy ``body``.

   **Návratová hodnota:**

   Vrací výsledek volání ``JsonResponse()``.


.. py:function:: check_soubor_vazba(typ_vazby, ident, id_zaznamu)

   Ověří soubor vazba.

   **Parametry:**

   - ``typ_vazby``: Parametr ``typ_vazby`` ovlivňuje větvení podmínek.
   - ``ident``: Identifikátor ``ident`` používaný pro dohledání cílového záznamu.
   - ``id_zaznamu``: Parametr ``id_zaznamu`` předává se do volání ``filter()``.

   **Návratová hodnota:**

   Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.

   **Výjimky:**

   - ``ZaznamSouborNotmatching``: Vyvolá se při splnění podmínky ``soubor.count() > 0``.

