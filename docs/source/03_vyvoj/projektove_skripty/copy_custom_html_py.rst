Skript copy_custom_html.py
==========================

Automaticky generovaná dokumentace skriptu ``scripts/copy_custom_html.py``.

Přehled modulu
--------------

Copy custom HTML templates to the nginx data volume, preserving existing h1 content.

For each HTML file in the source directory, if a destination file already exists,
its h1 text is saved and restored into the newly copied template.

Funkce
------

.. py:function:: copy_with_preserved_h1(src, dst)

   Zkopíruje HTML šablony ze zdrojového adresáře do cílového, přičemž zachová obsah elementu h1.

   Pro každý HTML soubor ve zdrojovém adresáři: pokud cílový soubor existuje,
   uloží se text jeho h1 a po zkopírování nové šablony se obnoví.

   :param src: Zdrojový adresář s novými HTML šablonami.
   :param dst: Cílový adresář (persistentní volume).

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/copy_custom_html.py
   :language: python
   :linenos:
