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

      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

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

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: validate()

      Validuje hodnotu. v aplikaci.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.


.. py:class:: OrcidAutocompleteField

   Implementuje komponentu ``OrcidAutocompleteField`` v rámci aplikace.

   **Metody:**

   .. py:method:: _get_initial_value_from_instance()

      Vrací initial value from instance.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: prepare_value()

      Provádí operaci prepare value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: valid_value()

      Provádí operaci valid value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: validate()

      Validuje hodnotu. v aplikaci.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.


.. py:class:: RorAutocompleteField

   Implementuje komponentu ``RorAutocompleteField`` v rámci aplikace.

   **Metody:**

   .. py:method:: valid_value()

      Provádí operaci valid value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: validate()

      Validuje hodnotu. v aplikaci.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.


.. py:class:: WikiDataAutocompleteField

   Implementuje komponentu ``WikiDataAutocompleteField`` v rámci aplikace.

   **Metody:**

   .. py:method:: _get_initial_value_from_instance()

      Vrací initial value from instance.

      :return: Načtená data odpovídající zadaným vstupům.

   .. py:method:: prepare_value()

      Provádí operaci prepare value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: valid_value()

      Provádí operaci valid value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

   .. py:method:: validate()

      Validuje hodnotu. v aplikaci.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

