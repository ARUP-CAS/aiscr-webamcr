"""
Streamovaný parser **denního změnového** VFR souboru (GML 3.2.1) z ČÚZK.

Modul implementuje :func:`parse_changes`, která načte denní změnový VFR
(``ST_ZKSH`` – originální hranice; jediná varianta, kterou AMČR používá)
a vrátí iterátor :class:`RuianChangeEvent` (upserty + delete). Volá se
z :class:`heslar.ruian_sync.provider.FileVfrSource` v Celery cronu
:func:`cron.tasks.sync_ruian_changes`.

Pro plný (initial) sync **není** modul určen – ten řeší
:class:`heslar.ruian_sync.shp_importer.ShpUzszSource` (SHP polygony +
``ST_UZSZ`` definiční body, výrazně jednodušší pipeline).

Implementační poznámky:

* používá ``lxml.etree.iterparse`` se streamováním (konstantní paměť);
* namespace prefixy se ignorují – matching probíhá přes
  ``etree.QName(elem.tag).localname`` (VFR specifikace v4.0 nezaručuje stabilní
  prefixy);
* ZIP archiv otevírá přes ``zipfile.ZipFile`` a streamuje XML přímo z něj
  bez rozbalování na disk;
* geometrie se převádí z EPSG:5514 na EPSG:4326 přes existující
  ``core.coordTransform.transform_geom_to_wgs84``;
* okres katastru se rezolvuje přes přechodný map ``obec_kod → okres_kod``
  z téhož souboru; pokud obec ve změnovém souboru chybí, syncer dohledá
  okres z DB.

Parser čte výhradně variantu **ZKSH** (denní změnový + originální hranice
katastrů). Jiné varianty (``ZKSG`` generalizované, ``ZZSZ`` bez polygonů)
nejsou potřeba – AMČR potřebuje pouze originální hranice.
"""

from __future__ import annotations

import logging
import re
import zipfile
from pathlib import Path
from typing import Iterator, Optional, Tuple

from core.coordTransform import transform_geom_to_wgs84
from heslar.ruian_sync.provider import (
    EVENT_DELETE,
    EVENT_UPSERT,
    LEVEL_KATASTR,
    LEVEL_KRAJ,
    LEVEL_OKRES,
    RuianChangeEvent,
    RuianKatastrDTO,
    RuianKrajDTO,
    RuianOkresDTO,
)
from lxml import etree

logger = logging.getLogger(__name__)


class RuianMissingMandatoryFieldError(Exception):
    """
    Vyhozeno, pokud je v DB potřeba uložit nový kraj/okres, ale VFR
    neposkytuje povinné pole (``rada_id`` u kraje, ``spz`` u okresu).

    Volající (syncer) zachytí, zaloguje a označí ``RuianSyncRun.status="failed"``.
    """

    def __init__(self, level: str, kod: int, missing: list):
        """
        :param level: Úroveň prvku (``"kraj"`` / ``"okres"``).
        :param kod: Kód prvku.
        :param missing: Seznam názvů chybějících polí.
        """
        super().__init__(f"Nový {level} kód={kod} – chybí povinná pole: {', '.join(missing)}")
        self.level = level
        self.kod = kod
        self.missing = missing


# ---------------------------------------------------------------------------
# Veřejné API
# ---------------------------------------------------------------------------


