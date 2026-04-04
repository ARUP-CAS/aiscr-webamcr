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

      **Parametry:**

      - ``request``: HTTP požadavek.

      **Návratová hodnota:**

      Výsledek volání ``all()``.


   .. py:method:: filter()

      Filtruje hodnotu. v aplikaci.

      **Parametry:**

      - ``qs``: Queryset, který má být filtrován.
      - ``value``: Vybrané hodnoty filtru (v této implementaci se queryset vrací beze změny).

      **Návratová hodnota:**

      Proměnná ``qs``.


