DJ modely
=========

Definice modelů.

Třídy
------

.. py:class:: DokumentacniJednotka

   Databázový model dokumentační jednotky.

   **Metody:**

   .. py:method:: get_absolute_url()

      Metoda pro získání absolutní URL archeologického záznamu pro dokumentační jednotku.

   .. py:method:: ident_cely_safe()

      Provádí operaci ident cely safe.

      :return: Vrací výsledek provedené operace.

   .. py:method:: has_adb()

      Metoda pro ověření, jestli dokumentační jednotka má ADB.

   .. py:method:: get_permission_object()

      Vrací permission object.

      :return: Vrací načtená data odpovídající vstupním parametrům.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.
      :return: Funkce nevrací hodnotu (``None``).

   .. py:method:: initial_pian()

      Vrátí objekt Pian na základě initial_pian_id (líné načtení).

