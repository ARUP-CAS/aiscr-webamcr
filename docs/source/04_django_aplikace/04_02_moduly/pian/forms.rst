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
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: _instance_geom_wkt()

      Provádí operaci instance geom wkt.

      :param field_name: Vstupní hodnota ``field_name`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: run_loaded_validation()

      Metoda pro validaci geometrií při potvrzení PIANu.

   .. py:method:: clean()

      Provádí operaci clean.

      :return: Vrací výsledek provedené operace.

   .. py:method:: validate_geom()

      Metoda pro validaci PIAN pomocí funkce v postgres databázi.

