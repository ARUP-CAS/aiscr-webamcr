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

      :param kwargs: Dodatečné klíčové argumenty předávané nadřízené metodě.

          :return: Vrací proměnná ``context``.


.. py:class:: ExterniZdrojListView

   Třida pohledu pro zobrazení listu/tabulky s externím zdrojem.

   **Metody:**

   .. py:method:: init_translations()

      Inicializuje přeložené popisky stránek a záhlaví pro seznam externích zdrojů.

   .. py:method:: rename_field_for_ordering()

      Přeloží název pole z URL parametru na skutečný název databázového pole pro řazení.

      :param field: Název pole z URL parametru řazení (může obsahovat prefix ``-`` pro sestupné řazení).

          :return: Vrací výsledek volání ``get()``.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací výsledek volání ``check_filter_permission()``.

   .. py:method:: add_accessibility_lookup()

      Aplikuje filtrování přístupu na queryset externích zdrojů dle oprávnění uživatele.

      :param permission: Objekt oprávnění určující úroveň přístupu uživatele.
      :param qs: Vstupní queryset externích zdrojů, který se filtruje.

          :return: Vrací proměnná ``qs``.


.. py:class:: ExterniZdrojDetailView

   Třida pohledu pro zobrazení detailu externího zdroju.

   **Metody:**

   .. py:method:: get_context_data()

      Vrátí kontext šablony s daty pro detail externího zdroje včetně připojených akcí a lokalit.

      :param kwargs: Dodatečné klíčové argumenty předávané nadřízené metodě.

          :return: Vrací proměnná ``context``.


.. py:class:: ExterniZdrojCreateView

   Třida pohledu pro vytvoření externího zdroje.

   **Metody:**

   .. py:method:: get_form_kwargs()

      Vrací form kwargs.

      :return: Vrací proměnná ``kwargs``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

          :return: Vrací proměnná ``context``.

   .. py:method:: form_valid()

      Uloží nový externí zdroj do databáze i Fedory a přesměruje na jeho detail.

      :param form: Validovaný formulář pro vytvoření externího zdroje.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``HttpResponseRedirect()``, výsledek volání ``form_invalid()``.

   .. py:method:: form_invalid()

      Zobrazí chybovou zprávu a znovu vykreslí formulář při neúspěšném vytvoření externího zdroje.

      :param form: Nevalidní formulář s chybami validace.

          :return: Vrací výsledek volání ``form_invalid()``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``get()``.


.. py:class:: ExterniZdrojEditView

   Třida pohledu pro editaci externího zdroje.

   **Metody:**

   .. py:method:: get_form_kwargs()

      Vrací form kwargs.

      :return: Vrací proměnná ``kwargs``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

          :return: Vrací proměnná ``context``.

   .. py:method:: form_valid()

      Uloží změny externího zdroje do databáze a Fedory a přesměruje na jeho detail.

      :param form: Validovaný formulář pro editaci externího zdroje.

          :return: Vrací výsledek volání ``HttpResponseRedirect()``.

   .. py:method:: form_invalid()

      Zobrazí chybovou zprávu a znovu vykreslí formulář při neúspěšné editaci externího zdroje.

      :param form: Nevalidní formulář s chybami validace.

          :return: Vrací výsledek volání ``form_invalid()``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``get()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``get()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``get()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``get()``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``post()``, vstupuje do návratové hodnoty.
      :param args: Parametr ``args`` se předává do volání ``post()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``post()``, vstupuje do návratové hodnoty.

          :return: Vrací výsledek volání ``post()``.


