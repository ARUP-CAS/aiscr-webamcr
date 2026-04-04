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

      **Parametry:**

      - ``pian``: Instance PIANu, jehož geometrie se nenachází v žádném kladu mapových listů.
      - ``message``: Textová zpráva popisující důvod výjimky.



.. py:class:: MaximalIdentNumberError

   Implementuje komponentu ``MaximalIdentNumberError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku s číslem identifikátoru, které překročilo povolené maximum.

      **Parametry:**

      - ``number``: Číslo identifikátoru, které překročilo maximální povolenou hodnotu.
      - ``message``: Textová zpráva popisující důvod výjimky.



.. py:class:: DJNemaPianError

   Implementuje komponentu ``DJNemaPianError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy dokumentační jednotka nemá přiřazen žádný PIAN.

      **Parametry:**

      - ``dj``: Instance dokumentační jednotky, která postrádá přiřazený PIAN.
      - ``message``: Textová zpráva popisující důvod výjimky.



.. py:class:: NelzeZjistitRaduError

   Implementuje komponentu ``NelzeZjistitRaduError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy nelze určit řadu dokumentu.

      **Parametry:**

      - ``message``: Textová zpráva popisující důvod výjimky.



.. py:class:: NeocekavanaRadaError

   Implementuje komponentu ``NeocekavanaRadaError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy je zjištěna neočekávaná řada dokumentu.

      **Parametry:**

      - ``message``: Textová zpráva popisující důvod výjimky.



.. py:class:: WrongSheetError

   Implementuje komponentu ``WrongSheetError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy importovaný Excel soubor nemá správné sloupce.

      **Parametry:**

      - ``message``: Textová zpráva popisující důvod výjimky.



.. py:class:: NeznamaGeometrieError

   Implementuje komponentu ``NeznamaGeometrieError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy je zjištěn neznámý nebo neočekávaný typ geometrie PIANu.

      **Parametry:**

      - ``message``: Textová zpráva popisující důvod výjimky.



.. py:class:: UnexpectedDataRelations

   Implementuje komponentu ``UnexpectedDataRelations`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ duplicitních nebo chybějících datových relací při importu.

      **Parametry:**

      - ``message``: Textová zpráva popisující důvod výjimky.



.. py:class:: MaximalEventCount

   Implementuje komponentu ``MaximalEventCount`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy byl překročen maximální počet archeologických akcí.

      **Parametry:**

      - ``number``: Aktuální počet akcí, jenž překročil povolené maximum.
      - ``message``: Textová zpráva popisující důvod výjimky.



.. py:class:: WrongCSVError

   Implementuje komponentu ``WrongCSVError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy importovaný CSV soubor nemá správné sloupce.

      **Parametry:**

      - ``message``: Textová zpráva popisující důvod výjimky.



.. py:class:: ZaznamSouborNotmatching

   Implementuje komponentu ``ZaznamSouborNotmatching`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy záznam AMČR neobsahuje očekávaný soubor.

      **Parametry:**

      - ``message``: Textová zpráva popisující důvod výjimky.



.. py:class:: StateChangedError

   Implementuje komponentu ``StateChangedError`` v rámci aplikace.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje výjimku pro případ, kdy byl stav záznamu AMČR změněn jiným uživatelem od jeho načtení.

      **Parametry:**

      - ``message``: Textová zpráva popisující důvod výjimky.


