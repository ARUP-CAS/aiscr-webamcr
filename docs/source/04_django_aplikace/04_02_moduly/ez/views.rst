EZ views
========

Definice views.

Třídy
------

.. py:class:: ExterniZdrojIndexView

   Třida pohledu pro zobrazení domovské stránky externích zdrojů s navigačními možnostmi.

   **Metody:**

   .. py:method:: get_context_data()

      Vrátí kontext šablony s názvem panelu nástrojů pro domovskou stránku externích zdrojů.

      **Parametry:**

      - ``kwargs``: Dodatečné klíčové argumenty předávané nadřízené metodě.

      **Návratová hodnota:**

      Vrací proměnná ``context``.



.. py:class:: ExterniZdrojListView

   Třida pohledu pro zobrazení listu/tabulky s externím zdrojem.

   **Metody:**

   .. py:method:: init_translations()

      Inicializuje přeložené popisky stránek a záhlaví pro seznam externích zdrojů.

   .. py:method:: rename_field_for_ordering()

      Přeloží název pole z URL parametru na skutečný název databázového pole pro řazení.

      **Parametry:**

      - ``field``: Název pole z URL parametru řazení (může obsahovat prefix ``-`` pro sestupné řazení).

      **Návratová hodnota:**

      Vrací výsledek volání ``get()``.


   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      **Návratová hodnota:**

      Vrací výsledek volání ``check_filter_permission()``.


   .. py:method:: add_accessibility_lookup()

      Aplikuje filtrování přístupu na queryset externích zdrojů dle oprávnění uživatele.

      **Parametry:**

      - ``permission``: Objekt oprávnění určující úroveň přístupu uživatele.
      - ``qs``: Vstupní queryset externích zdrojů, který se filtruje.

      **Návratová hodnota:**

      Vrací proměnná ``qs``.



.. py:class:: ExterniZdrojDetailView

   Třida pohledu pro zobrazení detailu externího zdroju.

   **Metody:**

   .. py:method:: get_context_data()

      Vrátí kontext šablony s daty pro detail externího zdroje včetně připojených akcí a lokalit.

      **Parametry:**

      - ``kwargs``: Dodatečné klíčové argumenty předávané nadřízené metodě.

      **Návratová hodnota:**

      Vrací proměnná ``context``.



.. py:class:: ExterniZdrojCreateView

   Třida pohledu pro vytvoření externího zdroje.

   **Metody:**

   .. py:method:: get_form_kwargs()

      Vrací form kwargs.

      **Návratová hodnota:**

      Vrací proměnná ``kwargs``.


   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: form_valid()

      Uloží nový externí zdroj do databáze i Fedory a přesměruje na jeho detail.

      **Parametry:**

      - ``form``: Validovaný formulář pro vytvoření externího zdroje.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``HttpResponseRedirect()``, výsledek volání ``form_invalid()``.


   .. py:method:: form_invalid()

      Zobrazí chybovou zprávu a znovu vykreslí formulář při neúspěšném vytvoření externího zdroje.

      **Parametry:**

      - ``form``: Nevalidní formulář s chybami validace.

      **Návratová hodnota:**

      Vrací výsledek volání ``form_invalid()``.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
      - ``args``: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``get()``.



.. py:class:: ExterniZdrojEditView

   Třida pohledu pro editaci externího zdroje.

   **Metody:**

   .. py:method:: get_form_kwargs()

      Vrací form kwargs.

      **Návratová hodnota:**

      Vrací proměnná ``kwargs``.


   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: form_valid()

      Uloží změny externího zdroje do databáze a Fedory a přesměruje na jeho detail.

      **Parametry:**

      - ``form``: Validovaný formulář pro editaci externího zdroje.

      **Návratová hodnota:**

      Vrací výsledek volání ``HttpResponseRedirect()``.


   .. py:method:: form_invalid()

      Zobrazí chybovou zprávu a znovu vykreslí formulář při neúspěšné editaci externího zdroje.

      **Parametry:**

      - ``form``: Nevalidní formulář s chybami validace.

      **Návratová hodnota:**

      Vrací výsledek volání ``form_invalid()``.


   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
      - ``args``: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``get()``.


   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``post()``, vstupuje do návratové hodnoty.
      - ``args``: Parametr ``args`` se předává do volání ``post()``, vstupuje do návratové hodnoty.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``post()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek volání ``post()``.



