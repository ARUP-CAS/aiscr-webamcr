CORE widgety
============

Definice widgetů.

Třídy
------

.. py:class:: ForeignKeyReadOnlyTextInput

   Widget pro textinput pro vazbu cizí klíč.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :param attrs: Kolekce ``attrs`` zpracovávaná touto funkcí.

   .. py:method:: format_value()

      Provádí operaci format value.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.


.. py:class:: AutocompleteSelect2WidgetMixin

   Implementuje komponentu ``AutocompleteSelect2WidgetMixin`` v rámci aplikace.

   **Metody:**

   .. py:method:: build_attrs()

      Nastaveni placeholderu pro pole, pokud neni poskytnuto a zmena zakladni tridy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: AutocompleteListSelect2

   Implementuje komponentu ``AutocompleteListSelect2`` v rámci aplikace.


.. py:class:: AutocompleteSelect2Multiple

   Implementuje komponentu ``AutocompleteSelect2Multiple`` v rámci aplikace.


.. py:class:: AutocompleteModelSelect2

   Implementuje komponentu ``AutocompleteModelSelect2`` v rámci aplikace.


.. py:class:: AutocompleteModelSelect2Multiple

   Implementuje komponentu ``AutocompleteModelSelect2Multiple`` v rámci aplikace.

