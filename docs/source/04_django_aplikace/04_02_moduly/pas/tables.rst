PAS tables
==========

Modul tables.

Třídy
------

.. py:class:: SamostatnyNalezTable

   Class pro definování tabulky pro samostatný nález použitých pro zobrazení přehledu nálezu a exportu.

   **Metody:**

   .. py:method:: render_nahled()

      Metoda pro správně zobrazení náhledu souboru.

   .. py:method:: __init__()


.. py:class:: AktivaceDeaktivaceColumn

   Popis není k dispozici.

   **Metody:**

   .. py:method:: render()


.. py:class:: smazatColumn

   Popis není k dispozici.

   **Metody:**

   .. py:method:: render()


.. py:class:: UzivatelSpolupraceTable

   Class pro definování tabulky pro uživatelskou spolupráci použitých pro zobrazení přehledu spoluprác a exportu.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: get_all_idents()

      Vrátí prázdnu hodnotu. Metoda je zde kvůli kompatibilitě s ostatními tabulkami.
