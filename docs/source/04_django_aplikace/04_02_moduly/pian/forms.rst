PIAN formuláře
==============

Definice formulářů.

Třídy
------

.. py:class:: PianCreateForm

   Hlavní formulář pro vytvoření, editaci a zobrazení pianu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: _instance_geom_wkt()

      Provádí operaci instance geom wkt.

      :param field_name: Textový název nebo klíč ``field_name`` používaný v rámci operace.
      :return: Výstup funkce odpovídající implementované logice.

   .. py:method:: run_loaded_validation()

      Metoda pro validaci geometrií při potvrzení PIANu.

   .. py:method:: clean()

      Provádí operaci clean.

   .. py:method:: validate_geom()

      Metoda pro validaci PIAN pomocí funkce v postgres databázi.

      :param geom: Doménový objekt `geom`, se kterým funkce pracuje.
      :param epsg: Číselná nebo geometrická hodnota `epsg` použitá při výpočtu nebo transformaci.

