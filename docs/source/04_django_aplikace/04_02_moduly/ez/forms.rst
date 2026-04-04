EZ formuláře
============

Definice formulářů.

Třídy
------

.. py:class:: ExterniZdrojForm

   Hlavní formulář pro vytvoření, editaci a zobrazení externího zdroju.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``, ``DoiAutocompleteField()``.
      - ``required``: Parametr ``required`` ovlivňuje větvení podmínek.
      - ``required_next``: Parametr ``required_next`` ovlivňuje větvení podmínek.
      - ``readonly``: Parametr ``readonly`` ovlivňuje větvení podmínek.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: ExterniOdkazForm

   Hlavní formulář pro vytvoření, editaci externího odkazu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``type_arch``: Typ archeologického záznamu (nevyužit v tomto formuláři, přijímán pro kompatibilitu).
      - ``args``: Poziční argumenty předávané nadřízené třídě.
      - ``kwargs``: Klíčové argumenty předávané nadřízené třídě.



.. py:class:: PripojitArchZaznamForm

   Hlavní formulář pro připojení archeologického záznamu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``type_arch``: Parametr ``type_arch`` předává se do volání ``ChoiceField()``, ``AutocompleteListSelect2()``, ovlivňuje větvení podmínek.
      - ``dok``: Parametr ``dok`` ovlivňuje větvení podmínek.
      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: PripojitExterniOdkazForm

   Hlavní formulář pro připojení externího zdroju.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


