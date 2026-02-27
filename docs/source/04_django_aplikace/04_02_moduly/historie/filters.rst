HISTORIE filtry
===============

Definice filtrů.

Třídy
------

.. py:class:: HistorieOrganizaceMultipleChoiceFilter

   Implementuje komponentu ``HistorieOrganizaceMultipleChoiceFilter`` v rámci aplikace.

   **Metody:**

   .. py:method:: get_queryset()

      Vrací queryset.

      :param request: Django HTTP požadavek použitý při zpracování.
      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: filter()

      Filtruje hodnotu.

      :param qs: Vstupní hodnota ``qs`` pro danou operaci.
      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

