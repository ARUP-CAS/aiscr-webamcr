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

      :param jednotky: Popis parametru ``jednotky``.
      :param instance: Popis parametru ``instance``.
      :param typ_arch_z: Popis parametru ``typ_arch_z``.
      :param typ_akce: Popis parametru ``typ_akce``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param not_readonly: Vstupní hodnota ``not_readonly`` pro danou operaci.
      :param typ_arch_z: Vstupní hodnota ``typ_arch_z`` pro danou operaci.
      :param typ_akce: Vstupní hodnota ``typ_akce`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: ChangeKatastrForm

   Formulář pro editaci katastru u archeologického záznamu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

