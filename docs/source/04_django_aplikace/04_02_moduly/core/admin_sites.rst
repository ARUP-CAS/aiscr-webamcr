CORE admin_sites
================

Modul admin_sites.

Třídy
------

.. py:class:: AmcrCustomAdminSite

   Vlastní admin site AMČR s reorganizovanou strukturou menu a správou dat.

   **Metody:**

   .. py:method:: get_app_list()

      Reorganizuje seznam aplikací v admin rozhraní do požadované struktury menu.

      :param request: HTTP požadavek.
      :param app_label: Volitelný label aplikace pro filtrování.
      :return: Vrací reorganizovaný seznam aplikací.

   .. py:method:: _read_file()

      Načte CSV/XLSX soubor se seznamem identifikátorů a převede jej na DataFrame.

      :param uploaded_file: Nahraný soubor z formuláře; podle ``content_type`` se načte jako CSV nebo Excel.
      :param context: Slovník kontextu pro šablonu; při chybě čtení nebo neplatném formátu se do něj uloží klíč ``error``.
      :return: DataFrame s jedním sloupcem ``ident_cely`` indexovaným touto hodnotou, nebo ``None`` při chybě.

   .. py:method:: update_doi()

      Zpracuje hromadnou aktualizaci DOI/IGSN podle nahraného seznamu identifikátorů.

      :param request: HTTP požadavek; u ``POST`` od superuživatele validuje formulář, připraví job v Redis a vrátí stránku průběhu.
      :return: Odpověď ``TemplateResponse`` s formulářem nebo stránkou spuštěného jobu.

   .. py:method:: update_metadata_file_upload()

      Zpracuje hromadnou aktualizaci metadat ve Fedora repozitáři.

      :param request: HTTP požadavek; u ``POST`` od superuživatele validuje formulář, připraví job v Redis a vrátí stránku průběhu.
      :return: Odpověď ``TemplateResponse`` s formulářem nebo stránkou spuštěného jobu.

   .. py:method:: update_katastry_file_upload()

      Zpracuje hromadný přepočet katastrů u záznamů Projekt/AZ/SN.

      Přijímá CSV/XLSX se sloupcem ``ident_cely`` (jeden záznam na řádek),
      založí job v Redis pod prefixem ``update_katastry_`` a deleguje vlastní
      zpracování na :class:`heslar.views.ContinueKatastrProcessing` (polovaný
      z JS na stránce průběhu).

      :param request: HTTP požadavek; ``POST`` od superuživatele validuje formulář a připraví job.

      :return: Odpověď ``TemplateResponse`` s formulářem nebo stránkou průběhu.

   .. py:method:: import_data()

      Importuje datové CSV soubory ze ZIP archivu do interní importní fronty.

      :param request: HTTP požadavek; při ``POST`` od superuživatele zvaliduje vstupní formulář,
          zpracuje obsah ZIPu, provede validační kroky přes mapery a uloží připravené záznamy do Redis.
      :return: Odpověď ``TemplateResponse`` s výsledkem validace, případně s chybovou hláškou importu.
      :raises ImportDataUnsupportedFilesError: Vyvolá se, pokud ZIP obsahuje soubory mimo povolenou sadu názvů.
      :raises ImportDataUnsupportedFileError: Vyvolá se, pokud pro nalezený CSV soubor neexistuje mapper.

   .. py:method:: get_urls()

      Vrátí vlastní URL cesty admin site pro hromadné operace.

      :return: Seznam URL vzorů rozšířený o cesty pro aktualizaci metadat,
          aktualizaci DOI/IGSN a hromadný import dat.

