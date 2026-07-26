"""
Pomocné funkce pro suffixové schéma názvů souborů (issue #3487).

Suffix je část názvu mezi identem záznamu (bez pomlček) a příponou:

* dokumenty (včetně 3D modelů): prázdný řetězec (základní soubor ``{ident}.{ext}``) a písmena ``A``–``Z``,
* samostatné nálezy: ``F01`` … ``F99``.

Modul záměrně nezávisí na modelech ani views, aby jej mohly používat obě vrstvy bez cyklických importů.
"""

import os
from string import ascii_uppercase as letters


def _obsazene_suffixy(navazany_objekt, base, current_soubor=None):
    """
    Vrátí množinu suffixů (částí názvu mezi identem a příponou) obsazených soubory záznamu.

    :param navazany_objekt: Navázaný objekt (dokument nebo samostatný nález) s vazbou ``soubory``.
    :param base: Identifikátor záznamu bez pomlček, kterým názvy souborů začínají.
    :param current_soubor: Soubor, který se přejmenovává a do obsazených suffixů se nezapočítává.
    :return: Množina řetězců suffixů obsazených ostatními soubory.
    """
    obsazene = set()
    for soubor in navazany_objekt.soubory.soubory.all():
        if current_soubor is not None and soubor.pk == current_soubor.pk:
            continue
        stem = os.path.splitext(soubor.nazev)[0]
        if stem.startswith(base):
            obsazene.add(stem[len(base) :])
    return obsazene


def get_dokument_free_suffixes(dokument, current_soubor=None):
    """
    Vrátí seznam volných suffixů pro soubory dokumentu (platí pro všechny dokumenty včetně 3D modelů).

    Možné hodnoty jsou prázdný řetězec (základní soubor ``{ident}.{ext}``) a písmena ``A``–``Z``.
    Suffix přejmenovávaného souboru se považuje za volný, aby jej bylo možné v nabídce ponechat.

    :param dokument: Dokument, jehož soubory se zkoumají.
    :param current_soubor: Přejmenovávaný soubor (vyloučen z obsazených suffixů).
    :return: Seznam volných suffixů v pořadí prázdný slot, ``A`` … ``Z``.
    """
    base = dokument.ident_cely.replace("-", "")
    obsazene = _obsazene_suffixy(dokument, base, current_soubor)
    return [suffix for suffix in [""] + list(letters) if suffix not in obsazene]


def get_finds_free_suffixes(find, current_soubor=None):
    """
    Vrátí seznam volných suffixů pro soubory samostatného nálezu.

    Suffix má tvar ``F01`` … ``F99``. Suffix přejmenovávaného souboru se považuje za volný.

    :param find: Samostatný nález, jehož soubory se zkoumají.
    :param current_soubor: Přejmenovávaný soubor (vyloučen z obsazených suffixů).
    :return: Seznam volných suffixů v pořadí ``F01`` … ``F99``.
    """
    base = find.ident_cely.replace("-", "")
    obsazene = _obsazene_suffixy(find, base, current_soubor)
    return [f"F{number:02d}" for number in range(1, 100) if f"F{number:02d}" not in obsazene]


def get_soubor_suffix(soubor):
    """
    Vrátí aktuální suffix souboru (část názvu mezi identem záznamu bez pomlček a příponou).

    :param soubor: Soubor, jehož suffix se zjišťuje.
    :return: Řetězec suffixu (může být prázdný); ``None`` pokud název neodpovídá očekávanému vzoru.
    """
    base = soubor.vazba.navazany_objekt.ident_cely.replace("-", "")
    stem = os.path.splitext(soubor.nazev)[0]
    if stem.startswith(base):
        return stem[len(base) :]
    return None
