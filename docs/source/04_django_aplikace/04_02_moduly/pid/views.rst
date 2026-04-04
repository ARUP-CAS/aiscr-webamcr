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

      **Parametry:**

      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: _get_value_from_cache()

      Vrací value from cache.

      **Parametry:**

      - ``key``: Textový název nebo klíč ``key`` používaný v rámci operace.

      **Návratová hodnota:**

      Načtená data odpovídající zadaným vstupům.


   .. py:method:: _save_value_to_cache()

      Uloží value to cache.

      **Parametry:**

      - ``key``: Textový název nebo klíč ``key`` používaný v rámci operace.
      - ``value``: Parametr ``value`` předává se do volání ``set()``.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice.


   .. py:method:: api_call()

      Zavolá API dotaz pro autocomplete (abstraktní metoda).

      **Parametry:**

      - ``q``: Vyhledávací dotaz od uživatele.
      - ``use_cache``: Zda používat mezipaměť výsledků.


   .. py:method:: get()

      Vrací JSON odpověď s autocomplete výsledky.

      **Parametry:**

      - ``request``: HTTP požadavek ze strany klienta.
      - ``args``: Poziční argumenty z URL.
      - ``kwargs``: Pojmenované argumenty z URL.

      **Návratová hodnota:**

      JSON odpověď s výsledky.


   .. py:method:: autocomplete_results()

      Transformuje výsledky API na formát autocomplete (id, text).

      **Parametry:**

      - ``results``: Výsledky vrácené API voláním.

      **Návratová hodnota:**

      Seznam tuples (id, text) pro autocomplete.


   .. py:method:: get_list()

      Vrací list. v aplikaci.

      **Návratová hodnota:**

      Vrací výsledek volání ``api_call()``.



.. py:class:: DoiAutocompleteView

   Implementuje komponentu ``DoiAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: _api_call_data_cite()

      Vyhledá DOI v DataCite API.

      **Parametry:**

      - ``q``: Vyhledávací dotaz (DOI).

      **Návratová hodnota:**

      Seznam [DOI, název] párů.


   .. py:method:: _api_call_cross_ref_doi()

      Vyhledá DOI v CrossRef API pomocí přímého DOI.

      **Parametry:**

      - ``q``: Vyhledávací dotaz (DOI).

      **Návratová hodnota:**

      Seznam [DOI, název] párů.


   .. py:method:: _api_call_cross_ref_title()

      Vyhledá DOI v CrossRef API pomocí názvu publikace.

      **Parametry:**

      - ``q``: Vyhledávací dotaz (název publikace).

      **Návratová hodnota:**

      Seznam [DOI, název] párů.


   .. py:method:: _doi_item_exists()

      Ověří existenci DOI pomocí HTTP HEAD požadavku.

      **Parametry:**

      - ``doi``: DOI identifikátor.

      **Návratová hodnota:**

      Seznam [DOI, DOI] pokud existuje, jinak prázdný seznam.


   .. py:method:: api_call()

      Vyhledá DOI v CrossRef a DataCite API.

      **Parametry:**

      - ``q``: Vyhledávací dotaz.
      - ``use_cache``: Zda používat cache.

      **Návratová hodnota:**

      Seznam [DOI, název] párů.



.. py:class:: OrcidAutocompleteView

   Implementuje komponentu ``OrcidAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: api_call()

      Vyhledá výzkumné pracovníky v ORCID API.

      **Parametry:**

      - ``q``: Vyhledávací dotaz.
      - ``use_cache``: Zda používat cache.

      **Návratová hodnota:**

      Seznam [ORCID ID, jméno] párů.



.. py:class:: RorAutocompleteView

   Implementuje komponentu ``RorAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: api_call()

      Vyhledá organizace v ROR API.

      **Parametry:**

      - ``q``: Vyhledávací dotaz.
      - ``use_cache``: Zda používat cache.

      **Návratová hodnota:**

      Seznam [ROR ID, jméno] párů.



.. py:class:: WikiDataAutocompleteView

   Implementuje komponentu ``WikiDataAutocompleteView`` v rámci aplikace.

   **Metody:**

   .. py:method:: api_call()

      Vyhledá osoby v WikiData SPARQL API.

      **Parametry:**

      - ``q``: Vyhledávací dotaz.
      - ``use_cache``: Zda používat cache.

      **Návratová hodnota:**

      Seznam [WikiData ID, jméno] párů.



.. py:class:: ContinuePidProcessing

   Implementuje komponentu ``ContinuePidProcessing`` v rámci aplikace.

   **Metody:**

   .. py:method:: _perform_client_action()

      Provede akci na záznamu a publikuje do DataCite.

      **Parametry:**

      - ``record``: Záznam k publikaci (Lokalita, SamostatnyNalez nebo Dokument).
      - ``attribute_name``: Atribut záznamu pro uložení DOI.
      - ``publish_callable_method``: Callable pro publikaci.
      - ``set_callable_method``: Callable pro nastavení stavu.

      **Návratová hodnota:**

      DOI nebo chybová zpráva.


   .. py:method:: process_record()

      Zpracuje záznam pro publikaci/skrytí/smazání PID.

      **Parametry:**

      - ``record``: Záznam k publikaci.
      - ``result``: Výsledek formuláře.
      - ``result``: Textový název, klíč nebo zpráva ``result`` používaná v rámci operace.
      - ``kwargs``: Parametr ``kwargs`` pracuje se s atributy ``get``.

      **Návratová hodnota:**

      Vrací proměnná ``result``.


