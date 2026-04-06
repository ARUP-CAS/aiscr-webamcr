ARCH_Z tables
=============

Modul tables.

Třídy
------

.. py:class:: BooleanValueColumn

   Implementuje komponentu ``BooleanValueColumn`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``pop``.

   .. py:method:: render()

      Převede booleovskou hodnotu na textovou reprezentaci pro tabulku.

      :param value: Parametr ``value`` předává se do volání ``bool()``, ``len()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

          :return: Vrací hodnotu podle větve zpracování, typicky: vybranou hodnotu z kolekce, str.


.. py:class:: AkceTable

   Definuje tabulku akcí pro přehled i export.

   **Metody:**

   .. py:method:: order_vedouci_organizace()

      Seřadí queryset podle zkráceného názvu organizace vedoucího akce.

      :param queryset: Parametr ``queryset`` pracuje se s atributy ``annotate``, vstupuje do návratové hodnoty.
      :param is_descending: Parametr ``is_descending`` předává se do volání ``order_by()``.

          :return: Vrací n-tici.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: get_all_idents()

      Vrátí seznam identifikátorů archeologických záznamů pro akci.

      :return: Vrací výsledek volání ``join()``.

