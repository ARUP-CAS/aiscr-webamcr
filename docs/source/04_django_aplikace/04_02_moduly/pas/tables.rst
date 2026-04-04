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

      **Parametry:**

      - ``value``: Parametr ``value`` slouží jako vstup pro logiku funkce ``render_nahled``.
      - ``record``: Parametr ``record`` předává se do volání ``reverse()``, pracuje se s atributy ``nahled_soubor``, ``ident_cely``.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``format_html()``, str.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



.. py:class:: AktivaceDeaktivaceColumn

   Implementuje komponentu ``AktivaceDeaktivaceColumn`` v rámci aplikace.

   **Metody:**

   .. py:method:: render()

      Vyrenderuje hodnotu. v aplikaci.

      **Parametry:**

      - ``record``: Parametr ``record`` předává se do volání ``check_permissions()``, ``render()``, pracuje se s atributy ``aktivni``, ``id``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      - ``table``: Parametr ``table`` předává se do volání ``hasattr()``, ``check_permissions()``, pracuje se s atributy ``request``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      - ``value``: Parametr ``value`` předává se do volání ``render()``, vstupuje do návratové hodnoty.
      - ``bound_column``: Parametr ``bound_column`` se předává do volání ``render()``, vstupuje do návratové hodnoty.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``render()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: str, výsledek volání ``render()``, výsledek volání ``format_html()``.



.. py:class:: smazatColumn

   Implementuje komponentu ``smazatColumn`` v rámci aplikace.

   **Metody:**

   .. py:method:: render()

      Vyrenderuje hodnotu. v aplikaci.

      **Parametry:**

      - ``record``: Parametr ``record`` předává se do volání ``check_permissions()``, ``render()``, pracuje se s atributy ``id``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      - ``table``: Parametr ``table`` předává se do volání ``hasattr()``, ``check_permissions()``, pracuje se s atributy ``request``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.
      - ``value``: Parametr ``value`` předává se do volání ``render()``, vstupuje do návratové hodnoty.
      - ``bound_column``: Parametr ``bound_column`` se předává do volání ``render()``, vstupuje do návratové hodnoty.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``render()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací hodnotu podle větve zpracování, typicky: str, výsledek volání ``render()``, výsledek volání ``format_html()``.



.. py:class:: UzivatelSpolupraceTable

   Definuje tabulku uživatelských spoluprací pro přehled i export.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: get_all_idents()

      Vrátí prázdnu hodnotu. Metoda je zde kvůli kompatibilitě s ostatními tabulkami.

      **Návratová hodnota:**

      Vrací str.


