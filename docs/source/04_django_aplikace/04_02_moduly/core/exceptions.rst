CORE exceptions
===============

Modul exceptions.

Třídy
------

.. py:class:: PianNotInKladysm5Error

   Implementuje komponentu ``PianNotInKladysm5Error`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku s odkazem na PIAN, jehož geometrie neleží v žádném kladu mapových listů.

      :param pian: Instance PIANu, jehož geometrie se nenachází v žádném kladu mapových listů.
      :param message: Textová zpráva popisující důvod výjimky.


.. py:class:: MaximalIdentNumberError

   Implementuje komponentu ``MaximalIdentNumberError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku s číslem identifikátoru, které překročilo povolené maximum.

      :param number: Číslo identifikátoru, které překročilo maximální povolenou hodnotu.
      :param message: Textová zpráva popisující důvod výjimky.


.. py:class:: DJNemaPianError

   Implementuje komponentu ``DJNemaPianError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy dokumentační jednotka nemá přiřazen žádný PIAN.

      :param dj: Instance dokumentační jednotky, která postrádá přiřazený PIAN.
      :param message: Textová zpráva popisující důvod výjimky.


.. py:class:: NelzeZjistitRaduError

   Implementuje komponentu ``NelzeZjistitRaduError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy nelze určit řadu dokumentu.

      :param message: Textová zpráva popisující důvod výjimky.


.. py:class:: NeocekavanaRadaError

   Implementuje komponentu ``NeocekavanaRadaError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy je zjištěna neočekávaná řada dokumentu.

      :param message: Textová zpráva popisující důvod výjimky.


.. py:class:: WrongSheetError

   Implementuje komponentu ``WrongSheetError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy importovaný Excel soubor nemá správné sloupce.

      :param message: Textová zpráva popisující důvod výjimky.


.. py:class:: NeznamaGeometrieError

   Implementuje komponentu ``NeznamaGeometrieError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy je zjištěn neznámý nebo neočekávaný typ geometrie PIANu.

      :param message: Textová zpráva popisující důvod výjimky.


.. py:class:: UnexpectedDataRelations

   Implementuje komponentu ``UnexpectedDataRelations`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ duplicitních nebo chybějících datových relací při importu.

      :param message: Textová zpráva popisující důvod výjimky.


.. py:class:: MaximalEventCount

   Implementuje komponentu ``MaximalEventCount`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy byl překročen maximální počet archeologických akcí.

      :param number: Aktuální počet akcí, jenž překročil povolené maximum.
      :param message: Textová zpráva popisující důvod výjimky.


.. py:class:: WrongCSVError

   Implementuje komponentu ``WrongCSVError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy importovaný CSV soubor nemá správné sloupce.

      :param message: Textová zpráva popisující důvod výjimky.


.. py:class:: ZaznamSouborNotmatching

   Implementuje komponentu ``ZaznamSouborNotmatching`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy záznam AMČR neobsahuje očekávaný soubor.

      :param message: Textová zpráva popisující důvod výjimky.


.. py:class:: StateChangedError

   Implementuje komponentu ``StateChangedError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy byl stav záznamu AMČR změněn jiným uživatelem od jeho načtení.

      :param message: Textová zpráva popisující důvod výjimky.