def parse_changes(path: Path) -> Iterator[RuianChangeEvent]:
    """
    Načte denní změnový VFR (variantu ``ZKSH`` – originální hranice) a vrací
    iterátor událostí.

    Změnový soubor obsahuje **změněné/nové** prvky (struktura stejná jako
    stavová) plus kolekci ``ZaniklePrvky/ZaniklyPrvek`` pro mazání.

    :param path: Cesta k VFR ZIP/XML souboru.

        :return: Generátor :class:`RuianChangeEvent` v pořadí (Vusc, Okres, KU, ZaniklePrvek).
    """
    logger.debug("heslar.ruian_sync.vfr_parser.parse_changes.start", extra={"path": str(path)})

    # Pro upserty potřebujeme obec_okres mapu z toho samého souboru
    # (změnový obsahuje jen změněné obce – ostatní okres rezolvujeme z DB).
    obec_okres_map: dict = {}
    for elem in _iter_elements(path, ("Obec",)):
        if not _is_historical(elem):
            kod = _first_text_int(elem, "Kod")
            okres_kod = _nested_int(elem, "Okres", "Kod")
            if kod is not None and okres_kod is not None:
                obec_okres_map[kod] = okres_kod
        elem.clear()

    # Hlavní průchod – upserty pro Vusc/Okres/KU + delete pro ZaniklyPrvek
    for elem in _iter_elements(path, ("Vusc", "Okres", "KatastralniUzemi", "ZaniklyPrvek")):
        local = etree.QName(elem.tag).localname
        if local == "Vusc":
            dto = _parse_kraj_dto(elem)
            if dto is not None:
                yield RuianChangeEvent(level=LEVEL_KRAJ, event_type=EVENT_UPSERT, kod=dto.kod, payload=dto)
        elif local == "Okres":
            dto = _parse_okres_dto(elem)
            if dto is not None:
                yield RuianChangeEvent(level=LEVEL_OKRES, event_type=EVENT_UPSERT, kod=dto.kod, payload=dto)
        elif local == "KatastralniUzemi":
            dto = _parse_katastr_dto(elem, obec_okres_map=obec_okres_map)
            if dto is not None:
                yield RuianChangeEvent(level=LEVEL_KATASTR, event_type=EVENT_UPSERT, kod=dto.kod, payload=dto)
        elif local == "ZaniklyPrvek":
            ev = _parse_zanikly_prvek(elem)
            if ev is not None:
                yield ev
        elem.clear()

    logger.debug("heslar.ruian_sync.vfr_parser.parse_changes.end")


# ---------------------------------------------------------------------------
# Iterace ZIP/XML přes lxml.iterparse
# ---------------------------------------------------------------------------


def _open_xml_stream(path: Path):
    """
    Otevře XML stream z VFR ZIPu (nebo přímo z XML souboru, pokud není ZIP).

    :param path: Cesta k souboru.

        :return: File-like objekt s XML obsahem.
        :raises ValueError: Pokud ZIP neobsahuje XML.
    """
    p = Path(path)
    if p.suffix.lower() == ".zip" or zipfile.is_zipfile(str(p)):
        zf = zipfile.ZipFile(str(p))
        xml_names = [n for n in zf.namelist() if n.lower().endswith(".xml")]
        if not xml_names:
            raise ValueError(f"VFR ZIP neobsahuje žádný .xml soubor: {p}")
        return zf.open(xml_names[0])
    return open(str(p), "rb")


#: Povolené rodičovské kontejnery pro každý target localname.
#:
#: VFR má stejný název kolekce a prvku pro ``Vusc`` a ``KatastralniUzemi``
#: (např. ``<vf:KatastralniUzemi><vf:KatastralniUzemi>...</vf:KatastralniUzemi></vf:KatastralniUzemi>``).
#: Filtrování podle rodiče zaručí, že yieldujeme pouze **definice** (přímí
#: potomci kontejnerů), nikoliv **reference** uvnitř Parcela/Zsj/Obec atd.,
#: které obsahují jen ``<Kod>`` a způsobily by nesprávné DTO i destruktivní
#: cleanup nadřazených prvků.
_TARGET_PARENTS = {
    "Vusc": {"Vusc"},  # kolekce VUSC se jmenuje stejně jako prvek
    "Okres": {"Okresy"},
    "Obec": {"Obce"},
    "KatastralniUzemi": {"KatastralniUzemi"},  # kolekce KU se jmenuje stejně
    "ZaniklyPrvek": {"ZaniklePrvky"},
}


def _iter_elements(path: Path, local_names: Tuple[str, ...]) -> Iterator:
    """
    Iteruje skončené elementy odpovídající zadaným local-names.

    Yield se provede pouze tehdy, když je rodič elementu správný kontejner
    (viz :data:`_TARGET_PARENTS`). Tím se vyloučí reference uvnitř ostatních
    prvků (např. ``<Parcela><KatastralniUzemi><Kod>X</Kod></KatastralniUzemi></Parcela>``)
    a zabrání se destruktivnímu cleanupu vnořených struktur.

    Po vyieldování top-level elementu se uvolní předchozí siblingy (snížení
    paměti při velkých kolekcích).

    :param path: Cesta k VFR souboru.
    :param local_names: Tuple local-names (bez namespace prefixu) k matchnutí.

        :return: Generátor lxml elementů.
    """
    target_set = set(local_names)
    stream = _open_xml_stream(path)
    try:
        ctx = etree.iterparse(stream, events=("end",), huge_tree=True)
        for _, elem in ctx:
            local = etree.QName(elem.tag).localname
            if local not in target_set:
                continue
            parent = elem.getparent()
            if parent is None:
                continue
            parent_local = etree.QName(parent.tag).localname
            allowed = _TARGET_PARENTS.get(local)
            if allowed is not None and parent_local not in allowed:
                # Reference uvnitř jiného prvku (např. Parcela/KatastralniUzemi).
                continue
            yield elem
            # Uvolnění předchozích siblingů (snížení paměti)
            while elem.getprevious() is not None:
                del parent[0]
    finally:
        stream.close()


