HISTORIE filtry
===============

Definice filtrů.

Třídy
------

.. py:class:: HistorieOrganizaceMultipleChoiceFilter

   Implementuje komponentu ``HistorieOrganizaceMultipleChoiceFilter`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset. v aplikaci.

      :param request: Parametr ``request`` slouží jako vstup pro logiku funkce ``get_queryset``.

      :return: Vrací výsledek volání ``all()``.

   .. py:method:: filter()

      Filtruje hodnotu. v aplikaci.

      :param qs: Parametr ``qs`` vstupuje do návratové hodnoty.
      :param value: Parametr ``value`` slouží jako vstup pro logiku funkce ``filter``.

      :return: Vrací proměnná ``qs``.

