PAS tables
==========

Modul tables.

Třídy
------

.. py:class:: SamostatnyNalezTable

   Definuje tabulku samostatných nálezů pro přehled i export.

   **Metody:**

   .. py:method:: render_nahled()

      Metoda pro správně zobrazení náhledu souboru.

      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :param record: Záznam, který funkce čte nebo upravuje.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: AktivaceDeaktivaceColumn

   Implementuje komponentu ``AktivaceDeaktivaceColumn`` v rámci aplikace.

   **Metody:**

   .. py:method:: render()

      Vyrenderuje hodnotu. v aplikaci.

      :param record: Záznam, který funkce čte nebo upravuje.
      :param table: Název nebo typ ``table`` používaný pro volbu cílové logiky.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :param bound_column: Číselná nebo geometrická hodnota `bound_column` použitá při výpočtu nebo transformaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: smazatColumn

   Implementuje komponentu ``smazatColumn`` v rámci aplikace.

   **Metody:**

   .. py:method:: render()

      Vyrenderuje hodnotu. v aplikaci.

      :param record: Záznam, který funkce čte nebo upravuje.
      :param table: Název nebo typ ``table`` používaný pro volbu cílové logiky.
      :param value: Hodnota vstupu (např. z formuláře nebo filtru), kterou funkce validuje či převádí.
      :param bound_column: Číselná nebo geometrická hodnota `bound_column` použitá při výpočtu nebo transformaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: UzivatelSpolupraceTable

   Definuje tabulku uživatelských spoluprací pro přehled i export.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_all_idents()

      Vrátí prázdnu hodnotu. Metoda je zde kvůli kompatibilitě s ostatními tabulkami.

