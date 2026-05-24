"""
Importér RÚIAN dat ze SHP polygonů + VFR `ST_UZSZ` definičních bodů.

Tato implementace :class:`RuianSource` používá kombinaci dvou autoritativních
zdrojů ČÚZK pro počáteční (případně manuální) plný sync:

* **SHP `1.zip`** (``https://services.cuzk.gov.cz/shp/stat/epsg-5514/1.zip``,
  ~241 MB) – obsahuje polygony všech úrovní (VUSC_P, OKRESY_P, OBCE_P,
  KATUZE_P) v EPSG:5514.
* **VFR `ST_UZSZ.xml.zip`** (~4.5 MB) – základní datová sada pro celou ČR
  s autoritativními definičními body (kraj/okres/obec/KÚ).

Kombinace pokrývá data, která zachycuje současný stav DB a co aplikace
potřebuje pro spatial intersect (`core/utils.py`) i UI markery, **bez nutnosti
stahovat 6258 per-obec VFR souborů**.

Polygony i body jsou v EPSG:5514 (S-JTSK Krovak East-North); modul je
převádí do EPSG:4326 přes existující :mod:`core.coordTransform` (stejně jako
:mod:`vfr_parser`), aby zápis do DB odpovídal `srid=4326`.

Architektura:

* :class:`ShpUzszSource` implementuje :class:`RuianSource.fetch_full_state` –
  v jednom průchodu načte SHP layery, ve druhém průchodu UZSZ XML pro body,
  vrátí :class:`RuianFullState`. Metoda :meth:`fetch_changes` vyhazuje
  :class:`NotImplementedError` (změny řeší cron přes :class:`FileVfrSource`).

Pro denní inkrementální sync se nadále používá :mod:`vfr_parser` /
:mod:`vfr_download` se variantou ``ZKSH``.
"""

from __future__ import annotations

import logging
import re
import zipfile
from pathlib import Path
from typing import Dict, Iterable, Optional

from core.coordTransform import transform_geom_to_wgs84
from django.contrib.gis.gdal import DataSource
from heslar.ruian_sync.provider import (
    RuianChangeEvent,
    RuianFullState,
    RuianKatastrDTO,
    RuianKrajDTO,
    RuianOkresDTO,
    RuianSource,
)
from lxml import etree

logger = logging.getLogger(__name__)


#: Mapování úrovně RÚIAN → název SHP souboru (bez přípony) v ZIPu `1.zip`.
#:
#: Pořadí odpovídá hierarchii (kraj → okres → obec → katastr); obce
#: se načítají jen kvůli atributu ``OKRES_KOD`` v případě, že ho katastry
#: nemají (KATUZE_P už ale OKRES_KOD obsahuje, takže obce nejsou striktně nutné).
_SHP_LAYERS = {
    "kraj": "VUSC_P",
    "okres": "OKRESY_P",
    "katastr": "KATUZE_P",
}

#: Konstanty pro extrakci atributů z DBF (sloupce mají různé názvy podle vrstvy).
#:
#: Klíč = úroveň, hodnota = mapa logického jména na DBF sloupec.
_SHP_ATTR_MAP = {
    "kraj": {"kod": "KOD", "nazev": "NAZEV"},
    "okres": {"kod": "KOD", "nazev": "NAZEV", "kraj_kod": "VUSC_KOD"},
    "katastr": {"kod": "KOD", "nazev": "NAZEV", "okres_kod": "OKRES_KOD"},
}

#: Identifikační prefixy elementů ``gml:id`` v UZSZ pro mapování na úroveň.
#:
#: Z PDF specifikace VFR a empirické inspekce souboru:
#: ``VC.<kod>`` = Vusc, ``OK.<kod>`` = Okres, ``OB.<kod>`` = Obec,
#: ``KU.<kod>`` = KatastralniUzemi.
_UZSZ_ID_PREFIXES = {
    "kraj": "VC",
    "okres": "OK",
    "obec": "OB",
    "katastr": "KU",
}