# ---------------------------------------------------------------------------
# DTO extraktory
# ---------------------------------------------------------------------------


def _is_historical(elem) -> bool:
    """
    Vrací True, pokud má prvek vyplněné ``PlatiDo`` (= je historický/zaniklý).

    VFR publikuje i historické (zaniklé) prvky pro audit – mají nastavené
    ``<PlatiDo>2015-12-31T23:59:59</PlatiDo>``. Ty pro náš sync ignorujeme,
    pracujeme jen s aktuálně platnými záznamy.

    Kontroluje **přímé potomky** elementu (ne rekurzivně), aby se nezachytilo
    ``PlatiDo`` z vnořených referencí (např. uvnitř ``Vusc``).

    :param elem: lxml element prvku (``Vusc``/``Okres``/``KatastralniUzemi``).

        :return: ``True`` pokud má prvek vyplněné ``PlatiDo``.
    """
    for child in elem:
        if etree.QName(child.tag).localname == "PlatiDo":
            text = (child.text or "").strip()
            return bool(text)
    return False


def _parse_kraj_dto(elem) -> Optional[RuianKrajDTO]:
    """
    Vytvoří :class:`RuianKrajDTO` z elementu ``Vusc``.

    Vrací ``None`` pokud:

    * prvek je historický (vyplněné ``PlatiDo``),
    * chybí povinný ``Kod`` nebo ``Nazev``.

    :param elem: lxml element ``vf:Vusc``.

        :return: DTO nebo ``None``.
    """
    if _is_historical(elem):
        return None
    kod = _first_text_int(elem, "Kod")
    nazev = _first_text(elem, "Nazev")
    if kod is None or not nazev:
        logger.debug(
            "heslar.ruian_sync.vfr_parser._parse_kraj_dto.skip_incomplete",
            extra={"kod": kod, "nazev": nazev},
        )
        return None
    db_wkt = _extract_definicni_bod(elem)
    hr_wkt = _extract_hranice(elem)
    return RuianKrajDTO(
        kod=kod,
        nazev=nazev,
        nazev_en=None,  # VFR neposkytuje
        rada_id="",  # VFR neposkytuje – syncer řeší
        definicni_bod_wkt=db_wkt,
        hranice_wkt=hr_wkt,
    )


def _parse_okres_dto(elem) -> Optional[RuianOkresDTO]:
    """
    Vytvoří :class:`RuianOkresDTO` z elementu ``Okres``.

    Vazba na kraj se odvozuje z ``Okres/Vusc/Kod`` (vazba ``Okres/Kraj``
    je od zákona 51/2020 vyprázdněna).

    Vrací ``None`` pokud:

    * prvek je historický (vyplněné ``PlatiDo``),
    * chybí povinný ``Kod`` nebo ``Nazev``.

    :param elem: lxml element ``vf:Okres``.

        :return: DTO nebo ``None``.
    """
    if _is_historical(elem):
        return None
    kod = _first_text_int(elem, "Kod")
    nazev = _first_text(elem, "Nazev")
    if kod is None or not nazev:
        logger.debug(
            "heslar.ruian_sync.vfr_parser._parse_okres_dto.skip_incomplete",
            extra={"kod": kod, "nazev": nazev},
        )
        return None
    vusc_kod = _nested_int(elem, "Vusc", "Kod") or 0
    db_wkt = _extract_definicni_bod(elem)
    hr_wkt = _extract_hranice(elem)
    return RuianOkresDTO(
        kod=kod,
        nazev=nazev,
        kraj_kod=vusc_kod,
        nazev_en=None,
        spz="",  # VFR neposkytuje
        definicni_bod_wkt=db_wkt,
        hranice_wkt=hr_wkt,
    )


