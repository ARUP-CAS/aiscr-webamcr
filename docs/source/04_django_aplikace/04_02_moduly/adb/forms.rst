ADB formuláře
=============

Definice formulářů.

Třídy
------

.. py:class:: AdbReadOnlyTextInput

   Implementuje komponentu ``AdbReadOnlyTextInput`` v rámci aplikace.

   **Metody:**

   .. py:method:: format_value()

      Vrátí textový popis osoby (vypis_cely) pro zobrazení v read-only poli.

      **Parametry:**

      - ``value``: Primární klíč záznamu Osoba.

      **Návratová hodnota:**

      Textový popis osoby nebo prázdný řetězec, pokud záznam neexistuje.



.. py:class:: CreateADBForm

   Hlavní formulář pro vytvoření, editaci a zobrazení ADB.

   **Metody:**

   .. py:method:: __init__()

      Init metoda pro vytvoření formuláře.

      **Parametry:**

      - ``args``: Dodatečné poziční argumenty předané konstruktoru formuláře.
      - ``readonly``: Pokud ``True``, formulář se vykreslí jen pro čtení.
      - ``kwargs``: Dodatečné pojmenované argumenty předané konstruktoru formuláře.



.. py:class:: VyskovyBodFormSetHelper

   Form helper pro správné vykreslení formuláře výškovího bodu.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

      **Parametry:**

      - ``args``: Parametr ``args`` se předává do volání ``__init__()``.
      - ``kwargs``: Parametr ``kwargs`` se předává do volání ``__init__()``.



Funkce
------

.. py:function:: create_vyskovy_bod_form(pian, niveleta, not_readonly)

   Funkce která vrací formulář VB pro formset.

   **Parametry:**

   - ``pian``: objekt PIAN.
   - ``niveleta``: niveleta objekt.
   - ``not_readonly``: nastavuje formulář na readonly.

   **Návratová hodnota:**

   django model formulář VB.

