CORE services
=============

Modul services.

Třídy
------

.. py:class:: PermissionService

   Třída pro načtení oprávnení.

   **Metody:**

   .. py:method:: __init__()

   .. py:method:: run()

      Zpracuje nahraný soubor s oprávněními, provede validaci, import oprávnění
      a vrátí upravený list a seznam chybějících URL.
      
      :param docfile: Nahraný CSV nebo Excel soubor s definicí oprávnění.
      :type docfile: InMemoryUploadedFile
      :return: Dvojice obsahující zpracovaný DataFrame a seznam chybějících URL.
      :rtype: tuple[pandas.DataFrame, list[str]]

   .. py:method:: validate_and_prepare_csv()

      Metoda pro validaci importovaného csv.

   .. py:method:: validate_and_prepare_sheet()

      Metoda pro validaci importovaného excelu a jeho úpravu.

   .. py:method:: find_missing_urls()

      Najde URL, která chybí v importní tabulce, ale v projektu
      existují, a vrátí jejich seznam.
      ignorované URL ('admin/', '__debug__/')
      
      :param sheet: DataFrame se vstupní tabulkou oprávnění.
      :type sheet: pandas.DataFrame
      :param url_list: DataFrame se seznamem URL z projektu.
      :type url_list: pandas.DataFrame
      :return: Seznam chybějících URL.
      :rtype: list[str]

   .. py:method:: check_save_row()

      Zkontroluje a zpracuje jeden řádek importního souboru s oprávněními
      a uloží odpovídající záznamy do databáze.
      
      :param row: Řádek importovaných dat.
      :type row: pandas.Series
      :param url_list: Seznam dostupných URL v projektu.
      :type url_list: pandas.DataFrame
      :return: Textový stav výsledku nebo seznam výsledků pro jednotlivé role.
      :rtype: str nebo list[str]

   .. py:method:: save_permission()

      Zkontroluje a uloží jedno konkrétní oprávnění z daného řádku
      importního souboru.
      
      :param row: Řádek s importovanými daty.
      :type row: pandas.Series
      :param i: Index zpracovávané role/sloupce.
      :type i: int
      :return: True při úspěšném uložení, jinak False.
      :rtype: bool

   .. py:method:: check_status_regex()

      Metoda pro kontrolu správneho zadáni statusu v excelu.