def _parse_katastr_dto(elem, *, obec_okres_map: dict) -> Optional[RuianKatastrDTO]:
    """
    Vytvoří :class:`RuianKatastrDTO` z elementu ``KatastralniUzemi``.

    Okres se dohledá přes obec (``KatastralniUzemi/Obec/Kod →
    obec_okres_map[obec_kod]``). Pokud obec není v mapě (např. ve změnovém
    souboru, kde je jen KÚ ale ne obec), DTO se nevrátí (``None``) a
    syncer si okres dohledá z DB.

    Vrací ``None`` pokud:

    * prvek je historický (vyplněné ``PlatiDo``),
    * chybí povinný ``Kod`` nebo ``Nazev``.

    :param elem: lxml element ``vf:KatastralniUzemi``.
    :param obec_okres_map: Mapa kódů obcí na kódy okresů.

        :return: DTO nebo ``None``.
    """
    if _is_historical(elem):
        return None
    kod = _first_text_int(elem, "Kod")
    nazev = _first_text(elem, "Nazev")
    if kod is None or not nazev:
        logger.debug(
            "heslar.ruian_sync.vfr_parser._parse_katastr_dto.skip_incomplete",
            extra={"kod": kod, "nazev": nazev},
        )
        return None
    obec_kod = _nested_int(elem, "Obec", "Kod")
    okres_kod = obec_okres_map.get(obec_kod) if obec_kod is not None else None
    if okres_kod is None:
        # Ve změnovém režimu může okres chybět – syncer si ho dohledá z DB.
        # Označíme to placeholder hodnotou 0 a syncer rozhodne.
        okres_kod = 0
    db_wkt = _extract_definicni_bod(elem)
    hr_wkt = _extract_hranice(elem)
    return RuianKatastrDTO(
        kod=kod,
        nazev=nazev,
        okres_kod=okres_kod,
        definicni_bod_wkt=db_wkt,
        hranice_wkt=hr_wkt,
    )


def _parse_zanikly_prvek(elem) -> Optional[RuianChangeEvent]:
    """
    Mapuje element ``ZaniklyPrvek`` na :class:`RuianChangeEvent` typu DELETE.

    Mapování ``TypPrvkuKod`` → úroveň::

        VC → kraj      (VÚSC)
        OK → okres
        KU → katastr   (Katastrální území)

    Hodnoty pochází z číselníku ``CS_TYP_PRVKU`` (ruian.cuzk.cz). Jiné typy
    (obec, ZSJ, …) ignorujeme – #372 je nesynchronizuje.

    :param elem: lxml element ``vf:ZaniklyPrvek``.

        :return: Event, nebo ``None`` pokud typ prvku není kraj/okres/katastr.
    """
    typ_kod = (_first_text(elem, "TypPrvkuKod") or "").strip().upper()
    prvek_id = _first_text_int(elem, "PrvekId")
    if prvek_id is None:
        return None

    mapping = {"VC": LEVEL_KRAJ, "OK": LEVEL_OKRES, "KU": LEVEL_KATASTR}
    level = mapping.get(typ_kod)
    if level is None:
        return None
    return RuianChangeEvent(level=level, event_type=EVENT_DELETE, kod=prvek_id, payload=None)


# ---------------------------------------------------------------------------
# Pomocné extraktory hodnot
# ---------------------------------------------------------------------------


def _first_text(elem, local_name: str) -> Optional[str]:
    """
    Vrátí text prvního descendantu se zadaným local-name.

    :param elem: lxml element.
    :param local_name: Local-name hledaného dítěte.

        :return: Text (stripped) nebo ``None``.
    """
    for child in elem.iter():
        if etree.QName(child.tag).localname == local_name:
            return (child.text or "").strip() or None
    return None


def _first_text_int(elem, local_name: str) -> Optional[int]:
    """
    Vrátí int hodnotu prvního descendantu se zadaným local-name.

    :param elem: lxml element.
    :param local_name: Local-name dítěte.

        :return: ``int`` nebo ``None``.
    """
    txt = _first_text(elem, local_name)
    if txt is None:
        return None
    try:
        return int(txt)
    except ValueError:
        return None


