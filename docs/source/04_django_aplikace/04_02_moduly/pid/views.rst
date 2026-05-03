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

      Zavolá API dotaz pro autocomplete (abstraktní metoda).

      :param q: Vyhledávací dotaz od uživatele.
      :param use_cache: Zda používat mezipaměť výsledků.

   .. py:method:: get()

      Vrací JSON odpověď s autocomplete výsledky.

      :param request: HTTP požadavek ze strany klienta.
      :param args: Poziční argumenty z URL.
      :param kwargs: Pojmenované argumenty z URL.
      :return: JSON odpověď s výsledky.

   .. py:method:: autocomplete_results()

      Transformuje výsledky API na formát autocomplete (id, text).

      :param results: Výsledky vrácené API voláním.
      :return: Seznam tuples (id, text) pro autocomplete.

   .. py:method:: get_list()

      Vrací list. v aplikaci.

      :return: Vrací výsledek volání ``api_call()``.


.. py:class:: DoiAutocompleteView

   Implementuje komponentu ``DoiAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: _api_call_cross_ref_doi()

      Vyhledá DOI v CrossRef API pomocí přímého DOI.

      :param q: Vyhledávací dotaz (DOI).
      :return: Seznam [DOI, název] párů.

   .. py:method:: _doi_item_exists()

      Ověří existenci DOI pomocí HTTP HEAD požadavku.

      :param doi: DOI identifikátor.
      :return: Seznam [DOI, DOI] pokud existuje, jinak prázdný seznam.

   .. py:method:: api_call()

      Vyhledá DOI v CrossRef a DataCite API.

      :param q: Vyhledávací dotaz.
      :param use_cache: Zda používat cache.
      :return: Seznam [DOI, název] párů.


.. py:class:: OrcidAutocompleteView

   Implementuje komponentu ``OrcidAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: api_call()

      Vyhledá výzkumné pracovníky v ORCID API.

      :param q: Vyhledávací dotaz.
      :param use_cache: Zda používat cache.
      :return: Seznam [ORCID ID, jméno] párů.


.. py:class:: RorAutocompleteView

   Implementuje komponentu ``RorAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: api_call()

      Vyhledá organizace v ROR API.

      :param q: Vyhledávací dotaz.
      :param use_cache: Zda používat cache.
      :return: Seznam [ROR ID, jméno] párů.


.. py:class:: WikiDataAutocompleteView

   Implementuje komponentu ``WikiDataAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: api_call()

      Vyhledá osoby v WikiData SPARQL API.

      :param q: Vyhledávací dotaz.
      :param use_cache: Zda používat cache.
      :return: Seznam [WikiData ID, jméno] párů.


.. py:class:: ContinuePidProcessing

   Implementuje komponentu ``ContinuePidProcessing`` v rámci aplikace.

   **Metody:**

   .. py:method:: _perform_client_action()

      Provede akci na záznamu a publikuje do DataCite.

      :param record: Záznam k publikaci (Lokalita, SamostatnyNalez nebo Dokument).
      :param attribute_name: Atribut záznamu pro uložení DOI.
      :param publish_callable_method: Callable pro publikaci.
      :param set_callable_method: Callable pro nastavení stavu.
      :return: DOI nebo chybová zpráva.

   .. py:method:: process_record()

      Zpracuje záznam pro publikaci/skrytí/smazání PID.

      :param record: Záznam k publikaci.
      :param result: Výsledek formuláře.
      :param result: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.
      :param kwargs: Parametr ``kwargs`` pracuje se s atributy ``get``.

      :return: Vrací proměnná ``result``.

