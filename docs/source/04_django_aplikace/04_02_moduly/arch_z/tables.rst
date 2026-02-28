ARCH_Z tables
=============

Modul tables.

Třídy
------

.. py:class:: BooleanValueColumn

   Implementuje komponentu ``BooleanValueColumn`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: render()

      Převede booleovskou hodnotu na textovou reprezentaci pro tabulku.
      :param value: Vstupní hodnota ``value`` pro danou operaci.


.. py:class:: AkceTable

   Definuje tabulku akcí pro přehled i export.

   **Metody:**

   .. py:method:: order_vedouci_organizace()

      Provádí operaci order vedouci organizace.

      :param queryset: Vstupní hodnota ``queryset`` pro danou operaci.
      :param is_descending: Vstupní hodnota ``is_descending`` pro danou operaci.

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      :param args: Dodatečné poziční argumenty předané voláním.
      :param kwargs: Dodatečné pojmenované argumenty předané voláním.

   .. py:method:: get_all_idents()

      Vrátí seznam identifikátorů archeologických záznamů pro akci.