def _nested_int(elem, parent_local: str, child_local: str) -> Optional[int]:
    """
    Vrátí int z konkrétní dvojúrovňové cesty ``elem//<parent>//<child>``.

    Bere první nález – předpokládá, že struktura VFR má jen jednu vazbu
    daného typu (např. ``Okres/Vusc/Kod`` na okresu existuje přesně 1×).

    :param elem: Kořenový element.
    :param parent_local: Local-name rodiče.
    :param child_local: Local-name dítěte uvnitř rodiče.

        :return: ``int`` nebo ``None``.
    """
    for parent in elem.iter():
        if etree.QName(parent.tag).localname != parent_local:
            continue
        for child in parent.iter():
            if etree.QName(child.tag).localname == child_local:
                txt = (child.text or "").strip()
                try:
                    return int(txt)
                except ValueError:
                    return None
    return None


# ---------------------------------------------------------------------------
# Geometrie
# ---------------------------------------------------------------------------


def _extract_definicni_bod(elem) -> Optional[str]:
    """
    Najde a převede ``Geometrie/DefinicniBod`` na WKT POINT v EPSG:4326.

    VFR poskytuje ``gml:MultiPoint``; pro naši DB s ``PointField`` použijeme
    první ``gml:Point`` v kolekci.

    :param elem: Kořenový element prvku (Vusc/Okres/KatastralniUzemi).

        :return: WKT POINT nebo ``None``.
    """
    pos_text = None
    for descendant in elem.iter():
        local = etree.QName(descendant.tag).localname
        if local == "pos":
            pos_text = (descendant.text or "").strip()
            break  # první gml:pos vyhraje
    if not pos_text:
        return None
    coords = pos_text.split()
    if len(coords) < 2:
        return None
    try:
        x = float(coords[0])
        y = float(coords[1])
    except ValueError:
        return None
    wkt_5514 = f"POINT({x} {y})"
    return _to_wgs84(wkt_5514)


#: AMČR potřebuje vždy originální hranice. Pokud ``OriginalniHranice``
#: v elementu chybí, vrací ``_extract_hranice`` ``None`` – generalizovaná
#: hranice se záměrně nenačítá.
_HRANICE_PREFERENCE = ("OriginalniHranice",)


def _extract_hranice(elem) -> Optional[str]:
    """
    Najde a převede ``Geometrie/OriginalniHranice`` na WKT MULTIPOLYGON v EPSG:4326.

    Pokud ``OriginalniHranice`` v elementu chybí, vrátí ``None``.
    Generalizované hranice se záměrně nenačítají.

    :param elem: Kořenový element prvku.

        :return: WKT MULTIPOLYGON nebo ``None``.
    """
    for hranice_name in _HRANICE_PREFERENCE:
        for descendant in elem.iter():
            if etree.QName(descendant.tag).localname == hranice_name:
                wkt_5514 = _gml_multisurface_to_wkt(descendant)
                if wkt_5514:
                    return _to_wgs84(wkt_5514)
    return None


def _gml_multisurface_to_wkt(hranice_elem) -> Optional[str]:
    """
    Převede ``gml:MultiSurface`` (nebo ``gml:MultiPolygon``) na WKT MULTIPOLYGON.

    Iteruje ``gml:Polygon`` (nebo ``gml:Surface``); každý polygon má
    exteriér (``gml:exterior/gml:LinearRing/gml:posList``) a 0..N
    interiérů (otvorů). WKT pro MULTIPOLYGON má syntaxi
    ``MULTIPOLYGON(((x y, x y, ...), (x y, ...)), ((...)))``.

    :param hranice_elem: Element ``OriginalniHranice``.

        :return: WKT řetězec nebo ``None``.
    """
    polygons_wkt = []
    for poly in hranice_elem.iter():
        if etree.QName(poly.tag).localname not in ("Polygon", "Surface"):
            continue
        rings = []
        for ring_role in ("exterior", "interior"):
            for role_elem in poly.iter():
                if etree.QName(role_elem.tag).localname != ring_role:
                    continue
                pos_list = None
                for ring_child in role_elem.iter():
                    if etree.QName(ring_child.tag).localname == "posList":
                        pos_list = (ring_child.text or "").strip()
                        break
                if pos_list:
                    coords = _coords_from_poslist(pos_list)
                    if coords:
                        rings.append(coords)
        if rings:
            ring_strs = ["(" + ", ".join(f"{x} {y}" for x, y in r) + ")" for r in rings]
            polygons_wkt.append("(" + ", ".join(ring_strs) + ")")

    if not polygons_wkt:
        return None
    return "MULTIPOLYGON(" + ", ".join(polygons_wkt) + ")"


