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
* geometrie zůstává v EPSG:5514 (RÚIAN heslář je od migrace 0013 primárně
  JTSK) — parser jen normalizuje případné záporné S-JTSK z VFR na kladnou
  East-North konvenci přes :func:`_normalize_sjtsk_wkt`;
* okres katastru se rezolvuje přes přechodný map ``obec_kod → okres_kod``
  z téhož souboru; pokud obec ve změnovém souboru chybí, syncer dohledá
  okres z DB.

Parser čte výhradně variantu **ZKSH** (denní změnový + originální hranice
katastrů). Jiné varianty (``ZKSG`` generalizované, ``ZZSZ`` bez polygonů)
nejsou potřeba – AMČR potřebuje pouze originální hranice.

Bezpečnostní poznámky – změnový soubor se stahuje automaticky z internetu,
takže je z pohledu aplikace **nedůvěryhodný vstup**:

* ``resolve_entities=False`` blokuje XXE i „billion laughs";
* ``huge_tree`` zůstává vypnuté, aby platily pojistky libxml2 na hloubku
  stromu a délku jmen a textových uzlů;
* velikost rozbaleného obsahu je omezená (:data:`_MAX_UNPACKED_BYTES`,
  :data:`_MAX_COMPRESSION_RATIO`) proti dekompresní bombě, a limit se vynucuje
  i při čtení, protože hlavička ZIPu je pod kontrolou útočníka;
* geometrie se parsuje **výhradně vlastním kódem**; GML se nepředává do GDALu,
  aby se podvrženým souborem nedal oslovit parser v rozsáhlé C/C++ knihovně
  (viz :data:`_FOREIGN_CURVED_LOCALNAMES`).
"""

from __future__ import annotations

import logging
import math
import re
import zipfile
from pathlib import Path
from typing import Iterator, Optional, Tuple

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
    Vyhozeno, pokud je v DB potřeba uložit nový kraj/okres, ale zdroj
    neposkytuje povinné pole (``rada_id`` u kraje, ``spz`` u okresu).

    Ta pole v RÚIAN neexistují – jsou vlastní AMČR a historicky se plnila
    ručně. Prázdný řetězec se do ``NOT NULL`` sloupce záměrně nezapisuje
    (u ``spz`` je navíc ``unique``, takže by stejně prošel nejvýš jednou).

    Volající (syncer) zachytí, zaloguje a označí ``RuianSyncRun.status="failed"``.
    """

    def __init__(self, level: str, kod: int, missing: list):
        """
        :param level: Úroveň prvku (``"kraj"`` / ``"okres"``).
        :param kod: Kód prvku.
        :param missing: Seznam názvů chybějících polí.
        """
        super().__init__(
            f"Nový {level} kód={kod} – chybí povinná pole: {', '.join(missing)}. "
            f"Hodnotu je nutné doplnit zásahem do DB nebo přes shell a sync spustit znovu; "
            f"administrace RÚIAN heslářů je pro tato pole read-only."
        )
        self.level = level
        self.kod = kod
        self.missing = missing


#: Strop na velikost XML rozbaleného z jedné denní delty. Reálné soubory ČÚZK
#: se pohybují v jednotkách až desítkách MB (naměřeno: stavový ``ST_UZSZ``
#: 4,5 MB komprimovaně → 48,7 MB rozbaleno), takže 1 GiB je ~20× nad největším
#: reálným vstupem a přitom spolehlivě zastaví dekompresní bombu.
_MAX_UNPACKED_BYTES = 1024 * 1024 * 1024

#: Strop na poměr rozbalené/komprimované velikosti. Naměřené reálné hodnoty:
#: 2,4× (SHP archiv) a 10,8× (VFR XML). Bomby mívají poměr v tisících, takže
#: 100× je bezpečně nad legitimním provozem.
_MAX_COMPRESSION_RATIO = 100.0


