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

      :param jednotky: Číselná hodnota ``jednotky`` použitá při výpočtu nebo transformaci.
      :param instance: Parametr ``instance`` předává se do volání ``debug()``, ``hasattr()``, pracuje se s atributy ``typ``, ``ident_cely``, ovlivňuje větvení podmínek.
      :param typ_arch_z: Parametr ``typ_arch_z`` předává se do volání ``debug()``, ovlivňuje větvení podmínek.
      :param typ_akce: Parametr ``typ_akce`` předává se do volání ``debug()``, ovlivňuje větvení podmínek.

          :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``filter()``, proměnná ``queryset``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param not_readonly: Číselná hodnota ``not_readonly`` použitá při výpočtu nebo transformaci.
      :param typ_arch_z: Parametr ``typ_arch_z`` předává se do volání ``ModelChoiceField()``, ``get_typ_queryset()``.
      :param typ_akce: Parametr ``typ_akce`` předává se do volání ``ModelChoiceField()``, ``get_typ_queryset()``, ovlivňuje větvení podmínek.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``, pracuje se s atributy ``pop``.


.. py:class:: ChangeKatastrForm

   Formulář pro editaci katastru u archeologického záznamu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

