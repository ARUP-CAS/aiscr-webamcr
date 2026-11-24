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

      Vykreslí HTML náhled modelu 3D.

      :param value: Hodnota sloupce (ignorováno).
      :param record: Záznam s daty modelu 3D.
      :return: HTML řetězec s náhledem nebo prázdný řetězec.


.. py:class:: DokumentTable

   Definuje tabulku dokumentů pro přehled i export.

   **Metody:**

   .. py:method:: render_nahled()

      Vykreslí HTML náhled běžného dokumentu (nikoli modelu 3D).

      Odkazy na náhled i velký náhled se skládají s ``typ_vazby="dokument"``, aby prošly kontrolou
      ``check_soubor_vazba``; modely 3D vykresluje samostatná ``Model3DTable``.

      :param value: Hodnota sloupce (ignorováno).
      :param record: Záznam běžného dokumentu (jiného typu než model 3D).
      :return: HTML řetězec s náhledem nebo prázdný řetězec.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Parametr ``args`` se předává do volání ``__init__()``.
      :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.