class RuianDecompressionBombError(Exception):
    """
    Vyhozeno, pokud stažený archiv vypadá jako dekompresní bomba – rozbalený
    obsah překračuje :data:`_MAX_UNPACKED_BYTES` nebo poměr komprese
    :data:`_MAX_COMPRESSION_RATIO`.

    Kontrola má dvě fáze, protože hlavička ZIPu je pod kontrolou útočníka:
    nejdřív se ověří deklarované velikosti z centrálního adresáře, pak se limit
    **znovu vynucuje při čtení** streamu (:class:`_LimitedReader`) – archiv,
    který v hlavičce lže, se zastaví až na skutečně přečtených bajtech.

    Volající (syncer) zachytí, zaloguje a označí ``RuianSyncRun.status="failed"``.
    """

    def __init__(self, duvod: str, *, path=None):
        """
        :param duvod: Lidsky čitelný popis, který limit byl překročen.
        :param path: Cesta k archivu, kterého se nález týká.
        """
        super().__init__(f"Podezření na dekompresní bombu ({path}): {duvod}")
        self.duvod = duvod
        self.path = path


class _LimitedReader:
    """
    Obal nad file-like objektem, který zastaví čtení po překročení limitu.

    Existuje proto, že ``ZipInfo.file_size`` pochází z centrálního adresáře
    archivu, tedy z dat, která může útočník libovolně podvrhnout. Kontrola
    hlavičky sama o sobě proto nestačí – tenhle obal počítá **skutečně
    přečtené** bajty a po překročení limitu vyhodí
    :class:`RuianDecompressionBombError`.

    :param stream: Podkladový binární stream.
    :param limit: Maximální počet bajtů, které smí být celkem přečteny.
    :param path: Cesta k archivu (jen pro chybovou hlášku).
    """

    def __init__(self, stream, limit: int, *, path=None):
        self._stream = stream
        self._limit = limit
        self._path = path
        self._read_total = 0

    def read(self, size=-1):
        """
        Přečte data z podkladového streamu a započítá je do limitu.

        :param size: Počet bajtů k přečtení; ``-1`` znamená vše.

            :return: Přečtené bajty.
            :raises RuianDecompressionBombError: Při překročení limitu.
        """
        chunk = self._stream.read(size)
        self._read_total += len(chunk)
        if self._read_total > self._limit:
            raise RuianDecompressionBombError(
                f"rozbalený obsah překročil {self._limit} B " f"(přečteno nejméně {self._read_total} B)",
                path=self._path,
            )
        return chunk

    def close(self):
        """Zavře podkladový stream."""
        return self._stream.close()


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
        xml_infos = [i for i in zf.infolist() if i.filename.lower().endswith(".xml")]
        if not xml_infos:
            zf.close()
            raise ValueError(f"VFR ZIP neobsahuje žádný .xml soubor: {p}")
        info = xml_infos[0]
        try:
            _check_zip_header(info, path=p)
        except RuianDecompressionBombError:
            zf.close()
            raise
        stream = zf.open(info)
        _orig_close = stream.close

        def _close_both():
            _orig_close()
            zf.close()

        stream.close = _close_both
        return _LimitedReader(stream, _MAX_UNPACKED_BYTES, path=p)
    return _LimitedReader(open(str(p), "rb"), _MAX_UNPACKED_BYTES, path=p)


