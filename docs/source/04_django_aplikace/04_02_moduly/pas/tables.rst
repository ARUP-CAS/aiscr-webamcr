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

      :param value: Popis parametru ``value``.
      :param record: Popis parametru ``record``.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: AktivaceDeaktivaceColumn

   Implementuje komponentu ``AktivaceDeaktivaceColumn`` v rámci aplikace.

   **Metody:**

   .. py:method:: render()

      Vyrenderuje hodnotu. v aplikaci.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :param table: Vstupní hodnota ``table`` pro danou operaci.
      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :param bound_column: Vstupní hodnota ``bound_column`` pro danou operaci.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.


.. py:class:: smazatColumn

   Implementuje komponentu ``smazatColumn`` v rámci aplikace.

   **Metody:**

   .. py:method:: render()

      Vyrenderuje hodnotu. v aplikaci.

      :param record: Vstupní hodnota ``record`` pro danou operaci.
      :param table: Vstupní hodnota ``table`` pro danou operaci.
      :param value: Vstupní hodnota ``value`` pro danou operaci.
      :param bound_column: Vstupní hodnota ``bound_column`` pro danou operaci.
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

