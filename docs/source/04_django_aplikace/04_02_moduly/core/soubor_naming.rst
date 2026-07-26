CORE soubor_naming
==================

Modul soubor_naming.

Přehled modulu
--------------

Pomocné funkce pro suffixové schéma názvů souborů (issue #3487).

Suffix je část názvu mezi identem záznamu (bez pomlček) a příponou:

* dokumenty (včetně 3D modelů): prázdný řetězec (základní soubor ``{ident}.{ext}``) a písmena ``A``–``Z``,
* samostatné nálezy: ``F01`` … ``F99``.

Modul záměrně nezávisí na modelech ani views, aby jej mohly používat obě vrstvy bez cyklických importů.

Funkce
------

.. py:function:: _obsazene_suffixy(navazany_objekt, base, current_soubor)

   Vrátí množinu suffixů (částí názvu mezi identem a příponou) obsazených soubory záznamu.

   :param navazany_objekt: Navázaný objekt (dokument nebo samostatný nález) s vazbou ``soubory``.
   :param base: Identifikátor záznamu bez pomlček, kterým názvy souborů začínají.
   :param current_soubor: Soubor, který se přejmenovává a do obsazených suffixů se nezapočítává.
   :return: Množina řetězců suffixů obsazených ostatními soubory.

.. py:function:: get_dokument_free_suffixes(dokument, current_soubor)

   Vrátí seznam volných suffixů pro soubory dokumentu (platí pro všechny dokumenty včetně 3D modelů).

   Možné hodnoty jsou prázdný řetězec (základní soubor ``{ident}.{ext}``) a písmena ``A``–``Z``.
   Suffix přejmenovávaného souboru se považuje za volný, aby jej bylo možné v nabídce ponechat.

   :param dokument: Dokument, jehož soubory se zkoumají.
   :param current_soubor: Přejmenovávaný soubor (vyloučen z obsazených suffixů).
   :return: Seznam volných suffixů v pořadí prázdný slot, ``A`` … ``Z``.

.. py:function:: get_finds_free_suffixes(find, current_soubor)

   Vrátí seznam volných suffixů pro soubory samostatného nálezu.

   Suffix má tvar ``F01`` … ``F99``. Suffix přejmenovávaného souboru se považuje za volný.

   :param find: Samostatný nález, jehož soubory se zkoumají.
   :param current_soubor: Přejmenovávaný soubor (vyloučen z obsazených suffixů).
   :return: Seznam volných suffixů v pořadí ``F01`` … ``F99``.

.. py:function:: get_soubor_suffix(soubor)

   Vrátí aktuální suffix souboru (část názvu mezi identem záznamu bez pomlček a příponou).

   :param soubor: Soubor, jehož suffix se zjišťuje.
   :return: Řetězec suffixu (může být prázdný); ``None`` pokud název neodpovídá očekávanému vzoru.
