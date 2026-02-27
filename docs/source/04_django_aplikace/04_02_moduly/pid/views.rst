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
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: _get_value_from_cache()

      Vrací value from cache.

      :param key: Vstupní hodnota ``key`` pro danou operaci.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _save_value_to_cache()

      Uloží value to cache.

      :param key: Vstupní hodnota ``key`` pro danou operaci.
      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: api_call()

      Provádí operaci api call.

      :param q: Vstupní hodnota ``q`` pro danou operaci.
      :param use_cache: Vstupní hodnota ``use_cache`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get()

      Vrací výsledek operace.

      :param request: Django HTTP požadavek použitý při zpracování.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: autocomplete_results()

      Provádí operaci autocomplete results.

      :param results: Vstupní hodnota ``results`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: get_list()

      Vrací list.

      :return: Vrací načtená data odpovídající vstupním parametrům.


.. py:class:: DoiAutocompleteView

   Implementuje komponentu ``DoiAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: _api_call_data_cite()

      Provádí operaci api call data cite.

      :param q: Vstupní hodnota ``q`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _api_call_cross_ref_doi()

      Provádí operaci api call cross ref doi.

      :param q: Vstupní hodnota ``q`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _api_call_cross_ref_title()

      Provádí operaci api call cross ref title.

      :param q: Vstupní hodnota ``q`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: _doi_item_exists()

      Provádí operaci doi item exists.

      :param doi: Vstupní hodnota ``doi`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: api_call()

      Provádí operaci api call.

      :param q: Vstupní hodnota ``q`` pro danou operaci.
      :param use_cache: Vstupní hodnota ``use_cache`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: OrcidAutocompleteView

   Implementuje komponentu ``OrcidAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: api_call()

      Provádí operaci api call.

      :param q: Vstupní hodnota ``q`` pro danou operaci.
      :param use_cache: Vstupní hodnota ``use_cache`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: RorAutocompleteView

   Implementuje komponentu ``RorAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: api_call()

      Provádí operaci api call.

      :param q: Vstupní hodnota ``q`` pro danou operaci.
      :param use_cache: Vstupní hodnota ``use_cache`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: WikiDataAutocompleteView

   Implementuje komponentu ``WikiDataAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: api_call()

      Provádí operaci api call.

      :param q: Vstupní hodnota ``q`` pro danou operaci.
      :param use_cache: Vstupní hodnota ``use_cache`` pro danou operaci.
      :return: Vrací výsledek provedené operace.


.. py:class:: ContinuePidProcessing

   Implementuje komponentu ``ContinuePidProcessing`` v rámci aplikace.

   **Metody:**

   .. py:method:: _perform_client_action()

      Provádí operaci perform client action.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :param attribute_name: Vstupní hodnota ``attribute_name`` pro danou operaci.
      :param publish_callable_method: Vstupní hodnota ``publish_callable_method`` pro danou operaci.
      :param set_callable_method: Vstupní hodnota ``set_callable_method`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: process_record()

      Provádí operaci process record.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :param result: Vstupní hodnota ``result`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Vrací výsledek provedené operace.

