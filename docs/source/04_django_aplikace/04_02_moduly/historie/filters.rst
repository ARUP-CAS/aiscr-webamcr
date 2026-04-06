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

      :param request: HTTP požadavek.

      :return: Výsledek volání ``all()``.

   .. py:method:: filter()

      Filtruje hodnotu. v aplikaci.

      :param qs: Queryset, který má být filtrován.
      :param value: Vybrané hodnoty filtru (v této implementaci se queryset vrací beze změny).

      :return: Proměnná ``qs``.

