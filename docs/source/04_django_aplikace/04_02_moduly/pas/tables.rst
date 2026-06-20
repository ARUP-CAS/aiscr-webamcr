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

      :param value: Parametr ``value`` slouží jako vstup pro logiku funkce ``render_nahled``.
      :param record: Parametr ``record`` předává se do volání ``reverse()``, pracuje se s atributy ``nahled_soubor``, ``ident_cely``.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``format_html()``, str.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.


.. py:class:: AktivaceDeaktivaceColumn

   Implementuje komponentu ``AktivaceDeaktivaceColumn`` v rámci aplikace.

   **Metody:**

   .. py:method:: render()

      Vyrenderuje hodnotu. v aplikaci.

      :param record: Parametr ``record`` předává se do volání ``check_permissions()``, ``render()``, pracuje se s atributy ``aktivni``, ``id``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param table: Parametr ``table`` předává se do volání ``hasattr()``, ``check_permissions()``, pracuje se s atributy ``request``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param value: Parametr ``value`` předává se do volání ``render()``, vstupuje do návratové hodnoty.
      :param bound_column: Parametr ``bound_column`` se předává do volání ``render()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``render()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: str, výsledek volání ``render()``, výsledek volání ``format_html()``.


.. py:class:: smazatColumn

   Implementuje komponentu ``smazatColumn`` v rámci aplikace.

   **Metody:**

   .. py:method:: render()

      Vyrenderuje hodnotu. v aplikaci.

      :param record: Parametr ``record`` předává se do volání ``check_permissions()``, ``render()``, pracuje se s atributy ``id``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param table: Parametr ``table`` předává se do volání ``hasattr()``, ``check_permissions()``, pracuje se s atributy ``request``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param value: Parametr ``value`` předává se do volání ``render()``, vstupuje do návratové hodnoty.
      :param bound_column: Parametr ``bound_column`` se předává do volání ``render()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``render()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: str, výsledek volání ``render()``, výsledek volání ``format_html()``.


.. py:class:: EditProjektyColumn

   Implementuje komponentu ``EditProjektyColumn`` pro editaci projektů spolupráce.

   **Metody:**

   .. py:method:: render()

      Vyrenderuje hodnotu v aplikaci.

      :param record: Parametr ``record`` předává se do volání ``check_permissions()``, ``render()``, pracuje se s atributy ``id``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param table: Parametr ``table`` předává se do volání ``hasattr()``, ``check_permissions()``, pracuje se s atributy ``request``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      :param value: Parametr ``value`` předává se do volání ``render()``, vstupuje do návratové hodnoty.
      :param bound_column: Parametr ``bound_column`` se předává do volání ``render()``, vstupuje do návratové hodnoty.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``render()``, vstupuje do návratové hodnoty.

      :return: Vrací hodnotu podle větve zpracování, typicky: str, výsledek volání ``render()``, výsledek volání ``format_html()``.


.. py:class:: UzivatelSpolupraceTable

   Definuje tabulku uživatelských spoluprací pro přehled i export.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param user: Přihlášený uživatel; pro roli Badatel se sloupec ``edit_projekty`` z tabulky odstraní.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: render_projekty()

      Vyrenderuje seznam projektů přiřazených ke spolupráci jako klikatelné odkazy.

      :param value: Parametr ``value`` slouží jako vstup pro logiku funkce ``render_projekty``.
      :param record: Parametr ``record`` předává se do volání ``record.projekty.all()``.

      :return: Vrací výsledek volání ``format_html()``.

   .. py:method:: value_projekty()

      Vrátí seznam identifikátorů projektů přiřazených ke spolupráci jako prostý text pro export.

      Na rozdíl od ``render_projekty`` nevrací HTML s odkazy, ale pouze čárkou oddělené
      identifikátory. Metoda je využita při sestavení Redis snapshotu (``get_cell_value``),
      ze kterého se generuje export, takže do CSV/XLSX/JSON se uloží čitelná hodnota místo HTML.

      :param record: Záznam spolupráce, ze kterého se přes ``record.projekty.all()`` načítají přiřazené projekty.

      :return: Vrací čárkou oddělené identifikátory projektů, nebo prázdný řetězec.

   .. py:method:: get_all_idents()

      Vrátí prázdnu hodnotu. Metoda je zde kvůli kompatibilitě s ostatními tabulkami.

      :return: Vrací str.