.. py:class:: TransakceView

   Třida pohledu pro změnu stavu a práci s externíma zdrojama cez modal, která se dedí pro jednotlivá změny.

   **Metody:**

   .. py:method:: init_translation()

      Nastaví výchozí hodnoty popisků titulku a tlačítka pro modální dialog transakce.

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: get_context_data()

      Vrátí kontext šablony s daty pro modální dialog transakce externího zdroje.

      **Parametry:**

      - ``kwargs``: Dodatečné klíčové argumenty předávané nadřízené metodě.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: dispatch()

      Ověří, zda je stav externího zdroje povolený pro danou transakci, a zamítne přístup při neplatném stavu.

      **Parametry:**

      - ``request``: HTTP požadavek obsahující informace o uživateli.
      - ``args``: Dodatečné poziční argumenty předávané nadřízené metodě.
      - ``kwargs``: Dodatečné klíčové argumenty předávané nadřízené metodě.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``dispatch()``.


   .. py:method:: get()

      Zobrazí modální dialog pro transakci nad externím zdrojem.

      **Parametry:**

      - ``request``: HTTP požadavek.
      - ``args``: Dodatečné poziční argumenty.
      - ``kwargs``: Dodatečné klíčové argumenty předávané metodě ``get_context_data``.

      **Návratová hodnota:**

      Vrací výsledek volání ``render_to_response()``.


   .. py:method:: post()

      Provede transakci změny stavu externího zdroje a přesměruje na jeho detail.

      **Parametry:**

      - ``request``: HTTP požadavek obsahující informace o přihlášeném uživateli.
      - ``args``: Dodatečné poziční argumenty.
      - ``kwargs``: Dodatečné klíčové argumenty předávané metodě ``get_context_data``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: ExterniZdrojOdeslatView

   Třida pohledu pro odeslání externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Nastaví přeložené popisky titulku, tlačítka a zprávy o úspěchu pro odeslání externího zdroje.


.. py:class:: ExterniZdrojPotvrditView

   Třida pohledu pro potvrzení externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Nastaví přeložené popisky titulku, tlačítka a zprávy o úspěchu pro potvrzení externího zdroje.

   .. py:method:: post()

      Potvrdí externí zdroj a případně aktualizuje IGSN lokalit; při chybě provede rollback transakce.

      **Parametry:**

      - ``request``: HTTP požadavek obsahující informace o přihlášeném uživateli.
      - ``args``: Dodatečné poziční argumenty.
      - ``kwargs``: Dodatečné klíčové argumenty předávané metodě ``get_context_data``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: ExterniZdrojSmazatView

   Třida pohledu pro smazání externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Nastaví přeložené popisky titulku, tlačítka a zprávy o úspěchu pro smazání externího zdroje.

   .. py:method:: post()

      Smaže externí zdroj z databáze i Fedory; při existenci navázaných záznamů zamítne smazání.

      **Parametry:**

      - ``request``: HTTP požadavek obsahující informace o přihlášeném uživateli.
      - ``args``: Dodatečné poziční argumenty.
      - ``kwargs``: Dodatečné klíčové argumenty předávané metodě ``get_context_data``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: ExterniZdrojVratitView

   Třida pohledu pro vrácení externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Nastaví přeložené popisky titulku, tlačítka a zprávy o úspěchu pro vrácení externího zdroje.

   .. py:method:: get()

      Zobrazí modální dialog pro vrácení externího zdroje s formulářem pro zadání důvodu.

      **Parametry:**

      - ``request``: HTTP požadavek.
      - ``args``: Dodatečné poziční argumenty.
      - ``kwargs``: Dodatečné klíčové argumenty předávané metodě ``get_context_data``.

      **Návratová hodnota:**

      Vrací výsledek volání ``render_to_response()``.


   .. py:method:: post()

      Vrátí externí zdroj do předchozího stavu s důvodem; při neplatném formuláři znovu zobrazí dialog.

      **Parametry:**

      - ``request``: HTTP požadavek obsahující POST data s důvodem vrácení.
      - ``args``: Dodatečné poziční argumenty.
      - ``kwargs``: Dodatečné klíčové argumenty předávané metodě ``get_context_data``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render_to_response()``.



