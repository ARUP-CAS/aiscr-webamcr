KOMPONENTA formuláře
====================

Definice formulářů.

Třídy
------

.. py:class:: CreateKomponentaForm

   Hlavní formulář pro vytvoření, editaci a zobrazení komponenty.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``obdobi_choices``: Parametr ``obdobi_choices`` se předává do volání ``TwoLevelSelectField()``, ``Select()``.
      - ``areal_choices``: Parametr ``areal_choices`` předává se do volání ``TwoLevelSelectField()``, ``Select()``.
      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``readonly``: Příznak, zda mají být všechna pole formuláře zobrazena pouze pro čtení.
      - ``required``: Parametr ``required`` ovlivňuje větvení podmínek.
      - ``required_next``: Parametr ``required_next`` ovlivňuje větvení podmínek.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