def _coords_from_poslist(pos_list: str):
    """
    Naparsuje ``gml:posList`` (whitespace-separated čísla) na seznam dvojic.

    GML 3.2.1 ``posList`` může mít formát ``x1 y1 x2 y2 ...``. Pokud poslední
    bod prstenu není totožný s prvním (nezavřený LinearRing), funkce ho
    automaticky doplní – WKT a OGC standardy zavření vyžadují a některé
    VFR soubory ho explicitně neuvádějí.

    :param pos_list: Textový obsah ``gml:posList``.

        :return: Seznam ``[(x, y), …]`` se zaručeným ``out[0] == out[-1]`` při
            ≥3 bodech, nebo prázdný seznam při neparsovatelném vstupu.
    """
    nums = pos_list.split()
    if len(nums) % 2 != 0:
        return []
    out = []
    for i in range(0, len(nums), 2):
        try:
            out.append((float(nums[i]), float(nums[i + 1])))
        except ValueError:
            return []
    # Zajistit uzavření prstenu: pokud poslední bod není identický s prvním,
    # přidej kopii prvního na konec. Ošetřuje GML produkce, které neuzavírají
    # explicitně, i občasné float-rounding artefakty.
    if len(out) >= 3 and out[0] != out[-1]:
        out.append(out[0])
    return out


# ---------------------------------------------------------------------------
# CRS transformace 5514 → 4326
# ---------------------------------------------------------------------------


# Range pro detekci znaménka S-JTSK (z core/coordTransform.py:69):
# záporné Y v rozmezí -905000 .. -400000, X v rozmezí -1230000 .. -930000.
_SJTSK_NEGATIVE_Y_RANGE = (-905000, -400000)
_SJTSK_NEGATIVE_X_RANGE = (-1230000, -930000)


def _to_wgs84(wkt_5514: str) -> str:
    """
    Převede WKT v EPSG:5514 na WKT v EPSG:4326 přes ``core.coordTransform``.

    ``core.coordTransform.convertToWGS84`` očekává **záporná** Y/X
    (rozsah -905000..-400000 resp. -1230000..-930000). VFR soubory mohou
    obsahovat S-JTSK v kladné formě (standardní EPSG:5514). Helper
    detekuje sign podle prvních souřadnic a podle potřeby invertuje
    znaménka v celém WKT řetězci před voláním transformace.

    :param wkt_5514: WKT v EPSG:5514 (kladný nebo záporný S-JTSK).

        :return: WKT v EPSG:4326 (longitude latitude).
    """
    sample_x, sample_y = _sample_xy(wkt_5514)
    needs_negation = sample_x is not None and sample_x > 0 and sample_y is not None and sample_y > 0
    if needs_negation:
        wkt_to_transform = _negate_coords(wkt_5514)
    else:
        wkt_to_transform = wkt_5514
    transformed = transform_geom_to_wgs84(wkt_to_transform)
    if isinstance(transformed, tuple):
        # transform_geom vrací (geom, status); pro nás stačí WKT
        return transformed[0]
    return transformed


def _sample_xy(wkt: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Vyzvedne první dvojici souřadnic (x, y) z WKT řetězce pro detekci znaménka.

    :param wkt: WKT řetězec.

        :return: ``(x, y)`` nebo ``(None, None)`` při neúspěchu.
    """
    match = re.search(r"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)", wkt)
    if not match:
        return None, None
    try:
        return float(match.group(1)), float(match.group(2))
    except ValueError:
        return None, None


def _negate_coords(wkt: str) -> str:
    """
    Invertuje znaménka u všech čísel ve WKT řetězci.

    Záměrně jednoduché – WKT obsahuje čísla pouze v souřadnicích, ne
    v klíčových slovech.

    :param wkt: Vstupní WKT.

        :return: WKT se všemi čísly s opačným znaménkem.
    """

    def _flip(match):
        s = match.group(0)
        if s.startswith("-"):
            return s[1:]
        return "-" + s

    return re.sub(r"-?\d+(?:\.\d+)?", _flip, wkt)


# ---------------------------------------------------------------------------
# Re-export
# ---------------------------------------------------------------------------


__all__ = [
    "parse_changes",
    "RuianMissingMandatoryFieldError",
]
