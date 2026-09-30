"""
Znaménková konvence S-JTSK sdílená plným syncem i denní deltou.

Projekt ukládá EPSG:5514 v **záporné** (West-South) konvenci: souřadnice
vycházejí ze standardního Křovákova zobrazení s opačným znaménkem, takže
Y i X jsou záporné. Zdroje ČÚZK obě formy míchají – SHP dodává kladnou,
UZSZ i změnové VFR obojí –, proto se vstup vždy normalizuje.

Modul existuje proto, aby :mod:`heslar.ruian_sync.shp_importer`
i :mod:`heslar.ruian_sync.vfr_parser` používaly tutéž implementaci. Dřív
měl každý vlastní negaci i vlastní **detekci** kladné formy, a ty se už
rozcházely: jeden modul se rozhodoval podle znaménka první souřadnice X,
druhý podle toho, jestli jsou kladné obě.
"""

import re
from typing import Optional

#: Čísla ve WKT. Klíčová slova (``MULTIPOLYGON``, ``POINT``…) žádná čísla
#: neobsahují, takže regex přes všechna čísla míří výhradně na souřadnice.
_CISLO = re.compile(r"-?\d+(?:\.\d+)?")

#: První dvojice souřadnic ve WKT – vzorek, podle kterého se určuje forma.
_PRVNI_DVOJICE = re.compile(r"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)")


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


def je_kladna_forma(x: float, y: float) -> bool:
    """
    Rozhodne, jestli je dvojice souřadnic v kladné formě S-JTSK.

    Jediné místo, kde se o formě rozhoduje. Za kladnou se považuje jen dvojice,
    kde jsou kladné **obě** souřadnice: platné S-JTSK má obě souřadnice
    se stejným znaménkem, takže smíšená dvojice je vadný vstup a měnit ji
    by jen zakrylo chybu.

    :param x: První souřadnice.
    :param y: Druhá souřadnice.
    :return: ``True`` pro kladnou formu, kterou je potřeba převrátit.
    """
    return x > 0 and y > 0


def na_zapornou_formu(wkt: str) -> str:
    """
    Normalizuje WKT v EPSG:5514 na zápornou konvenci projektu.

    Forma se určuje z první dvojice souřadnic přes :func:`je_kladna_forma`;
    geometrie z jednoho zdroje má všechny body ve stejné formě.

    :param wkt: WKT v kladné nebo záporné formě.
    :return: WKT v záporné formě; beze změny, když už záporné je nebo když
        v něm žádná dvojice souřadnic není.
    """
    shoda = _PRVNI_DVOJICE.search(wkt)
    if shoda is None:
        return wkt
    if je_kladna_forma(float(shoda.group(1)), float(shoda.group(2))):
        return negate_wkt(wkt)
    return wkt


def bod_z_pos(pos_text: Optional[str]) -> Optional[str]:
    """
    Převede text ``gml:pos`` na WKT ``POINT`` v záporné konvenci.

    Používá ho načítání definičních bodů z UZSZ (plný sync) i ze změnových VFR
    (denní delta).

    :param pos_text: Obsah ``gml:pos``, např. ``"751802.14 1177969.41"``.
    :return: ``POINT(x y)`` v záporné formě, nebo ``None`` když text nemá
        aspoň dvě čísla.
    """
    casti = (pos_text or "").split()
    if len(casti) < 2:
        return None
    try:
        x, y = float(casti[0]), float(casti[1])
    except ValueError:
        return None
    if je_kladna_forma(x, y):
        x, y = -x, -y
    return f"POINT({x} {y})"
