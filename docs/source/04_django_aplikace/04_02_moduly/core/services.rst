CORE services
=============

Modul services.

Třídy
------

.. py:class:: PermissionService

   Třída pro načtení oprávnení.

   **Metody:**

   .. py:method:: __init__()

      Inicializuje instanci třídy.

   .. py:method:: run()

      Zpracuje nahraný soubor s oprávněními, provede validaci, import oprávnění
      a vrátí upravený list a seznam chybějících URL.

      **Parametry:**

      - ``docfile``: Parametr ``docfile`` se předává do volání ``read_csv()``, ``read_excel()``, pracuje se s atributy ``name``, ovlivňuje větvení podmínek. Nahraný CSV nebo Excel soubor s definicí oprávnění.

      **Návratová hodnota:**

      Výstup funkce odpovídající implementované logice. Dvojice obsahující zpracovaný DataFrame a seznam chybějících URL.


   .. py:method:: validate_and_prepare_csv()

      Metoda pro validaci importovaného csv.

      **Parametry:**

      - ``csv_sheet``: Parametr ``csv_sheet`` pracuje se s atributy ``columns``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek operace.

      **Výjimky:**

      - ``WrongCSVError``: Pokud CSV neodpovídá očekávané struktuře sloupců.


   .. py:method:: validate_and_prepare_sheet()

      Metoda pro validaci importovaného excelu a jeho úpravu.

      **Parametry:**

      - ``sheet``: Parametr ``sheet`` pracuje se s atributy ``columns``, ``iloc``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek operace.

      **Výjimky:**

      - ``WrongSheetError``: Pokud list neodpovídá očekávanému formátu importní šablony.


   .. py:method:: find_missing_urls()

      Najde URL, která chybí v importní tabulce, ale v projektu

      existují, a vrátí jejich seznam.
      ignorované URL ('admin/', '__debug__/')

      **Parametry:**

      - ``sheet`` (*pandas.DataFrame*): DataFrame se vstupní tabulkou oprávnění.
      - ``url_list`` (*pandas.DataFrame*): DataFrame se seznamem URL z projektu.

      **Návratová hodnota:**

      Seznam chybějících URL.

      *Typ:* list[str]


   .. py:method:: check_save_row()

      Zkontroluje a zpracuje jeden řádek importního souboru s oprávněními

      a uloží odpovídající záznamy do databáze.

      **Parametry:**

      - ``row`` (*pandas.Series*): Řádek importovaných dat.
      - ``url_list`` (*pandas.DataFrame*): Seznam dostupných URL v projektu.

      **Návratová hodnota:**

      Textový stav výsledku nebo seznam výsledků pro jednotlivé role.

      *Typ:* str nebo list[str]


   .. py:method:: save_permission()

      Zkontroluje a uloží jedno konkrétní oprávnění z daného řádku

      importního souboru.

      **Parametry:**

      - ``row`` (*pandas.Series*): Řádek s importovanými daty.
      - ``i`` (*int*): Index zpracovávané role/sloupce.

      **Návratová hodnota:**

      True při úspěšném uložení, jinak False.

      *Typ:* bool


   .. py:method:: check_status_regex()

      Metoda pro kontrolu správneho zadáni statusu v excelu.

      **Parametry:**

      - ``cell``: Parametr ``cell`` se předává do volání ``bool()``, ``fullmatch()``, vstupuje do návratové hodnoty.

      **Návratová hodnota:**

      Vrací výsledek operace.