def _check_zip_header(info: zipfile.ZipInfo, *, path) -> None:
    """
    Ověří deklarované velikosti členu archivu proti limitům dekompresní bomby.

    Jde jen o **první** fázi kontroly – hodnoty pocházejí z centrálního
    adresáře ZIPu, který útočník ovládá. Skutečné vynucení limitu dělá
    :class:`_LimitedReader` při čtení.

    :param info: Záznam členu archivu.
    :param path: Cesta k archivu (jen pro chybovou hlášku).
    :raises RuianDecompressionBombError: Při překročení některého z limitů.
    """
    if info.file_size > _MAX_UNPACKED_BYTES:
        raise RuianDecompressionBombError(
            f"člen {info.filename!r} deklaruje {info.file_size} B rozbalených, " f"limit je {_MAX_UNPACKED_BYTES} B",
            path=path,
        )
    if info.compress_size > 0:
        ratio = info.file_size / info.compress_size
        if ratio > _MAX_COMPRESSION_RATIO:
            raise RuianDecompressionBombError(
                f"člen {info.filename!r} má poměr komprese {ratio:.1f}x, " f"limit je {_MAX_COMPRESSION_RATIO:.0f}x",
                path=path,
            )


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

    Paměť se uvolňuje u **všech** záznamů nejvyšší úrovně, nejen u těch
    sledovaných. Denní ZKSH obsahuje řádově tisíce ``Parcela`` /
    ``StavebniObjekt`` / ``AdresniMisto``, které nás nezajímají – bez jejich
    zahazování by strom rostl po celou dobu parsování a tvrzení o konstantní
    paměti by neplatilo (naměřeno +40 MB na jeden soubor).

    Uklízet lze jen záznamy nejvyšší úrovně (vnuky kořene, tj. přímé potomky
    kolekcí jako ``Parcely``/``StavebniObjekty``). Hlouběji leží potomci
    sledovaných prvků – ``Kod``, ``Nazev``, ``Geometrie`` – a jejich ``end``
    událost přichází **dřív** než u rodiče, takže jejich vyprázdnění by
    zničilo data, která extraktory teprve potřebují.

    Vyieldovaný element se zde nevyprazdňuje; to dělá volající
    (:func:`parse_changes`) až po vytvoření DTO.

    :param path: Cesta k VFR souboru.
    :param local_names: Tuple local-names (bez namespace prefixu) k matchnutí.

        :return: Generátor lxml elementů.
    """
    target_set = set(local_names)
    stream = _open_xml_stream(path)
    try:
        # huge_tree=False (default) ponechává zapnuté pojistky libxml2 na hloubku
        # stromu a délku jmen/textových uzlů. Denní delty jsou malé (jednotky MB
        # komprimovaně, desítky MB rozbalené), takže je nepotřebují – a část
        # historických přetečení v libxml2 byla dosažitelná právě jen s vypnutými
        # limity. resolve_entities=False blokuje XXE i „billion laughs".
        # Obojí je bezpečnostní nastavení, neměnit bez rozmyslu.
        ctx = etree.iterparse(stream, events=("end",), resolve_entities=False)
        for _, elem in ctx:
            parent = elem.getparent()
            if parent is None:
                continue

            local = etree.QName(elem.tag).localname
            je_target = False
            if local in target_set:
                allowed = _TARGET_PARENTS.get(local)
                # Reference uvnitř jiného prvku (např. Parcela/KatastralniUzemi)
                # mají jiného rodiče než definice a nesmí se yieldovat.
                je_target = allowed is None or etree.QName(parent.tag).localname in allowed

            if je_target:
                yield elem
            else:
                # Záznam nejvyšší úrovně = vnuk kořene. Cokoli hlubšího je
                # potomek nějakého záznamu a uklidit se nesmí.
                grandparent = parent.getparent()
                if grandparent is None or grandparent.getparent() is not None:
                    continue
                elem.clear()

            # Zahození předchozích sourozenců – drží paměť na uzdě bez ohledu
            # na to, kolik záznamů v kolekci ještě přijde.
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
        # VFR rada_id neposkytuje. U existujícího kraje ho syncer ignoruje,
        # u nového vyhodí RuianMissingMandatoryFieldError (doplňuje se ručně).
        rada_id="",
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
        # VFR spz neposkytuje – stejný režim jako rada_id u kraje.
        spz="",
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
    return _normalize_sjtsk_wkt(wkt_5514)


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
                    return _normalize_sjtsk_wkt(wkt_5514)
    return None


#: Krok linearizace kruhových oblouků ve stupních, viz :func:`_linearize_arc`.
#:
#: Hodnota odpovídá densifikaci, kterou používá ČÚZK při exportu týchž hranic
#: do SHP.
#:
#: Držet stejný krok jako ČÚZK je podstatné: katastr aktualizovaný z VFR pak
#: lícuje se sousedem, který zůstal z plného syncu ze SHP, a nevznikají mezi
#: nimi překryvy.
_ARC_STEP_DEGREES = 6.0

#: Zakřivené GML elementy, které umí zpracovat vlastní kód
#: (:func:`_linearize_arcstring`). ``posList`` u nich nejsou lomové body, ale
#: řídicí body oblouků.
_NATIVE_CURVED_LOCALNAMES = frozenset({"Arc", "ArcString"})

#: Zakřivené GML elementy, které vlastní kód **neumí**. Ve zpracovávaných
#: prvcích (kraj/okres/katastr) se dosud neobjevily; ``Circle`` se vyskytuje
#: jen u ``Parcela``, kterou nesyncujeme.
#:
#: Dřív se geometrie s těmito typy delegovala na GDAL
#: (``ogr.CreateGeometryFromGML``). To ale znamenalo, že podvržený denní soubor
#: mohl jedním elementem dostat vlastní data do parseru GML v GDALu – tedy do
#: rozsáhlé C/C++ knihovny – po cestě, kterou reálná data ČÚZK nikdy nevyužijí.
#: Proto se prvek nově **odmítne** a zaloguje jako ERROR; stávající geometrie
#: v DB zůstane beze změny a operátor se o novém typu dozví z logu místo
#: tichého fallbacku. Viz :func:`_gml_multisurface_to_wkt`.
_FOREIGN_CURVED_LOCALNAMES = frozenset(
    {
        "ArcByCenterPoint",
        "ArcByBulge",
        "ArcStringByBulge",
        "Circle",
        "CircleByCenterPoint",
        "CubicSpline",
        "Bezier",
        "BSpline",
        "Clothoid",
        "OffsetCurve",
        "CompositeCurve",
    }
)

#: Elementy nesoucí ``posList`` jednoho úseku prstenu. ``LinearRing`` je celý
#: prsten jedním kusem, ostatní jsou dílčí segmenty uvnitř ``Ring``.
_SEGMENT_LOCALNAMES = frozenset(
    {
        "LinearRing",
        "LineString",
        "LineStringSegment",
        "Arc",
        "ArcString",
    }
)


def _first_foreign_curve(hranice_elem) -> Optional[str]:
    """
    Najde první zakřivený typ v podstromu, který vlastní kód neumí.

    Vrací přímo název typu (ne jen ``True``), aby jej volající mohl zalogovat –
    operátor tak z logu pozná, který nový GML typ ČÚZK zavedlo.

    :param hranice_elem: Element ``OriginalniHranice``.

        :return: Local-name nepodporovaného typu, nebo ``None`` když podstrom
            obsahuje jen typy, které vlastní kód zvládne.
    """
    for descendant in hranice_elem.iter():
        local = etree.QName(descendant.tag).localname
        if local in _FOREIGN_CURVED_LOCALNAMES:
            return local
    return None


def _circle_from_3points(p1, p2, p3):
    """
    Spočítá střed a poloměr kružnice procházející třemi body.

    :param p1: První bod ``(x, y)``.
    :param p2: Prostřední bod ``(x, y)``.
    :param p3: Koncový bod ``(x, y)``.

        :return: Dvojice ``((cx, cy), r)``, nebo ``(None, None)`` pokud jsou
            body kolineární (kružnice neexistuje).
    """
    ax, ay = p1
    bx, by = p2
    cx, cy = p3
    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:
        return None, None
    a2 = ax * ax + ay * ay
    b2 = bx * bx + by * by
    c2 = cx * cx + cy * cy
    ux = (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by)) / d
    uy = (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)) / d
    return (ux, uy), math.hypot(ax - ux, ay - uy)


def _linearize_arc(p1, p2, p3):
    """
    Proloží jeden kruhový oblouk úsečkami stejně, jak to dělá ČÚZK v SHP.

    Oblouk je v GML dán třemi body (počátek, bod na oblouku, konec). Pravidlo
    densifikace bylo zpětně odvozeno porovnáním VFR a SHP téhož katastru:
    počet úseček je ``ceil(úhel_oblouku_ve_stupních / _ARC_STEP_DEGREES)``
    a oblouk se dělí na **rovnoměrné úhlové kroky**. Na katastru Hřibsko dává
    tento postup shodný počet vrcholů jako SHP (38) a maximální odchylku
    0,013 mm; GDAL ``GetLinearGeometry`` dělí jinak (o vrchol víc) a zůstávaly
    po něm vlásečnicové překryvy se sousedy.

    Krajní body se přebírají **přesně** ze vstupu, aby navazující segment
    prstenu bez mezery lícoval (dopočtená hodnota by se lišila o float šum).

    :param p1: Počátek oblouku ``(x, y)``.
    :param p2: Bod na oblouku mezi ``p1`` a ``p3``.
    :param p3: Konec oblouku ``(x, y)``.

        :return: Seznam bodů ``[(x, y), …]`` včetně obou krajních; při
            kolineárních bodech ``[p1, p2, p3]`` (úsečka).
    """
    center, radius = _circle_from_3points(p1, p2, p3)
    if center is None:
        return [p1, p2, p3]

    def angle(pt):
        return math.atan2(pt[1] - center[1], pt[0] - center[0])

    def normalize(a):
        while a <= -math.pi:
            a += 2 * math.pi
        while a > math.pi:
            a -= 2 * math.pi
        return a

    a1 = angle(p1)
    # Směr oběhu určuje poloha prostředního bodu: pokud leží na kratší cestě
    # proti směru hodinových ručiček, jdeme tudy, jinak opačně.
    sweep_ccw = normalize(angle(p3) - a1) % (2 * math.pi)
    mid_ccw = normalize(angle(p2) - a1) % (2 * math.pi)
    if mid_ccw <= sweep_ccw:
        total, direction = sweep_ccw, 1.0
    else:
        total, direction = 2 * math.pi - sweep_ccw, -1.0

    steps = max(1, math.ceil(math.degrees(total) / _ARC_STEP_DEGREES))
    out = [p1]
    for i in range(1, steps):
        a = a1 + direction * total * i / steps
        out.append((center[0] + radius * math.cos(a), center[1] + radius * math.sin(a)))
    out.append(p3)
    return out


def _linearize_arcstring(control_points):
    """
    Proloží ``gml:ArcString`` (nebo ``gml:Arc``) úsečkami.

    ``ArcString`` je posloupnost oblouků se sdílenými koncovými body – body
    1-2-3 tvoří první oblouk, 3-4-5 druhý atd. Počet bodů je proto vždy
    lichý (``2n+1`` pro ``n`` oblouků).

    :param control_points: Řídicí body ``[(x, y), …]`` z ``gml:posList``.

        :return: Seznam bodů lomené čáry, nebo prázdný seznam při neplatném
            počtu řídicích bodů.
    """
    if len(control_points) < 3 or len(control_points) % 2 == 0:
        logger.warning(
            "heslar.ruian_sync.vfr_parser._linearize_arcstring.invalid_point_count",
            extra={"point_count": len(control_points)},
        )
        return []
    out = []
    for i in range(0, len(control_points) - 2, 2):
        seg = _linearize_arc(control_points[i], control_points[i + 1], control_points[i + 2])
        out.extend(seg if not out else seg[1:])
    return out


def _ring_coords(role_elem):
    """
    Sestaví souřadnice jednoho prstenu z jeho segmentů.

    Prsten může být zadaný dvěma způsoby (oba se ve VFR vyskytují):

    * ``gml:LinearRing`` s jedním ``posList`` – celý prsten jedním kusem;
    * ``gml:Ring`` s několika ``gml:curveMember``, kde každý nese
      ``gml:LineString`` (lomená čára) nebo ``gml:Curve/segments`` s
      ``gml:ArcString`` (kruhové oblouky).

    Segmenty se procházejí v pořadí dokumentu a spojují; sdílený bod na
    spoji se nezdvojuje. Oblouky projdou linearizací
    (:func:`_linearize_arcstring`), lomené čáry se berou tak, jak jsou.
    Na konci se prsten uzavře, pokud poslední bod není totožný s prvním.

    :param role_elem: Element ``gml:exterior`` nebo ``gml:interior``.

        :return: Seznam bodů ``[(x, y), …]`` uzavřeného prstenu, nebo
            prázdný seznam.
    """
    coords = []
    for prim in role_elem.iter():
        local = etree.QName(prim.tag).localname
        if local not in _SEGMENT_LOCALNAMES:
            continue
        pos_text = None
        for child in prim.iter():
            if etree.QName(child.tag).localname == "posList":
                pos_text = (child.text or "").strip()
                break
        if not pos_text:
            continue
        pts = _coords_from_poslist(pos_text, close_ring=False)
        if not pts:
            continue
        if local in _NATIVE_CURVED_LOCALNAMES:
            pts = _linearize_arcstring(pts)
            if not pts:
                continue
        if coords and coords[-1] == pts[0]:
            coords.extend(pts[1:])
        else:
            coords.extend(pts)
    if len(coords) >= 3 and coords[0] != coords[-1]:
        coords.append(coords[0])
    return coords


def _gml_multisurface_to_wkt(hranice_elem) -> Optional[str]:
    """
    Převede ``gml:MultiSurface`` (nebo ``gml:MultiPolygon``) na WKT MULTIPOLYGON.

    Iteruje ``gml:Polygon`` (nebo ``gml:Surface``); každý polygon má exteriér
    a 0..N interiérů (otvorů), jejichž souřadnice sestaví :func:`_ring_coords`
    – ta zvládne i prsteny složené z několika segmentů včetně kruhových
    oblouků. WKT pro MULTIPOLYGON má syntaxi
    ``MULTIPOLYGON(((x y, x y, ...), (x y, ...)), ((...)))``.

    Obsahuje-li geometrie zakřivený typ, který vlastní kód neumí
    (:data:`_FOREIGN_CURVED_LOCALNAMES`), prvek se **odmítne** – vrátí se
    ``None``, volající ponechá stávající geometrii v DB beze změny a událost
    se zaloguje jako ERROR. Tyto typy se v kraji/okrese/katastru nikdy
    nevyskytly; odmítnutí je bezpečnější než je posílat do parseru GML
    v GDALu (viz komentář u :data:`_FOREIGN_CURVED_LOCALNAMES`).

    :param hranice_elem: Element ``OriginalniHranice``.

        :return: WKT řetězec nebo ``None``.
    """
    foreign = _first_foreign_curve(hranice_elem)
    if foreign is not None:
        logger.error(
            "heslar.ruian_sync.vfr_parser._gml_multisurface_to_wkt.nepodporovana_krivka",
            extra={"typ": foreign},
        )
        return None

    polygons_wkt = []
    for poly in hranice_elem.iter():
        if etree.QName(poly.tag).localname not in ("Polygon", "Surface"):
            continue
        rings = []
        for ring_role in ("exterior", "interior"):
            for role_elem in poly.iter():
                if etree.QName(role_elem.tag).localname != ring_role:
                    continue
                segment_coords = _ring_coords(role_elem)
                if segment_coords:
                    rings.append(segment_coords)
        if rings:
            ring_strs = ["(" + ", ".join(f"{x} {y}" for x, y in r) + ")" for r in rings]
            polygons_wkt.append("(" + ", ".join(ring_strs) + ")")

    if not polygons_wkt:
        return None
    return "MULTIPOLYGON(" + ", ".join(polygons_wkt) + ")"


def _coords_from_poslist(pos_list: str, *, close_ring: bool = True):
    """
    Naparsuje ``gml:posList`` (whitespace-separated čísla) na seznam dvojic.

    GML 3.2.1 ``posList`` má formát ``x1 y1 x2 y2 ...``.

    :param pos_list: Textový obsah ``gml:posList``.
    :param close_ring: Pokud ``True`` (default), automaticky doplní kopii
        prvního bodu na konec, pokud nejsou totožné (uzavření LinearRing dle
        OGC/WKT). Při ``False`` se vrátí čisté souřadnice – používá volající,
        který skládá prsten z několika ``posList`` segmentů (viz
        :func:`_gml_multisurface_to_wkt` pro Ring/curveMember/LineString).

        :return: Seznam ``[(x, y), …]``. Při ``close_ring=True`` a ≥3 bodech
            je zaručeno ``out[0] == out[-1]``. Prázdný seznam při
            neparsovatelném vstupu.
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
    if close_ring and len(out) >= 3 and out[0] != out[-1]:
        out.append(out[0])
    return out