.. py:class:: ExterniOdkazOdpojitView

   Třida pohledu pro odpojení externího odkazu pomoci modalu.

   **Metody:**

   .. py:method:: dispatch()

      Ověří, zda odpojovaný externí odkaz patří k danému externímu zdroji, a zamítne přístup při nesouladu.

      **Parametry:**

      - ``request``: HTTP požadavek.
      - ``args``: Dodatečné poziční argumenty předávané nadřízené metodě.
      - ``kwargs``: Dodatečné klíčové argumenty předávané nadřízené metodě.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: init_translation()

      Nastaví přeložené popisky titulku, tlačítka a zprávy o úspěchu pro odpojení externího odkazu.

   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: post()

      Odpojí externí odkaz od externího zdroje a případně aktualizuje IGSN archivované lokality.

      **Parametry:**

      - ``request``: HTTP požadavek obsahující informace o přihlášeném uživateli.
      - ``args``: Dodatečné poziční argumenty.
      - ``kwargs``: Dodatečné klíčové argumenty.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: ExterniOdkazPripojitView

   Třida pohledu pro připojení externího odkazu pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Nastaví přeložené popisky titulku a tlačítka pro připojení externího odkazu k externímu zdroji.

   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: post()

      Připojí archeologický záznam k externímu zdroji vytvořením nového externího odkazu.

      **Parametry:**

      - ``request``: HTTP požadavek obsahující POST data s identifikátorem archeologického záznamu.
      - ``args``: Dodatečné poziční argumenty.
      - ``kwargs``: Dodatečné klíčové argumenty předávané metodě ``get_context_data``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: ExterniOdkazEditView

   Třida pohledu pro editaci externího odkazu pomoci modalu.

   **Metody:**

   .. py:method:: dispatch()

      Ověří, zda editovaný externí odkaz patří k zadanému záznamu dle typu vazby, a zamítne přístup při nesouladu.

      **Parametry:**

      - ``request``: HTTP požadavek.
      - ``args``: Dodatečné poziční argumenty předávané nadřízené metodě.
      - ``kwargs``: Dodatečné klíčové argumenty předávané nadřízené metodě.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: get_success_url()

      Vrací success url.

      **Návratová hodnota:**

      Vrací proměnná ``response``.


   .. py:method:: get_object()

      Vrátí instanci externího odkazu a nastaví jí aktivní Fedora transakci, pokud existuje.

      **Parametry:**

      - ``queryset``: Volitelný queryset pro vyhledání objektu; pokud není zadán, použije se výchozí.

      **Návratová hodnota:**

      Vrací proměnná ``object``.


   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``create_transaction()``, ``post()``, pracuje se s atributy ``user``.
      - ``args``: Parametr ``args`` se předává do volání ``post()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``post()``.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.


   .. py:method:: form_valid()

      Uloží změny externího odkazu a zobrazí zprávu o úspěšném uložení.

      **Parametry:**

      - ``form``: Validovaný formulář pro editaci externího odkazu.

      **Návratová hodnota:**

      Vrací výsledek volání ``form_valid()``.


   .. py:method:: form_invalid()

      Zobrazí chybovou zprávu a znovu vykreslí formulář při neúspěšné editaci externího odkazu.

      **Parametry:**

      - ``form``: Nevalidní formulář s chybami validace.

      **Návratová hodnota:**

      Vrací výsledek volání ``form_invalid()``.



