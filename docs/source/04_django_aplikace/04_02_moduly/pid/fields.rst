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

      Provádí operaci valid value.

      :param value: Parametr ``value`` předává se do volání ``verify_doi()``, vstupuje do návratové hodnoty.

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

      Provádí operaci prepare value.

      :param value: Parametr ``value`` pracuje se s atributy ``replace``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: valid_value()

      Provádí operaci valid value.

      :param value: Parametr ``value`` předává se do volání ``verify_orcid()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``verify_orcid()``.

   .. py:method:: validate()

      Validuje hodnotu. v aplikaci.

      :param value: Parametr ``value`` předává se do volání ``verify_orcid()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``verify_orcid()``.


.. py:class:: RorAutocompleteField

   Implementuje komponentu ``RorAutocompleteField`` v rámci aplikace.

   **Metody:**

   .. py:method:: valid_value()

      Provádí operaci valid value.

      :param value: Parametr ``value`` předává se do volání ``verify_ror()``, vstupuje do návratové hodnoty.

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

      Provádí operaci prepare value.

      :param value: Parametr ``value`` pracuje se s atributy ``replace``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování.

   .. py:method:: valid_value()

      Provádí operaci valid value.

      :param value: Parametr ``value`` předává se do volání ``verify_wikidata()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``verify_wikidata()``.

   .. py:method:: validate()

      Validuje hodnotu. v aplikaci.

      :param value: Parametr ``value`` předává se do volání ``verify_wikidata()``, vstupuje do návratové hodnoty.

      :return: Vrací výsledek volání ``verify_wikidata()``.

