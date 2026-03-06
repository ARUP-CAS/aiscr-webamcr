PID views
=========

Definice views.

Třídy
------

.. py:class:: ApiView

   Implementuje komponentu ``ApiView`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: _get_value_from_cache()

      Vrací value from cache.

      :param key: Textový název nebo klíč ``key`` používaný v rámci operace.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _save_value_to_cache()

      Uloží value to cache.

      :param key: Textový název nebo klíč ``key`` používaný v rámci operace.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: api_call()

      Provádí operaci api call.

      :param q: Vyhledávací dotaz použitý pro filtrování/autocomplete výsledků.
      :param use_cache: Příznak ``use_cache`` určující průběh nebo rozsah zpracování.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: autocomplete_results()

      Provádí operaci autocomplete results.

      :param results: Kolekce ``results`` zpracovávaná touto funkcí.

   .. py:method:: get_list()

      Vrací list. v aplikaci.


.. py:class:: DoiAutocompleteView

   Implementuje komponentu ``DoiAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: _api_call_data_cite()

      Provádí operaci api call data cite.

      :param q: Vyhledávací dotaz použitý pro filtrování/autocomplete výsledků.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _api_call_cross_ref_doi()

      Provádí operaci api call cross ref doi.

      :param q: Vyhledávací dotaz použitý pro filtrování/autocomplete výsledků.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _api_call_cross_ref_title()

      Provádí operaci api call cross ref title.

      :param q: Vyhledávací dotaz použitý pro filtrování/autocomplete výsledků.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: _doi_item_exists()

      Provádí operaci doi item exists.

      :param doi: Textová hodnota `doi` používaná pro vyhledání, pojmenování nebo hlášení stavu.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: api_call()

      Provádí operaci api call.

      :param q: Vyhledávací dotaz použitý pro filtrování/autocomplete výsledků.
      :param use_cache: Příznak ``use_cache`` určující průběh nebo rozsah zpracování.


.. py:class:: OrcidAutocompleteView

   Implementuje komponentu ``OrcidAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: api_call()

      Provádí operaci api call.

      :param q: Vyhledávací dotaz použitý pro filtrování/autocomplete výsledků.
      :param use_cache: Příznak ``use_cache`` určující průběh nebo rozsah zpracování.


.. py:class:: RorAutocompleteView

   Implementuje komponentu ``RorAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: api_call()

      Provádí operaci api call.

      :param q: Vyhledávací dotaz použitý pro filtrování/autocomplete výsledků.
      :param use_cache: Příznak ``use_cache`` určující průběh nebo rozsah zpracování.


.. py:class:: WikiDataAutocompleteView

   Implementuje komponentu ``WikiDataAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: api_call()

      Provádí operaci api call.

      :param q: Vyhledávací dotaz použitý pro filtrování/autocomplete výsledků.
      :param use_cache: Příznak ``use_cache`` určující průběh nebo rozsah zpracování.


.. py:class:: ContinuePidProcessing

   Implementuje komponentu ``ContinuePidProcessing`` v rámci aplikace.

   **Metody:**

   .. py:method:: _perform_client_action()

      Provádí operaci perform client action.

      :param record: Záznam, který funkce čte nebo upravuje.
      :param attribute_name: Textový název nebo klíč ``attribute_name`` používaný v rámci operace.
      :param publish_callable_method: Číselná nebo geometrická hodnota `publish_callable_method` použitá při výpočtu nebo transformaci.
      :param set_callable_method: Kolekce ``set_callable_method`` zpracovávaná touto funkcí.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: process_record()

      Provádí operaci process record.

      :param record: Záznam, který funkce čte nebo upravuje.
      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

