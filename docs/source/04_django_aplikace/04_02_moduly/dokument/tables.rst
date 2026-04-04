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

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


   .. py:method:: render_nahled()

      Vykreslí HTML náhled modelu 3D.

      **Parametry:**

      - ``value``: Hodnota sloupce (ignorováno).
      - ``record``: Záznam s daty modelu 3D.

      **Návratová hodnota:**

      HTML řetězec s náhledem nebo prázdný řetězec.



.. py:class:: DokumentTable

   Definuje tabulku dokumentů pro přehled i export.

   **Metody:**

   .. py:method:: render_nahled()

      Vykreslí HTML náhled modelu 3D.

      **Parametry:**

      - ``value``: Hodnota sloupce (ignorováno).
      - ``record``: Záznam s daty modelu 3D.

      **Návratová hodnota:**

      HTML řetězec s náhledem nebo prázdný řetězec.


   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.


