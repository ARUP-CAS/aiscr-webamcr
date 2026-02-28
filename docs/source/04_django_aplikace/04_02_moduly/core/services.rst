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

      Spustí hodnotu. v aplikaci.

      :param docfile: Vstupní hodnota ``docfile`` pro danou operaci.
      :return: Vrací výsledek provedené operace.

   .. py:method:: validate_and_prepare_csv()

      Metoda pro validaci importovaného csv.

      :param csv_sheet: Popis parametru ``csv_sheet``.
      :return: Vrací výsledek operace.

   .. py:method:: validate_and_prepare_sheet()

      Metoda pro validaci importovaného excelu a jeho úpravu.

      :param sheet: Popis parametru ``sheet``.
      :return: Vrací výsledek operace.

   .. py:method:: find_missing_urls()

      Najde URL, která chybí v importní tabulce, ale v projektu

      existují, a vrátí jejich seznam.
      ignorované URL ('admin/', '__debug__/')

      :param sheet: DataFrame se vstupní tabulkou oprávnění.
      :param url_list: DataFrame se seznamem URL z projektu.
      :return: Seznam chybějících URL.
      :type sheet: pandas.DataFrame
      :type url_list: pandas.DataFrame
      :rtype: list[str]

   .. py:method:: check_save_row()

      Zkontroluje a zpracuje jeden řádek importního souboru s oprávněními

      a uloží odpovídající záznamy do databáze.

      :param row: Řádek importovaných dat.
      :param url_list: Seznam dostupných URL v projektu.
      :return: Textový stav výsledku nebo seznam výsledků pro jednotlivé role.
      :type row: pandas.Series
      :type url_list: pandas.DataFrame
      :rtype: str nebo list[str]

   .. py:method:: save_permission()

      Zkontroluje a uloží jedno konkrétní oprávnění z daného řádku

      importního souboru.

      :param row: Řádek s importovanými daty.
      :param i: Index zpracovávané role/sloupce.
      :return: True při úspěšném uložení, jinak False.
      :type row: pandas.Series
      :type i: int
      :rtype: bool

   .. py:method:: check_status_regex()

      Metoda pro kontrolu správneho zadáni statusu v excelu.

      :param cell: Popis parametru ``cell``.
      :return: Vrací výsledek operace.

