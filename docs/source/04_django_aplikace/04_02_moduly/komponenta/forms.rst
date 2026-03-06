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

      :param obdobi_choices: Číselná nebo geometrická hodnota `obdobi_choices` použitá při výpočtu nebo transformaci.
      :param areal_choices: Doménový objekt `areal_choices`, se kterým funkce pracuje.
      :param args: Dodatečné poziční argumenty předané voláním.
      :param readonly: Příznak ``readonly`` určující průběh nebo rozsah zpracování.
      :param required: Příznak ``required`` určující průběh nebo rozsah zpracování.
      :param required_next: Příznak ``required_next`` určující průběh nebo rozsah zpracování.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

