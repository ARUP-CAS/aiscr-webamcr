CORE soubor_naming
==================

Modul soubor_naming.

Přehled modulu
--------------

Pomocné funkce pro suffixové schéma názvů souborů (issue #3487, #3421).

Suffix je část názvu mezi identem záznamu (bez pomlček) a příponou. Nově má u dokumentů
(včetně 3D modelů) i u samostatných nálezů jednotný tvar ``F001`` … ``F999`` a přiděluje se
již prvnímu souboru záznamu (#3421).

Historická data zůstávají beze změny – u dokumentů jde o prázdný suffix (základní soubor
``{ident}.{ext}``) a písmena ``A``–``Z``, u samostatných nálezů o dvojciferné ``F01`` … ``F99``.
Tyto suffixy se nově nepřidělují, jen se u přejmenovávaného souboru ponechají v nabídce.

Modul záměrně nezávisí na modelech ani views, aby jej mohly používat obě vrstvy bez cyklických importů.

Funkce
------

.. py:function:: format_suffix(number)

   Sestaví suffix názvu souboru z pořadového čísla.

   :param number: Pořadové číslo souboru v rámci záznamu.
   :return: Suffix ve tvaru ``F`` a pořadové číslo doplněné nulami na :data:`SUFFIX_DIGIT_COUNT` číslic.

.. py:function:: _obsazene_suffixy(navazany_objekt, base, current_soubor)

   Vrátí množinu suffixů (částí názvu mezi identem a příponou) obsazených soubory záznamu.

   :param navazany_objekt: Navázaný objekt (dokument nebo samostatný nález) s vazbou ``soubory``.
   :param base: Identifikátor záznamu bez pomlček, kterým názvy souborů začínají.
   :param current_soubor: Soubor, který se přejmenovává a do obsazených suffixů se nezapočítává.
   :return: Množina řetězců suffixů obsazených ostatními soubory.

.. py:function:: _obsazena_cisla(obsazene)

   Vrátí množinu pořadových čísel, která jsou obsazená číslovanými suffixy.

   Historické suffixy dokumentů (prázdný slot a písmena) žádné pořadové číslo nenesou a do množiny
   nepatří. Dvojciferné suffixy samostatných nálezů (``F01`` … ``F99``) naopak obsazují stejné číslo
   jako jejich trojciferná podoba, aby se ``F01`` a ``F001`` nemohly u jednoho záznamu sejít.

   :param obsazene: Množina obsazených suffixů.
   :return: Množina obsazených pořadových čísel.

.. py:function:: get_next_soubor_name(navazany_objekt, filename)

   Vrátí název pro nově nahrávaný soubor záznamu ve tvaru ``{ident}F###.{ext}``.

   Pořadové číslo se určuje navýšením nejvyššího obsazeného čísla, uvolněná nižší čísla se
   nedoplňují. Uvolnění či změnu pozice řeší přejmenování souboru, ne toto přidělování.

   :param navazany_objekt: Dokument nebo samostatný nález, ke kterému se soubor nahrává.
   :param filename: Původní název nahrávaného souboru (použije se jeho přípona).
   :return: Nový název souboru, nebo ``False`` při vyčerpání všech pořadových čísel.

.. py:function:: get_free_suffixes(navazany_objekt, current_soubor)

   Vrátí seznam volných suffixů záznamu ve tvaru ``F001`` … ``F999``.

   Platí shodně pro dokumenty (včetně 3D modelů) i samostatné nálezy. Suffix přejmenovávaného
   souboru se považuje za volný, aby jej bylo možné v nabídce ponechat; pokud jde o historický
   suffix (prázdný slot, písmeno nebo dvojciferné ``F01``), zařadí se na začátek nabídky.

   :param navazany_objekt: Dokument nebo samostatný nález, jehož soubory se zkoumají.
   :param current_soubor: Přejmenovávaný soubor (vyloučen z obsazených suffixů).
   :return: Seznam volných suffixů ve vzestupném pořadí.

.. py:function:: get_soubor_suffix(soubor)

   Vrátí aktuální suffix souboru (část názvu mezi identem záznamu bez pomlček a příponou).

   :param soubor: Soubor, jehož suffix se zjišťuje.
   :return: Řetězec suffixu (může být prázdný); ``None`` pokud název neodpovídá očekávanému vzoru.
