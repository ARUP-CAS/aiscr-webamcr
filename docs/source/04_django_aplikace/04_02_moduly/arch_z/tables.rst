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

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``pop``.


   .. py:method:: render()

      Převede booleovskou hodnotu na textovou reprezentaci pro tabulku.

      **Parametry:**

      - ``value``: Parametr ``value`` předává se do volání ``bool()``, ``len()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: vybranou hodnotu z kolekce, str.



.. py:class:: AkceTable

   Definuje tabulku akcí pro přehled i export.

   **Metody:**

   .. py:method:: order_vedouci_organizace()

      Seřadí queryset podle zkráceného názvu organizace vedoucího akce.

      **Parametry:**

      - ``queryset``: Parametr ``queryset`` pracuje se s atributy ``annotate``, vstupuje do návratové hodnoty.
      - ``is_descending``: Parametr ``is_descending`` předává se do volání ``order_by()``.

      **Návratová hodnota:**

      Vrací n-tici.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: get_all_idents()

      Vrátí seznam identifikátorů archeologických záznamů pro akci.

      **Návratová hodnota:**

      Vrací výsledek volání ``join()``.


