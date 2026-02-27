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
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: _get_initial_value_from_instance()

      Vrací initial value from instance.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: _set_initial_values()

      Nastaví initial values.

      :return: Vrací výsledek provedené operace.


.. py:class:: DoiAutocompleteField

   Implementuje komponentu ``DoiAutocompleteField`` v rámci aplikace.

   **Metody:**

   .. py:method:: valid_value()

      Provádí operaci valid value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: validate()

      Validuje hodnotu.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: OrcidAutocompleteField

   Implementuje komponentu ``OrcidAutocompleteField`` v rámci aplikace.

   **Metody:**

   .. py:method:: _get_initial_value_from_instance()

      Vrací initial value from instance.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: prepare_value()

      Provádí operaci prepare value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: valid_value()

      Provádí operaci valid value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: validate()

      Validuje hodnotu.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: RorAutocompleteField

   Implementuje komponentu ``RorAutocompleteField`` v rámci aplikace.

   **Metody:**

   .. py:method:: valid_value()

      Provádí operaci valid value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: validate()

      Validuje hodnotu.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.


.. py:class:: WikiDataAutocompleteField

   Implementuje komponentu ``WikiDataAutocompleteField`` v rámci aplikace.

   **Metody:**

   .. py:method:: _get_initial_value_from_instance()

      Vrací initial value from instance.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: prepare_value()

      Provádí operaci prepare value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: valid_value()

      Provádí operaci valid value.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: validate()

      Validuje hodnotu.

      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek ověření nebo validačního pravidla.