# ---------------------------------------------------------------------------
# Normalizace znaménka S-JTSK (VFR ↔ PostGIS EPSG:5514 East-North)
# ---------------------------------------------------------------------------


def _normalize_sjtsk_wkt(wkt_5514: str) -> str:
    """
    Normalizuje WKT v EPSG:5514 do **záporné** (West-South) konvence,
    kterou používá zbytek projektu (``pian.geom_sjtsk``, ``adb.geom``
    a ``ruian_katastr.hranice`` po migraci 0013).

    Konvence projektu:

    * ``core.coordTransform.convertToJTSK`` vrací ``[-Y, -X]`` (záporné).
    * Všechna 5514 data v DB jsou v této konvenci uložena.
    * PostGIS ``ST_Intersects`` funguje matematicky správně dokud jsou obě
      strany ve stejné konvenci (neinterpretuje osy — porovnává souřadnice).

    VFR z ČÚZK může dodávat kladné (standardní EPSG:5514 East-North)
    i záporné souřadnice. Helper detekuje znaménko podle první dvojice
    a v případě **kladných** hodnot invertuje znaménka v celém WKT řetězci.

    :param wkt_5514: WKT v EPSG:5514 (kladný nebo záporný S-JTSK).

        :return: WKT v EPSG:5514 v záporné konvenci projektu.
    """
    sample_x, sample_y = _sample_xy(wkt_5514)
    if sample_x is not None and sample_x > 0 and sample_y is not None and sample_y > 0:
        return _negate_coords(wkt_5514)
    return wkt_5514


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
    "RuianDecompressionBombError",
]
