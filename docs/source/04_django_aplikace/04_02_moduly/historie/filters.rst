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

      :param request: Django HTTP požadavek použitý při zpracování.

   .. py:method:: filter()

      Filtruje hodnotu. v aplikaci.

      :param qs: Vstupní queryset, který má být dále zpracován.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.

