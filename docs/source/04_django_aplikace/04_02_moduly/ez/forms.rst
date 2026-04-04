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

      :param args: Parametr ``args`` se předává do volání ``__init__()``, ``DoiAutocompleteField()``.
      :param required: Parametr ``required`` ovlivňuje větvení podmínek.
      :param required_next: Parametr ``required_next`` ovlivňuje větvení podmínek.
      :param readonly: Parametr ``readonly`` ovlivňuje větvení podmínek.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: ExterniOdkazForm

   Hlavní formulář pro vytvoření, editaci externího odkazu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param type_arch: Typ archeologického záznamu (nevyužit v tomto formuláři, přijímán pro kompatibilitu).
      :param args: Poziční argumenty předávané nadřízené třídě.
      :param kwargs: Klíčové argumenty předávané nadřízené třídě.


.. py:class:: PripojitArchZaznamForm

   Hlavní formulář pro připojení archeologického záznamu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param type_arch: Parametr ``type_arch`` předává se do volání ``ChoiceField()``, ``AutocompleteListSelect2()``, ovlivňuje větvení podmínek.
      :param dok: Parametr ``dok`` ovlivňuje větvení podmínek.
      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: PripojitExterniOdkazForm

   Hlavní formulář pro připojení externího zdroju.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

