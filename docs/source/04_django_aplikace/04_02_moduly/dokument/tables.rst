DOKUMENT tables
===============

Modul tables.

Třídy
------

.. py:class:: Model3DTable

   Definuje tabulku 3D modelů pro přehled i export.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: render_nahled()

      Metoda pro správně zobrazení náhledu souboru.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :param record: Záznam, který funkce čte nebo upravuje.


.. py:class:: DokumentTable

   Definuje tabulku dokumentů pro přehled i export.

   **Metody:**

   .. py:method:: render_nahled()

      Metoda pro správně zobrazení náhledu souboru.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :param record: Záznam, který funkce čte nebo upravuje.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