.. py:class:: TransakceView

   Třida pohledu pro změnu stavu a práci s externíma zdrojama cez modal, která se dedí pro jednotlivá změny.

   **Metody:**

   .. py:method:: init_translation()

      Nastaví výchozí hodnoty popisků titulku a tlačítka pro modální dialog transakce.

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: get_context_data()

      Vrátí kontext šablony s daty pro modální dialog transakce externího zdroje.

      :param kwargs: Dodatečné klíčové argumenty předávané nadřízené metodě.

          :return: Vrací proměnná ``context``.

   .. py:method:: dispatch()

      Ověří, zda je stav externího zdroje povolený pro danou transakci, a zamítne přístup při neplatném stavu.

      :param request: HTTP požadavek obsahující informace o uživateli.
      :param args: Dodatečné poziční argumenty předávané nadřízené metodě.
      :param kwargs: Dodatečné klíčové argumenty předávané nadřízené metodě.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``dispatch()``.

   .. py:method:: get()

      Zobrazí modální dialog pro transakci nad externím zdrojem.

      :param request: HTTP požadavek.
      :param args: Dodatečné poziční argumenty.
      :param kwargs: Dodatečné klíčové argumenty předávané metodě ``get_context_data``.

          :return: Vrací výsledek volání ``render_to_response()``.

   .. py:method:: post()

      Provede transakci změny stavu externího zdroje a přesměruje na jeho detail.

      :param request: HTTP požadavek obsahující informace o přihlášeném uživateli.
      :param args: Dodatečné poziční argumenty.
      :param kwargs: Dodatečné klíčové argumenty předávané metodě ``get_context_data``.

          :return: Vrací výsledek volání ``JsonResponse()``.


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

      :param request: HTTP požadavek obsahující informace o přihlášeném uživateli.
      :param args: Dodatečné poziční argumenty.
      :param kwargs: Dodatečné klíčové argumenty předávané metodě ``get_context_data``.

          :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: ExterniZdrojSmazatView

   Třida pohledu pro smazání externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Nastaví přeložené popisky titulku, tlačítka a zprávy o úspěchu pro smazání externího zdroje.

   .. py:method:: post()

      Smaže externí zdroj z databáze i Fedory; při existenci navázaných záznamů zamítne smazání.

      :param request: HTTP požadavek obsahující informace o přihlášeném uživateli.
      :param args: Dodatečné poziční argumenty.
      :param kwargs: Dodatečné klíčové argumenty předávané metodě ``get_context_data``.

          :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: ExterniZdrojVratitView

   Třida pohledu pro vrácení externího zdroje pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Nastaví přeložené popisky titulku, tlačítka a zprávy o úspěchu pro vrácení externího zdroje.

   .. py:method:: get()

      Zobrazí modální dialog pro vrácení externího zdroje s formulářem pro zadání důvodu.

      :param request: HTTP požadavek.
      :param args: Dodatečné poziční argumenty.
      :param kwargs: Dodatečné klíčové argumenty předávané metodě ``get_context_data``.

          :return: Vrací výsledek volání ``render_to_response()``.

   .. py:method:: post()

      Vrátí externí zdroj do předchozího stavu s důvodem; při neplatném formuláři znovu zobrazí dialog.

      :param request: HTTP požadavek obsahující POST data s důvodem vrácení.
      :param args: Dodatečné poziční argumenty.
      :param kwargs: Dodatečné klíčové argumenty předávané metodě ``get_context_data``.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``JsonResponse()``, výsledek volání ``render_to_response()``.


.. py:class:: ExterniOdkazOdpojitView

   Třida pohledu pro odpojení externího odkazu pomoci modalu.

   **Metody:**

   .. py:method:: dispatch()

      Ověří, zda odpojovaný externí odkaz patří k danému externímu zdroji, a zamítne přístup při nesouladu.

      :param request: HTTP požadavek.
      :param args: Dodatečné poziční argumenty předávané nadřízené metodě.
      :param kwargs: Dodatečné klíčové argumenty předávané nadřízené metodě.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: init_translation()

      Nastaví přeložené popisky titulku, tlačítka a zprávy o úspěchu pro odpojení externího odkazu.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

          :return: Vrací proměnná ``context``.

   .. py:method:: post()

      Odpojí externí odkaz od externího zdroje a případně aktualizuje IGSN archivované lokality.

      :param request: HTTP požadavek obsahující informace o přihlášeném uživateli.
      :param args: Dodatečné poziční argumenty.
      :param kwargs: Dodatečné klíčové argumenty.

          :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: ExterniOdkazPripojitView

   Třida pohledu pro připojení externího odkazu pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Nastaví přeložené popisky titulku a tlačítka pro připojení externího odkazu k externímu zdroji.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

          :return: Vrací proměnná ``context``.

   .. py:method:: post()

      Připojí archeologický záznam k externímu zdroji vytvořením nového externího odkazu.

      :param request: HTTP požadavek obsahující POST data s identifikátorem archeologického záznamu.
      :param args: Dodatečné poziční argumenty.
      :param kwargs: Dodatečné klíčové argumenty předávané metodě ``get_context_data``.

          :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: ExterniOdkazEditView

   Třida pohledu pro editaci externího odkazu pomoci modalu.

   **Metody:**

   .. py:method:: dispatch()

      Ověří, zda editovaný externí odkaz patří k zadanému záznamu dle typu vazby, a zamítne přístup při nesouladu.

      :param request: HTTP požadavek.
      :param args: Dodatečné poziční argumenty předávané nadřízené metodě.
      :param kwargs: Dodatečné klíčové argumenty předávané nadřízené metodě.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

          :return: Vrací proměnná ``context``.

   .. py:method:: get_success_url()

      Vrací success url.

      :return: Vrací proměnná ``response``.

   .. py:method:: get_object()

      Vrátí instanci externího odkazu a nastaví jí aktivní Fedora transakci, pokud existuje.

      :param queryset: Volitelný queryset pro vyhledání objektu; pokud není zadán, použije se výchozí.

          :return: Vrací proměnná ``object``.

   .. py:method:: post()

      Obsluhuje HTTP metodu POST.

      :param request: Parametr ``request`` předává se do volání ``create_transaction()``, ``post()``, pracuje se s atributy ``user``.
      :param args: Parametr ``args`` se předává do volání ``post()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``post()``.

          :return: Vrací výsledek volání ``JsonResponse()``.

   .. py:method:: form_valid()

      Uloží změny externího odkazu a zobrazí zprávu o úspěšném uložení.

      :param form: Validovaný formulář pro editaci externího odkazu.

          :return: Vrací výsledek volání ``form_valid()``.

   .. py:method:: form_invalid()

      Zobrazí chybovou zprávu a znovu vykreslí formulář při neúspěšné editaci externího odkazu.

      :param form: Nevalidní formulář s chybami validace.

          :return: Vrací výsledek volání ``form_invalid()``.


