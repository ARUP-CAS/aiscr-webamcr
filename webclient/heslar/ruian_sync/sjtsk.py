"""
Znaménková konvence S-JTSK sdílená plným syncem i denní deltou.

Projekt ukládá EPSG:5514 v **záporné** (West-South) konvenci: souřadnice
vycházejí ze standardního Křovákova zobrazení s opačným znaménkem, takže
Y i X jsou záporné. Zdroje ČÚZK obě formy míchají – SHP dodává kladnou,
UZSZ i změnové VFR obojí –, proto se vstup vždy normalizuje.

Modul existuje proto, aby :mod:`heslar.ruian_sync.shp_importer`
i :mod:`heslar.ruian_sync.vfr_parser` používaly tutéž implementaci; dřív ji
měl každý svou.
"""

import re

#: Čísla ve WKT. Klíčová slova (``MULTIPOLYGON``, ``POINT``…) žádná čísla
#: neobsahují, takže regex přes všechna čísla míří výhradně na souřadnice.
_CISLO = re.compile(r"-?\d+(?:\.\d+)?")


def negate_wkt(wkt: str) -> str:
    """
    Invertuje znaménka všech čísel ve WKT řetězci.

    :param wkt: Vstupní WKT.
    :return: WKT se všemi čísly s opačným znaménkem.
    """

    def _flip(match):
        cislo = match.group(0)
        return cislo[1:] if cislo.startswith("-") else "-" + cislo

    return _CISLO.sub(_flip, wkt)
