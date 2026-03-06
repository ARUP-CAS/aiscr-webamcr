PROJEKT tables
==============

Modul tables.

Třídy
------

.. py:class:: ProjektTable

   Třída pro definování tabulky pro projekt použitých pro zobrazení přehledu projektů a exportu.

   **Metody:**

   .. py:method:: render_planovane_zahajeni()

      Vyrenderuje planovane zahajeni.

      :param value: Parametr ``value`` předává se do volání ``isinstance()``, ``str()``, pracuje se s atributy ``lower``, ``upper``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: None, hodnotu podle větve zpracování, výsledek volání ``str()``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