.. py:class:: ExterniOdkazOdpojitAZView

   Třida pohledu pro odpojení externího odkazu z archeologického záznamu pomoci modalu.

   **Metody:**

   .. py:method:: init_translation()

      Nastaví zprávu o úspěchu pro odpojení externího odkazu z archeologického záznamu.

   .. py:method:: dispatch()

      Ověří, zda odpojovaný externí odkaz patří k danému archeologickému záznamu, a zamítne přístup při nesouladu.

      :param request: HTTP požadavek.
      :param args: Dodatečné poziční argumenty předávané nadřízené metodě.
      :param kwargs: Dodatečné klíčové argumenty předávané nadřízené metodě.

      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      :return: Vrací výsledek volání ``get_object_or_404()``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

          :return: Vrací proměnná ``context``.

   .. py:method:: post()

      Odpojí externí odkaz od archeologického záznamu a případně aktualizuje IGSN archivované lokality.

      :param request: HTTP požadavek obsahující informace o přihlášeném uživateli.
      :param args: Dodatečné poziční argumenty.
      :param kwargs: Dodatečné klíčové argumenty.

          :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: ExterniZdrojAutocomplete

   Třída pohledu pro autocomplete externích zdrojů.

   **Metody:**

   .. py:method:: get_result_label()

      Vrací result label.

      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.

          :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``none()``, výsledek volání ``check_filter_permission()``.

   .. py:method:: add_accessibility_lookup()

      Aplikuje filtrování přístupu na queryset externích zdrojů pro autocomplete dle oprávnění uživatele.

      :param permission: Objekt oprávnění určující úroveň přístupu uživatele.
      :param qs: Vstupní queryset externích zdrojů, který se filtruje.

          :return: Vrací proměnná ``qs``.


.. py:class:: ExterniZdrojTableRowView

   Třída pohledu pro získaní řádku tabulky s externím zdrojem.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``get()``, pracuje se s atributy ``GET``.

          :return: Vrací výsledek volání ``HttpResponse()``.


.. py:class:: ExterniOdkazPripojitDoAzView

   Třída pohledu pro připojení externího odkazu do arch záznamu.

   **Metody:**

   .. py:method:: get_zaznam()

      Vrací zaznam. v aplikaci.

      :return: Vrací proměnná ``zaznam``.

   .. py:method:: get_context_data()

      Vrací context data.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``get_context_data()``.

          :return: Vrací proměnná ``context``.

   .. py:method:: post()

      Připojí externí odkaz k archeologickému záznamu a uloží propojení do databáze a Fedory.

      :param request: HTTP požadavek obsahující POST data s identifikátorem externího zdroje a paginací.
      :param args: Dodatečné poziční argumenty.
      :param kwargs: Dodatečné klíčové argumenty.

          :return: Vrací výsledek volání ``JsonResponse()``.


.. py:class:: EzOdkazyTableView

   Třída pohledu pro zobrazení řádků tabulky externích odkazů.

   **Metody:**

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` předává se do volání ``check_permissions()``, pracuje se s atributy ``GET``, ``user``.
      :param ident_cely: Parametr ``ident_cely`` se předává do volání ``get()``.

          :return: Vrací výsledek volání ``HttpResponse()``.


Funkce
------

.. py:function:: get_history_dates(historie_vazby, request_user)

   Funkce pro získaní historických datumu.

   :param historie_vazby: Kolekce ``historie_vazby`` zpracovávaná touto funkcí.
   :param request_user: Uživatel nebo osoba ``request_user``, v jejímž kontextu se operace provádí.
   :return: Slovník dat jednotlivých změn stavu pro zobrazení v historii.

.. py:function:: get_detail_template_shows(zaznam, user)

   Funkce pro získaní kontextu pro zobrazování možností na stránkách.

   :param zaznam: Parametr ``zaznam`` předává se do volání ``check_permissions()``, pracuje se s atributy ``stav``, ``ident_cely``.
   :param user: Parametr ``user`` se předává do volání ``check_permissions()``.
   :return: Slovník příznaků určujících, které akce a sekce detailu se mají zobrazit.

.. py:function:: get_required_fields()

   Funkce pro získaní dictionary povinných polí podle stavu externího zdroje.

       :return: Vrací proměnná ``required_fields``.

.. py:function:: save_autor_editor(zaznam, form)

   Funkce pro uložení autorů a editorů k externímu zdroji podle toho v jakém pořadí byly zadáni.

   :param zaznam: Parametr ``zaznam`` předává se do volání ``create()``.
   :param form: Parametr ``form`` pracuje se s atributy ``cleaned_data``.