#: Známé pseudo-prvky, pro které RÚIAN UZSZ záměrně **neposkytuje**
#: definiční bod – fallback na centroid je očekávaný a nemá se logovat
#: jako ``WARNING``, ale jen jako ``INFO``.
#:
#: Klíč: dvojice ``(level, kod)``. Položky:
#:
#: * ``("okres", 9999)`` – pseudo-okres „území Hlavního města Prahy"
#:   (LAU1: ``CZ0100``, NUTS3: ``CZ010``). V SHP existuje, protože ČÚZK
#:   potřebuje „okresové" napojení pro 112 katastrů Prahy. RÚIAN ale
#:   v Praze administrativně okresy nemá (Vusc 19 → KÚ přímo), takže
#:   v UZSZ pro něj žádný ``DOK.9999`` neexistuje.
_FALLBACK_EXPECTED = {
    ("okres", 9999),
}


class ShpUzszSource(RuianSource):
    """
    :class:`RuianSource` načítající polygony z SHP a definiční body z VFR `ST_UZSZ`.

    Třída otevírá ZIP archivy přes vestavěné nástroje (``zipfile``, GDAL přes
    Django ``DataSource``) a kombinuje výsledek do jednotného
    :class:`RuianFullState`. Kraje/okresy/katastry jsou převzaty kompletně;
    obce slouží pouze jako mezičlánek pro mapování ``obec_kod → okres_kod``,
    pokud by ho KATUZE_P výjimečně neměl.

    .. note::
       SHP zdroj nepublikuje denní změny, proto :meth:`fetch_changes`
       vyhazuje :class:`NotImplementedError`. Pro inkrementální sync použijte
       :class:`heslar.ruian_sync.provider.FileVfrSource` s variantou ``ZKSH``.
    """

    source_id = "shp_uzsz"

    def __init__(self, shp_path: Path, uzsz_path: Path):
        """
        :param shp_path: Cesta k ``1.zip`` (státní SHP, EPSG:5514) nebo k
            již rozbalenému adresáři obsahujícímu ``VUSC_P.shp``,
            ``OKRESY_P.shp``, ``KATUZE_P.shp``.
        :param uzsz_path: Cesta k ``YYYYMMDD_ST_UZSZ.xml.zip`` (nebo rozbalenému
            ``.xml`` souboru). Musí jít o **základní datovou sadu (UZSZ)**,
            ne o ``ST_UKSH`` ani jinou variantu – jiné typy souborů
            neobsahují definiční body pro KÚ a sync by selhal s
            ``IntegrityError`` při uložení katastru.

            :raises FileNotFoundError: Pokud některá z cest neexistuje.
            :raises ValueError: Pokud ``uzsz_path`` neobsahuje ``ST_UZSZ`` v hlavičce
                ``<vf:TypSouboru>`` (typický uživatelský omyl: záměna ST_UKSH/ST_UZSZ).
        """
        self.shp_path = Path(shp_path)
        self.uzsz_path = Path(uzsz_path)
        if not self.shp_path.exists():
            raise FileNotFoundError(f"SHP cesta nenalezena: {self.shp_path}")
        if not self.uzsz_path.exists():
            raise FileNotFoundError(f"UZSZ cesta nenalezena: {self.uzsz_path}")
        self._validate_uzsz_header()

    def _validate_uzsz_header(self) -> None:
        """
        Ověří, že předaný ``uzsz_path`` je opravdu ``ST_UZSZ`` soubor.

        Z VFR specifikace má každý soubor v hlavičce ``<vf:Hlavicka>`` element
        ``<vf:TypSouboru>``, jehož hodnota odpovídá názvu souboru (např.
        ``ST_UZSZ``, ``ST_UKSH``, ``ST_ZKSH`` atd.). Bez této kontroly by
        záměna typů (např. ST_UKSH → ST_UZSZ) prošla parserem (XML by se
        zpracovalo, jen by mapa def. bodů byla prázdná) a sync by spadl
        až při insertu prvního katastru s ``IntegrityError``.

        :raises ValueError: Pokud TypSouboru není ``ST_UZSZ``.
        """
        try:
            with self._open_uzsz_stream() as fh:
                ctx = etree.iterparse(fh, events=("end",), huge_tree=True)
                for _, elem in ctx:
                    if etree.QName(elem.tag).localname == "TypSouboru":
                        typ = (elem.text or "").strip()
                        elem.clear()
                        if typ != "ST_UZSZ":
                            raise ValueError(
                                f"Neočekávaný typ VFR souboru pro UZSZ vstup: {typ!r}. "
                                f"Předaná cesta {self.uzsz_path} obsahuje jiný typ "
                                f"(typická záměna: ST_UKSH místo ST_UZSZ). "
                                f"ST_UKSH neobsahuje definiční body katastrů, sync by selhal. "
                                f"Stáhněte správný soubor "
                                f"`https://services.cuzk.gov.cz/vfr/<RRRRMM>/<RRRRMMDD>_ST_UZSZ.xml.zip`."
                            )
                        return
                    elem.clear()
        except etree.XMLSyntaxError as exc:
            raise ValueError(f"UZSZ soubor {self.uzsz_path} není platné XML: {exc}") from exc
        raise ValueError(
            f"UZSZ soubor {self.uzsz_path} neobsahuje element <vf:TypSouboru> – "
            f"pravděpodobně poškozený nebo neočekávaný formát."
        )

    # ------------------------------------------------------------------
    # RuianSource API
    # ------------------------------------------------------------------

    def fetch_full_state(self) -> RuianFullState:
        """
        Načte plný stav krajů/okresů/katastrů ze SHP polygonů + UZSZ bodů.

        Postup:

        1. Z UZSZ extrahuje slovníky ``definiční_bod_wkt`` indexované podle
           ``kód`` pro úrovně Vusc/Okres/Obec/KU (jediný průchod XML).
        2. Otevře jednotlivé SHP layery, převede každý prvek na příslušné
           DTO, doplní definiční bod z mapy z kroku 1 (pokud chybí, ponechá
           ``None``).
        3. Vrátí :class:`RuianFullState`.

            :return: Naplněná instance :class:`RuianFullState`.
        """
        logger.debug(
            "heslar.ruian_sync.shp_importer.fetch_full_state.start",
            extra={"shp": str(self.shp_path), "uzsz": str(self.uzsz_path)},
        )

        def_bod_kraj, def_bod_okres, def_bod_katastr = self._load_uzsz_definicni_body()

        kraje = self._load_kraje(def_bod_kraj)
        okresy = self._load_okresy(def_bod_okres)
        katastry = self._load_katastry(def_bod_katastr)

        logger.debug(
            "heslar.ruian_sync.shp_importer.fetch_full_state.end",
            extra={"kraje": len(kraje), "okresy": len(okresy), "katastry": len(katastry)},
        )
        return RuianFullState(kraje=kraje, okresy=okresy, katastry=katastry)

    def fetch_changes(self, day) -> Iterable[RuianChangeEvent]:
        """
        Změnové soubory tato implementace nepodporuje.

        :param day: Den, ke kterému by změny platily (nepoužito).

            :return: Nevrací se – metoda vždy vyhodí výjimku.
            :raises NotImplementedError: Vždy. Pro inkrementální sync použijte
                :class:`heslar.ruian_sync.provider.FileVfrSource` s ``ZKSH``.
        """
        raise NotImplementedError(
            "ShpUzszSource je určen jen pro plný sync. " "Pro denní změny použijte FileVfrSource (ZKSH)."
        )

    # ------------------------------------------------------------------
    # UZSZ – extrakce definičních bodů
    # ------------------------------------------------------------------

    def _load_uzsz_definicni_body(self):
        """
        Načte mapy ``kód → WKT POINT(EPSG:4326)`` z UZSZ pro kraj/okres/katastr.

        Iteruje XML jen jednou; matchuje elementy podle ``gml:id`` prefixu
        (``VC.``/``OK.``/``KU.``). Obce se zde negenerují – vazba na obec
        není v DTO potřeba (KATUZE_P přímo zná ``OKRES_KOD``).

            :return: Trojice slovníků ``(kraj_pts, okres_pts, katastr_pts)``,
                kde hodnoty jsou WKT POINT v EPSG:4326 nebo prázdný řetězec
                pokud bod chybí.
        """
        kraj_pts: Dict[int, str] = {}
        okres_pts: Dict[int, str] = {}
        katastr_pts: Dict[int, str] = {}

        target_prefixes = {
            _UZSZ_ID_PREFIXES["kraj"]: kraj_pts,
            _UZSZ_ID_PREFIXES["okres"]: okres_pts,
            _UZSZ_ID_PREFIXES["katastr"]: katastr_pts,
        }

        # Iterujeme přes všechny <gml:Point> elementy v XML. UZSZ má dvě formy:
        #
        # * Vusc/Okres/Obec/MOMC/SP/Mop/Region/Stat – přímý ``<gml:Point gml:id="DVC.19">``
        #   uvnitř ``<DefinicniBod>``;
        # * KatastralniUzemi/ZSJ/CastObce – ``<gml:MultiPoint gml:id="DKU.668753">``
        #   se vnořeným ``<gml:Point gml:id="DKU.668753.1">``.
        #
        # Akceptujeme oba tvary ``gml:id`` – bez vnořeného segmentu (``DVC.19``)
        # i s ním (``DKU.668753.1``); kód bereme z **prvního** segmentu za prefixem.
        # Pokud bychom dostali duplicitní zápis pro tentýž kód, převálcujeme jej
        # poslední hodnotou – v UZSZ jsou všechny instance pro daný kód shodné.
        with self._open_uzsz_stream() as fh:
            ctx = etree.iterparse(fh, events=("end",), huge_tree=True)
            for _, elem in ctx:
                if etree.QName(elem.tag).localname != "Point":
                    continue
                gml_id = elem.get("{http://www.opengis.net/gml/3.2}id") or elem.get("id") or ""
                m = re.match(r"D([A-Z]+)\.(\d+)", gml_id)
                if not m:
                    elem.clear()
                    continue
                prefix, kod_text = m.group(1), m.group(2)
                target_dict = target_prefixes.get(prefix)
                if target_dict is None:
                    elem.clear()
                    continue
                pos_text = self._first_pos(elem)
                if pos_text is None:
                    elem.clear()
                    continue
                wkt_4326 = self._point_to_wgs84_wkt(pos_text)
                if wkt_4326 is not None:
                    try:
                        target_dict[int(kod_text)] = wkt_4326
                    except ValueError:
                        pass
                elem.clear()
                # Uvolnit předchozí siblingy (snížení paměti)
                parent = elem.getparent()
                if parent is not None:
                    while elem.getprevious() is not None:
                        del parent[0]

        logger.debug(
            "heslar.ruian_sync.shp_importer._load_uzsz_definicni_body",
            extra={"kraje": len(kraj_pts), "okresy": len(okres_pts), "katastry": len(katastr_pts)},
        )
        return kraj_pts, okres_pts, katastr_pts

    def _open_uzsz_stream(self):
        """
        Otevře UZSZ XML stream (z ZIPu nebo přímo z .xml).

            :return: File-like objekt s UTF-8 XML obsahem.
            :raises ValueError: Pokud ZIP neobsahuje XML.
        """
        p = self.uzsz_path
        if p.suffix.lower() == ".zip" or zipfile.is_zipfile(str(p)):
            zf = zipfile.ZipFile(str(p))
            xml_names = [n for n in zf.namelist() if n.lower().endswith(".xml")]
            if not xml_names:
                raise ValueError(f"UZSZ ZIP neobsahuje žádný .xml: {p}")
            return zf.open(xml_names[0])
        return open(str(p), "rb")

    @staticmethod
    def _first_pos(elem) -> Optional[str]:
        """
        Najde první ``gml:pos`` v elementu a vrátí jeho text.

        :param elem: lxml element (typicky ``gml:MultiPoint``).

            :return: Textový obsah ``pos`` nebo ``None``.
        """
        for ch in elem.iter():
            if etree.QName(ch.tag).localname == "pos":
                return (ch.text or "").strip()
        return None

    # ------------------------------------------------------------------
    # SHP – načítání polygonů
    # ------------------------------------------------------------------

    def _load_kraje(self, def_bod_map: Dict[int, str]):
        """
        Načte kraje (Vusc) ze ``VUSC_P.shp`` a doplní definiční body.

        Pokud UZSZ pro daný kraj definiční bod neposkytl, použije se
        fallback na centroid polygonu (viz :meth:`_centroid_to_wgs84_wkt`).

        :param def_bod_map: Mapa ``kód kraje → WKT POINT(EPSG:4326)``.

            :return: Seznam :class:`RuianKrajDTO`.
        """
        out = []
        for feat in self._iter_shp_features("kraj"):
            kod = self._safe_int(feat.get("KOD"))
            nazev = (feat.get("NAZEV") or "").strip()
            if kod is None or not nazev:
                continue
            hranice_wkt = self._geom_to_wgs84_multipolygon(feat.geom)
            def_bod_wkt = def_bod_map.get(kod) or self._centroid_to_wgs84_wkt(feat.geom, kod=kod, level="kraj")
            out.append(
                RuianKrajDTO(
                    kod=kod,
                    nazev=nazev,
                    nazev_en=None,  # SHP neposkytuje
                    rada_id="",  # SHP neposkytuje (řeší syncer)
                    definicni_bod_wkt=def_bod_wkt,
                    hranice_wkt=hranice_wkt,
                )
            )
        return out

    def _load_okresy(self, def_bod_map: Dict[int, str]):
        """
        Načte okresy ze ``OKRESY_P.shp`` a doplní definiční body.

        Pokud UZSZ pro daný okres definiční bod neposkytl, použije se
        fallback na centroid polygonu.

        :param def_bod_map: Mapa ``kód okresu → WKT POINT(EPSG:4326)``.

            :return: Seznam :class:`RuianOkresDTO`.
        """
        out = []
        for feat in self._iter_shp_features("okres"):
            kod = self._safe_int(feat.get("KOD"))
            nazev = (feat.get("NAZEV") or "").strip()
            kraj_kod = self._safe_int(feat.get("VUSC_KOD"))
            if kod is None or not nazev:
                continue
            hranice_wkt = self._geom_to_wgs84_multipolygon(feat.geom)
            def_bod_wkt = def_bod_map.get(kod) or self._centroid_to_wgs84_wkt(feat.geom, kod=kod, level="okres")
            out.append(
                RuianOkresDTO(
                    kod=kod,
                    nazev=nazev,
                    kraj_kod=kraj_kod or 0,
                    nazev_en=None,
                    spz="",  # SHP neposkytuje
                    definicni_bod_wkt=def_bod_wkt,
                    hranice_wkt=hranice_wkt,
                )
            )
        return out

    def _load_katastry(self, def_bod_map: Dict[int, str]):
        """
        Načte katastry ze ``KATUZE_P.shp`` a doplní definiční body.

        Pokud UZSZ pro daný katastr definiční bod neposkytl (např. nově
        vzniklý KÚ, který v měsíčním UZSZ ještě není), použije se fallback
        na centroid polygonu. To odpovídá historické konvenci projektu –
        existující záznamy v DB mají ``definicni_bod = ST_Centroid(hranice)``
        (ověřeno na vzorku 1000 KU s 100% match).

        Model :class:`RuianKatastr.definicni_bod` je NOT NULL, takže fallback
        je nutný – bez něj by import selhal s ``IntegrityError``.

        :param def_bod_map: Mapa ``kód katastru → WKT POINT(EPSG:4326)``.

            :return: Seznam :class:`RuianKatastrDTO`.
        """
        out = []
        fallback_count = 0
        for feat in self._iter_shp_features("katastr"):
            kod = self._safe_int(feat.get("KOD"))
            nazev = (feat.get("NAZEV") or "").strip()
            okres_kod = self._safe_int(feat.get("OKRES_KOD"))
            if kod is None or not nazev:
                continue
            hranice_wkt = self._geom_to_wgs84_multipolygon(feat.geom)
            def_bod_wkt = def_bod_map.get(kod)
            if not def_bod_wkt:
                def_bod_wkt = self._centroid_to_wgs84_wkt(feat.geom, kod=kod, level="katastr")
                if def_bod_wkt:
                    fallback_count += 1
            out.append(
                RuianKatastrDTO(
                    kod=kod,
                    nazev=nazev,
                    okres_kod=okres_kod or 0,
                    definicni_bod_wkt=def_bod_wkt,
                    hranice_wkt=hranice_wkt,
                )
            )
        if fallback_count:
            logger.info(
                "heslar.ruian_sync.shp_importer._load_katastry.fallback_summary",
                extra={"katastry_with_centroid_fallback": fallback_count},
            )
        return out

    # ------------------------------------------------------------------
    # SHP – iterace
    # ------------------------------------------------------------------

    def _iter_shp_features(self, level: str):
        """
        Generuje features z odpovídajícího SHP layeru.

        Pokud je ``shp_path`` ZIP, soubor rozbalí do dočasného adresáře
        při prvním přístupu. Pokud je adresář, otevírá ``.shp`` napřímo.

        :param level: ``"kraj"`` / ``"okres"`` / ``"katastr"``.

            :return: Generátor lxml feature objektů.
            :raises FileNotFoundError: Pokud SHP layer pro danou úroveň neexistuje.
        """
        layer_basename = _SHP_LAYERS[level]
        shp_file_path = self._resolve_shp_layer(layer_basename)
        ds = DataSource(str(shp_file_path))
        layer = ds[0]
        for feat in layer:
            yield feat

    def _resolve_shp_layer(self, basename: str) -> Path:
        """
        Vrátí cestu k ``<basename>.shp`` ze ``shp_path``.

        Podporuje:

        * ``shp_path`` jako adresář – hledá ``<basename>.shp`` přímo v něm,
        * ``shp_path`` jako ZIP – rozbalí potřebné soubory do
          ``shp_path.parent / "<stem>_unpacked"`` (jen pokud ještě nejsou rozbalené).

        :param basename: Základ názvu vrstvy bez přípony, např. ``"VUSC_P"``.

            :return: Absolutní cesta k ``.shp``.
            :raises FileNotFoundError: Pokud vrstva neexistuje.
        """
        if self.shp_path.is_dir():
            target = self.shp_path / f"{basename}.shp"
            if not target.exists():
                raise FileNotFoundError(f"SHP layer nenalezen: {target}")
            return target

        # ZIP – rozbalit, pokud ještě není
        if zipfile.is_zipfile(str(self.shp_path)):
            unpack_dir = self.shp_path.parent / f"{self.shp_path.stem}_unpacked"
            unpack_dir.mkdir(parents=True, exist_ok=True)
            target = unpack_dir / f"{basename}.shp"
            if not target.exists():
                with zipfile.ZipFile(str(self.shp_path)) as zf:
                    # Rozbalit všechny pomocné soubory (.shp, .shx, .dbf, .prj, .cpg)
                    for member in zf.namelist():
                        member_path = Path(member)
                        if member_path.stem == basename and member_path.suffix.lower() in (
                            ".shp",
                            ".shx",
                            ".dbf",
                            ".prj",
                            ".cpg",
                        ):
                            zf.extract(member, str(unpack_dir))
                            # Pokud je v ZIPu uložen v podadresáři, přemístit do unpack_dir
                            extracted = unpack_dir / member
                            if extracted != unpack_dir / member_path.name:
                                extracted.rename(unpack_dir / member_path.name)
            if not target.exists():
                raise FileNotFoundError(f"SHP layer {basename} nebyl v archivu {self.shp_path} nalezen.")
            return target

        raise FileNotFoundError(f"SHP cesta není ZIP ani adresář: {self.shp_path}")

    # ------------------------------------------------------------------
    # Geometrie – konverze EPSG:5514 → 4326
    # ------------------------------------------------------------------

    @staticmethod
    def _geom_to_wgs84_multipolygon(geom) -> Optional[str]:
        """
        Převede GDAL geometrii (Polygon/MultiPolygon, EPSG:5514) na WKT
        MULTIPOLYGON v EPSG:4326 přes :mod:`core.coordTransform`.

        Polygon obalí do MULTIPOLYGON, aby DTO odpovídalo `MultiPolygonField`
        v Django modelech.

        :param geom: GDAL geometrie z SHP feature.

            :return: WKT MULTIPOLYGON v EPSG:4326 nebo ``None`` při selhání.
        """
        if geom is None:
            return None
        wkt_5514 = geom.wkt
        if wkt_5514 is None:
            return None
        # Pokud je to Polygon, obal jako MULTIPOLYGON((...))
        if wkt_5514.upper().startswith("POLYGON"):
            inner = wkt_5514[wkt_5514.index("(") :]
            wkt_5514 = "MULTIPOLYGON(" + inner + ")"
        try:
            transformed = transform_geom_to_wgs84(wkt_5514)
        except Exception as err:  # noqa: BLE001 – defenzivní; chyba v transformaci 1 prvku nezhasí celý sync
            logger.warning(
                "heslar.ruian_sync.shp_importer._geom_to_wgs84_multipolygon.error",
                extra={"error": str(err)},
            )
            return None
        if isinstance(transformed, tuple):
            return transformed[0]
        return transformed

    @staticmethod
    def _centroid_to_wgs84_wkt(geom, *, kod: Optional[int] = None, level: str = "") -> Optional[str]:
        """
        Vrátí WKT POINT centroidu polygonu v EPSG:4326.

        Slouží jako fallback pro definiční bod, pokud ho UZSZ neposkytl.
        Centroid se počítá nad původní geometrií v EPSG:5514, pak se
        výsledný bod transformuje do EPSG:4326 přes
        :mod:`core.coordTransform`. Tento postup odpovídá historické
        konvenci projektu (existující ``RuianKatastr.definicni_bod`` má
        identickou hodnotu jako ``ST_Centroid(hranice)`` – ověřeno na
        vzorku 1000 záznamů s 100% shodou).

        Při úspěšném dopočtu zaloguje **warning** – fallback je sice validní
        (a očekávaný pro nově vzniklé prvky, které UZSZ ještě nezná), ale
        operátor by měl o jeho použití vědět: hodnota se mírně liší od
        autoritativní hodnoty z RÚIAN, kterou by měl příští `ST_UZSZ`
        už obsahovat. Sledováním warningů v ``RuianSyncRun.note`` /
        adminu se dá zjistit, kolik prvků bylo třeba dopočítat.

        :param geom: GDAL ``OGRGeometry`` z SHP feature (polygon/multipolygon
            v EPSG:5514).
        :param kod: Kód prvku pro logování (volitelné).
        :param level: Úroveň prvku pro logování – ``"kraj"``/``"okres"``/
            ``"katastr"`` (volitelné).

            :return: WKT ``POINT(lon lat)`` v EPSG:4326 nebo ``None`` při
                selhání transformace či prázdné geometrii.
        """
        if geom is None:
            return None
        try:
            centroid = geom.centroid  # OGRGeometry typu POINT v 5514
            wkt_5514 = centroid.wkt if centroid is not None else None
        except Exception as err:  # noqa: BLE001
            logger.warning(
                "heslar.ruian_sync.shp_importer._centroid_to_wgs84_wkt.error",
                extra={"error": str(err), "kod": kod, "level": level},
            )
            return None
        if not wkt_5514:
            logger.warning(
                "heslar.ruian_sync.shp_importer._centroid_to_wgs84_wkt.empty_centroid",
                extra={"kod": kod, "level": level},
            )
            return None
        try:
            transformed = transform_geom_to_wgs84(wkt_5514)
        except Exception as err:  # noqa: BLE001
            logger.warning(
                "heslar.ruian_sync.shp_importer._centroid_to_wgs84_wkt.transform_error",
                extra={"error": str(err), "wkt": wkt_5514, "kod": kod, "level": level},
            )
            return None
        if isinstance(transformed, tuple):
            transformed = transformed[0]

        # Pro známé pseudo-prvky (viz _FALLBACK_EXPECTED) je centroid očekávaný
        # výsledek – logujeme jako INFO, aby se neztrácel ve WARNING streamu.
        # Pro ostatní prvky je fallback signalizace, že UZSZ chybí dat (typicky
        # nově vzniklý prvek, který v měsíčním UZSZ ještě není) – WARNING.
        if (level, kod) in _FALLBACK_EXPECTED:
            log_call = logger.info
            reason = "Pseudo-prvek bez RÚIAN definičního bodu (whitelist), " "použit centroid polygonu."
        else:
            log_call = logger.warning
            reason = "UZSZ neposkytl autoritativní definiční bod, použit centroid polygonu."

        log_call(
            "heslar.ruian_sync.shp_importer._centroid_to_wgs84_wkt.fallback_used",
            extra={
                "kod": kod,
                "level": level,
                "centroid_wkt": transformed,
                "reason": reason,
            },
        )
        return transformed

    @staticmethod
    def _point_to_wgs84_wkt(pos_text: str) -> Optional[str]:
        """
        Převede ``gml:pos`` (S-JTSK East-North, typicky záporné Y/X)
        na WKT POINT v EPSG:4326.

        :param pos_text: Text obsahu ``gml:pos`` (např. ``"-751802.14 -1177969.41"``).

            :return: WKT ``POINT(lon lat)`` v EPSG:4326 nebo ``None``.
        """
        parts = pos_text.split()
        if len(parts) < 2:
            return None
        try:
            x, y = float(parts[0]), float(parts[1])
        except ValueError:
            return None
        wkt_5514 = f"POINT({x} {y})"
        try:
            transformed = transform_geom_to_wgs84(wkt_5514)
        except Exception as err:  # noqa: BLE001
            logger.warning(
                "heslar.ruian_sync.shp_importer._point_to_wgs84_wkt.error",
                extra={"error": str(err), "pos": pos_text},
            )
            return None
        if isinstance(transformed, tuple):
            return transformed[0]
        return transformed

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_int(value) -> Optional[int]:
        """
        Bezpečně převede hodnotu na int (atribut z DBF může být ``None`` / ``""``).

        :param value: Vstupní hodnota libovolného typu.

            :return: ``int`` nebo ``None``.
        """
        if value is None:
            return None
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None