.. py:class:: ExterniOdkazOdpojitAZView

   Třida pohledu pro odpojení externího odkazu z archeologického záznamu pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Nastaví zprávu o úspěchu pro odpojení externího odkazu z archeologického záznamu.

   .. py:method:: dispatch()

      Ověří, zda odpojovaný externí odkaz patří k danému archeologickému záznamu, a zamítne přístup při nesouladu.

      **Parametry:**

      - ``request``: HTTP požadavek.
      - ``args``: Dodatečné poziční argumenty předávané nadřízené metodě.
      - ``kwargs``: Dodatečné klíčové argumenty předávané nadřízené metodě.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      **Návratová hodnota:**

      Vrací výsledek volání ``get_object_or_404()``.


   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: post()

      Odpojí externí odkaz od archeologického záznamu a případně aktualizuje IGSN archivované lokality.

      **Parametry:**

      - ``request``: HTTP požadavek obsahující informace o přihlášeném uživateli.
      - ``args``: Dodatečné poziční argumenty.
      - ``kwargs``: Dodatečné klíčové argumenty.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: ExterniZdrojAutocomplete

   Třída pohledu pro autocomplete externích zdrojů.

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


   .. py:method:: add_accessibility_lookup()

      Aplikuje filtrování přístupu na queryset externích zdrojů pro autocomplete dle oprávnění uživatele.

      **Parametry:**

      - ``permission``: Objekt oprávnění určující úroveň přístupu uživatele.
      - ``qs``: Vstupní queryset externích zdrojů, který se filtruje.

      **Návratová hodnota:**

      Vrací proměnná ``qs``.



.. py:class:: ExterniZdrojTableRowView

   Třída pohledu pro získaní řádku tabulky s externím zdrojem.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``get()``, pracuje se s atributy ``GET``.

      **Návratová hodnota:**

      Vrací výsledek volání ``HttpResponse()``.



.. py:class:: ExterniOdkazPripojitDoAzView

   Třída pohledu pro připojení externího odkazu do arch záznamu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      **Návratová hodnota:**

      Vrací proměnná ``zaznam``.


   .. py:method:: get_context_data()

      Vrací context data.

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

      **Návratová hodnota:**

      Vrací proměnná ``context``.


   .. py:method:: post()

      Připojí externí odkaz k archeologickému záznamu a uloží propojení do databáze a Fedory.

      **Parametry:**

      - ``request``: HTTP požadavek obsahující POST data s identifikátorem externího zdroje a paginací.
      - ``args``: Dodatečné poziční argumenty.
      - ``kwargs``: Dodatečné klíčové argumenty.

      **Návratová hodnota:**

      Vrací výsledek volání ``JsonResponse()``.



.. py:class:: EzOdkazyTableView

   Třída pohledu pro zobrazení řádků tabulky externích odkazů.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      **Parametry:**

      - ``request``: Parametr ``request`` předává se do volání ``check_permissions()``, pracuje se s atributy ``GET``, ``user``.
      - ``ident_cely``: Parametr ``ident_cely`` se předává do volání ``get()``.

      **Návratová hodnota:**

      Vrací výsledek volání ``HttpResponse()``.



Funkce
------

.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní historických datumu.

   **Parametry:**

   - ``historie_vazby``: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
   - ``request_user``: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.

   **Návratová hodnota:**

   Slovník dat jednotlivých změn stavu pro zobrazení v historii.


.. py:function:: get_detail_template_shows(zaznam, user)

   Funkce pro získaní kontextu pro zobrazování možností na stránkách.

   **Parametry:**

   - ``zaznam``: Parametr ``zaznam`` předává se do volání ``check_permissions()``, pracuje se s atributy ``stav``, ``ident_cely``.
   - ``user``: Parametr ``user`` se předává do volání ``check_permissions()``.

   **Návratová hodnota:**

   Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.


.. py:function:: get_required_fields()

   Funkce pro získaní dictionary povinných polí podle stavu externího zdroje.

   **Návratová hodnota:**

   Vrací proměnná ``required_fields``.


.. py:function:: save_autor_editor(zaznam, form)

   Funkce pro uložení autorů a editorů k externímu zdroji podle toho v jakém pořadí byly zadáni.

   **Parametry:**

   - ``zaznam``: Parametr ``zaznam`` předává se do volání ``create()``.
   - ``form``: Parametr ``form`` pracuje se s atributy ``cleaned_data``.

