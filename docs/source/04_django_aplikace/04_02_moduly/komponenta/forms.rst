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

      :param obdobi_choices: Parametr ``obdobi_choices`` se předává do volání ``TwoLevelSelectField()``, ``Select()``.
      :param areal_choices: Parametr ``areal_choices`` předává se do volání ``TwoLevelSelectField()``, ``Select()``.
      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param readonly: Příznak, zda mají být všechna pole formuláře zobrazena pouze pro čtení.
      :param required: Parametr ``required`` ovlivňuje větvení podmínek.
      :param required_next: Parametr ``required_next`` ovlivňuje větvení podmínek.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

