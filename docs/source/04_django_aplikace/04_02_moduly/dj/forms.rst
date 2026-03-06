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
      :param instance: Instance modelu, které se operace týká.
      :param typ_arch_z: Název nebo typ ``typ_arch_z`` používaný pro volbu cílové logiky.
      :param typ_akce: Název nebo typ ``typ_akce`` používaný pro volbu cílové logiky.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param not_readonly: Číselná hodnota ``not_readonly`` použitá při výpočtu nebo transformaci.
      :param typ_arch_z: Název nebo typ ``typ_arch_z`` používaný pro volbu cílové logiky.
      :param typ_akce: Název nebo typ ``typ_akce`` používaný pro volbu cílové logiky.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ChangeKatastrForm

   Formulář pro editaci katastru u archeologického záznamu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

