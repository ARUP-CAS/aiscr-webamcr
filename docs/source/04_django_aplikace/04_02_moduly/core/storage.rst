CORE storage
============

Modul storage.

Třídy
------

.. py:class:: NonStrictManifestStaticFilesStorage

   ManifestStaticFilesStorage odolné vůči chybějícím souborům.

   manifest_strict=False zamezuje chybám při vyhledávání v manifestu.
   Přepsání hashed_name zamezuje chybám při post-processingu, kdy JS/CSS soubory
   odkazují na soubory (typicky .map), které nejsou součástí kolekce.

   **Metody:**

   .. py:method:: hashed_name()

      Vrací hašovaný název souboru, nebo původní název pokud soubor neexistuje.

      Zachycuje :exc:`ValueError` při post-processingu JS/CSS souborů, které odkazují
      na soubory chybějící v kolekci (typicky ``.map`` soubory z npm balíčků).

      :param name: Relativní cesta k souboru.
      :param content: Obsah souboru, nebo ``None`` při vyhledávání v manifestu.
      :param filename: Název souboru pro hašování, pokud se liší od ``name``.
      :return: Hašovaný název souboru, nebo ``name`` pokud soubor nebyl nalezen.

