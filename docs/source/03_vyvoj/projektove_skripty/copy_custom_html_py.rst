Skript copy_custom_html.py
==========================

Automaticky generovaná dokumentace skriptu ``scripts/copy_custom_html.py``.

Přehled modulu
--------------

Zkopíruje vlastní HTML šablony do datového svazku nginx a zachová stávající obsah nadpisů p.

U každého souboru HTML ve zdrojovém adresáři, pokud již cílový soubor existuje,
se text nadpisu p uloží a obnoví v nově zkopírované šabloně.

Funkce
------

.. py:function:: copy_with_preserved_p(src, dst)

   Zkopíruje HTML šablony ze zdrojového adresáře do cílového, přičemž zachová obsah elementu p.

   Pro každý HTML soubor ve zdrojovém adresáři: pokud cílový soubor existuje,
   uloží se text jeho p a po zkopírování nové šablony se obnoví.

   :param src: Zdrojový adresář s novými HTML šablonami.
   :param dst: Cílový adresář (persistentní volume).

Zdrojový kód
------------

.. literalinclude:: ../../../../scripts/copy_custom_html.py
   :language: python
   :linenos:
