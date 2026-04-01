PID fields
==========

Modul fields.

Třídy
------

.. py:class:: PidAutocompleteField

   Implementuje komponentu ``PidAutocompleteField`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``pop``.

   .. py:method:: _get_initial_value_from_instance()

      Vrací initial value from instance.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: _set_initial_values()

      Nastaví initial values.

      :return: Výstup funkce odpovídající implementované logice.


.. py:class:: DoiAutocompleteField

   Implementuje komponentu ``DoiAutocompleteField`` v rámci aplikace.

   **Metody:**

   .. py:method:: valid_value()

      Ověří, zda zadaná hodnota DOI existuje v databázi DOI identifikátorů.

      :param value: Řetězec s DOI identifikátorem, jehož platnost se ověřuje.

      :return: Vrací výsledek volání ``verify_doi()``.

   .. py:method:: validate()

      Validuje hodnotu. v aplikaci.

      :param value: Parametr ``value`` předává se do volání ``verify_doi()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``verify_doi()``.


.. py:class:: OrcidAutocompleteField

   Implementuje komponentu ``OrcidAutocompleteField`` v rámci aplikace.

   **Metody:**

   .. py:method:: _get_initial_value_from_instance()

      Vrací initial value from instance.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: prepare_value()

      Odstraní z ORCID hodnoty prefix URL a vrátí pouze samotný identifikátor.

      :param value: Řetězec s ORCID identifikátorem, případně s prefixem ``https://orcid.org/``.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: valid_value()

      Ověří, zda zadaný ORCID identifikátor existuje v databázi ORCID.

      :param value: Řetězec s ORCID identifikátorem, jehož platnost se ověřuje.

      :return: Vrací výsledek volání ``verify_orcid()``.

   .. py:method:: validate()

      Validuje hodnotu. v aplikaci.

      :param value: Parametr ``value`` předává se do volání ``verify_orcid()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``verify_orcid()``.


.. py:class:: RorAutocompleteField

   Implementuje komponentu ``RorAutocompleteField`` v rámci aplikace.

   **Metody:**

   .. py:method:: valid_value()

      Ověří, zda zadaný ROR identifikátor existuje v databázi ROR organizací.

      :param value: Řetězec s ROR identifikátorem, jehož platnost se ověřuje.

      :return: Vrací výsledek volání ``verify_ror()``.

   .. py:method:: validate()

      Validuje hodnotu. v aplikaci.

      :param value: Parametr ``value`` předává se do volání ``verify_ror()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``verify_ror()``.


.. py:class:: WikiDataAutocompleteField

   Implementuje komponentu ``WikiDataAutocompleteField`` v rámci aplikace.

   **Metody:**

   .. py:method:: _get_initial_value_from_instance()

      Vrací initial value from instance.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: prepare_value()

      Odstraní z hodnoty Wikidata prefix URL a vrátí pouze samotný identifikátor entity.

      :param value: Řetězec s identifikátorem Wikidata, případně s prefixem ``https://www.wikidata.org/entity/``.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: valid_value()

      Ověří, zda zadaný identifikátor Wikidata existuje jako platná entita.

      :param value: Řetězec s identifikátorem nebo URL záznamu Wikidata, jehož platnost se ověřuje.

      :return: Vrací výsledek volání ``verify_wikidata()``.

   .. py:method:: validate()

      Validuje hodnotu. v aplikaci.

      :param value: Parametr ``value`` předává se do volání ``verify_wikidata()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``verify_wikidata()``.

