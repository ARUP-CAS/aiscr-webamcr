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

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

   .. py:method:: render_nahled()

      Metoda pro správně zobrazení náhledu souboru.

      :param value: Parametr ``value`` slouží jako vstup pro logiku funkce ``render_nahled``.
      :param record: Parametr ``record`` předává se do volání ``len()``, ``reverse()``, pracuje se s atributy ``soubory``, ``ident_cely``, ovlivňuje větvení podmínek.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``format_html()``, str.


.. py:class:: DokumentTable

   Definuje tabulku dokumentů pro přehled i export.

   **Metody:**

   .. py:method:: render_nahled()

      Metoda pro správně zobrazení náhledu souboru.

      :param value: Parametr ``value`` slouží jako vstup pro logiku funkce ``render_nahled``.
      :param record: Parametr ``record`` předává se do volání ``hasattr()``, ``len()``, pracuje se s atributy ``soubory``, ``ident_cely``, ovlivňuje větvení podmínek.

      :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``format_html()``, str.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

