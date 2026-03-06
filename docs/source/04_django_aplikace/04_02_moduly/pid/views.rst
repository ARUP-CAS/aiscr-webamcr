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

      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: _get_value_from_cache()

      Vrací value from cache.

      :param key: Textový název nebo klíč ``key`` používaný v rámci operace.
      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _save_value_to_cache()

      Uloží value to cache.

      :param key: Textový název nebo klíč ``key`` používaný v rámci operace.
      :param value: Parametr ``value`` předává se do volání ``set()``.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: api_call()

      Provádí operaci api call.

      :param q: Vyhledávací dotaz použitý pro filtrování/autocomplete výsledků.
      :param use_cache: Parametr ``use_cache`` slouží jako vstup pro logiku funkce ``api_call``.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get``.
      :param args: Parametr ``args`` slouží jako vstup pro logiku funkce ``get``.
      :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``get``.

      :return: Vrací výsledek volání ``JsonResponse()``.

   .. py:method:: autocomplete_results()

      Provádí operaci autocomplete results.

      :param results: Kolekce ``results`` zpracovávaná touto funkcí.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: get_list()

      Vrací list. v aplikaci.

      :return: Vrací výsledek volání ``api_call()``.


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
      :param use_cache: Parametr ``use_cache`` slouží jako vstup pro logiku funkce ``api_call``.

      :return: Vrací proměnná ``results``.


.. py:class:: OrcidAutocompleteView

   Implementuje komponentu ``OrcidAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: api_call()

      Provádí operaci api call.

      :param q: Vyhledávací dotaz použitý pro filtrování/autocomplete výsledků.
      :param use_cache: Parametr ``use_cache`` ovlivňuje větvení podmínek.

      :return: Vrací hodnotu podle větve zpracování, typicky: seznam, proměnná ``result_list``.


.. py:class:: RorAutocompleteView

   Implementuje komponentu ``RorAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: api_call()

      Provádí operaci api call.

      :param q: Vyhledávací dotaz použitý pro filtrování/autocomplete výsledků.
      :param use_cache: Parametr ``use_cache`` slouží jako vstup pro logiku funkce ``api_call``.

      :return: Vrací proměnná ``result_list``.


.. py:class:: WikiDataAutocompleteView

   Implementuje komponentu ``WikiDataAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: api_call()

      Provádí operaci api call.

      :param q: Vyhledávací dotaz použitý pro filtrování/autocomplete výsledků.
      :param use_cache: Parametr ``use_cache`` slouží jako vstup pro logiku funkce ``api_call``.

      :return: Vrací hodnotu podle větve zpracování, typicky: seznam, proměnná ``result_list``.


.. py:class:: ContinuePidProcessing

   Implementuje komponentu ``ContinuePidProcessing`` v rámci aplikace.

   **Metody:**

   .. py:method:: _perform_client_action()

      Provádí operaci perform client action.

      :param record: Parametr ``record`` předává se do volání ``isinstance()``, pracuje se s atributy ``save``, ``lokalita``, ovlivňuje větvení podmínek.
      :param attribute_name: Textový název nebo klíč ``attribute_name`` používaný v rámci operace.
      :param publish_callable_method: Parametr ``publish_callable_method`` slouží jako vstup pro logiku funkce ``_perform_client_action``.
      :param set_callable_method: Kolekce ``set_callable_method`` zpracovávaná touto funkcí.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: process_record()

      Provádí operaci process record.

      :param record: Parametr ``record`` předává se do volání ``isinstance()``, ``_perform_client_action()``, pracuje se s atributy ``active_transaction``, ``doi``, ovlivňuje větvení podmínek.
      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.
      :param kwargs: Parametr ``kwargs`` pracuje se s atributy ``get``.

      :return: Vrací proměnná ``result``.

