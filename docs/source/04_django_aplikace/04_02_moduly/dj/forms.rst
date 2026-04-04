DJ formuláře
============

Definice formulářů.

Třídy
------

.. py:class:: CreateDJForm

   Hlavní formulář pro vytvoření, editaci a zobrazení dokumentační jednotky.

   **Metody:**

   .. py:method:: get_typ_queryset()

      Metoda formuláře pro získaní querysetu pro typ DJ podle typu akce.

      **Parametry:**

      - ``jednotky``: Číselná hodnota ``jednotky`` použitá při výpočtu nebo transformaci.
      - ``instance``: Parametr ``instance`` předává se do volání ``debug()``, ``hasattr()``, pracuje se s atributy ``typ``, ``ident_cely``, ovlivňuje větvení podmínek.
      - ``typ_arch_z``: Parametr ``typ_arch_z`` předává se do volání ``debug()``, ovlivňuje větvení podmínek.
      - ``typ_akce``: Parametr ``typ_akce`` předává se do volání ``debug()``, ovlivňuje větvení podmínek.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``filter()``, proměnná ``queryset``.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``not_readonly``: Číselná hodnota ``not_readonly`` použitá při výpočtu nebo transformaci.
      - ``typ_arch_z``: Parametr ``typ_arch_z`` předává se do volání ``ModelChoiceField()``, ``get_typ_queryset()``.
      - ``typ_akce``: Parametr ``typ_akce`` předává se do volání ``ModelChoiceField()``, ``get_typ_queryset()``, ovlivňuje větvení podmínek.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``pop``.



.. py:class:: ChangeKatastrForm

   Formulář pro editaci katastru u archeologického záznamu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


