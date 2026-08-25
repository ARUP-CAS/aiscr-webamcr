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

Polygony i body jsou v EPSG:5514 (S-JTSK Krovak East-North) a v tomtéž
CRS se ukládají do DB — RÚIAN heslář je od migrace 0013 primárně JTSK.
Modul žádnou CRS transformaci neprovádí; jen normalizuje SHP polygony
na ``MULTIPOLYGON`` a případně invertuje znaménko UZSZ bodů z historické
záporné formy na kladnou (PostGIS EPSG:5514 East-North konvence).

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
        Načte mapy ``kód → WKT POINT(EPSG:5514)`` z UZSZ pro kraj/okres/katastr.

        Iteruje XML jen jednou; matchuje elementy podle ``gml:id`` prefixu
        (``VC.``/``OK.``/``KU.``). Obce se zde negenerují – vazba na obec
        není v DTO potřeba (KATUZE_P přímo zná ``OKRES_KOD``).

            :return: Trojice slovníků ``(kraj_pts, okres_pts, katastr_pts)``,
                kde hodnoty jsou WKT POINT v EPSG:5514 nebo prázdný řetězec
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
                wkt = self._point_wkt(pos_text)
                if wkt is not None:
                    try:
                        target_dict[int(kod_text)] = wkt
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
        fallback na centroid polygonu (viz :meth:`_centroid_wkt`).

        :param def_bod_map: Mapa ``kód kraje → WKT POINT(EPSG:5514)``.

            :return: Seznam :class:`RuianKrajDTO`.
        """
        out = []
        for feat in self._iter_shp_features("kraj"):
            kod = self._safe_int(feat.get("KOD"))
            nazev = (feat.get("NAZEV") or "").strip()
            if kod is None or not nazev:
                continue
            hranice_wkt = self._geom_to_multipolygon_wkt(feat.geom)
            def_bod_wkt = def_bod_map.get(kod) or self._centroid_wkt(feat.geom, kod=kod, level="kraj")
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

        :param def_bod_map: Mapa ``kód okresu → WKT POINT(EPSG:5514)``.

            :return: Seznam :class:`RuianOkresDTO`.
        """
        out = []
        for feat in self._iter_shp_features("okres"):
            kod = self._safe_int(feat.get("KOD"))
            nazev = (feat.get("NAZEV") or "").strip()
            kraj_kod = self._safe_int(feat.get("VUSC_KOD"))
            if kod is None or not nazev:
                continue
            hranice_wkt = self._geom_to_multipolygon_wkt(feat.geom)
            def_bod_wkt = def_bod_map.get(kod) or self._centroid_wkt(feat.geom, kod=kod, level="okres")
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

        :param def_bod_map: Mapa ``kód katastru → WKT POINT(EPSG:5514)``.

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
            hranice_wkt = self._geom_to_multipolygon_wkt(feat.geom)
            def_bod_wkt = def_bod_map.get(kod)
            if not def_bod_wkt:
                def_bod_wkt = self._centroid_wkt(feat.geom, kod=kod, level="katastr")
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
          ``shp_path.parent / "<stem>_unpacked"``.

        Rozbaluje se, pokud vrstva ještě rozbalená není **nebo je starší než
        archiv**. Bez kontroly stáří by se po stažení novějšího ``1.zip``
        tiše použila zastaralá data.

        :param basename: Základ názvu vrstvy bez přípony, např. ``"VUSC_P"``.

            :return: Absolutní cesta k ``.shp``.
            :raises FileNotFoundError: Pokud vrstva neexistuje.
        """
        if self.shp_path.is_dir():
            target = self.shp_path / f"{basename}.shp"
            if not target.exists():
                raise FileNotFoundError(f"SHP layer nenalezen: {target}")
            logger.info(
                "heslar.ruian_sync.shp_importer._resolve_shp_layer.directory",
                extra={"basename": basename, "path": str(target)},
            )
            return target

        # ZIP – rozbalit, pokud chybí nebo je zastaralé
        if zipfile.is_zipfile(str(self.shp_path)):
            unpack_dir = self.shp_path.parent / f"{self.shp_path.stem}_unpacked"
            unpack_dir.mkdir(parents=True, exist_ok=True)
            target = unpack_dir / f"{basename}.shp"
            zip_mtime = self.shp_path.stat().st_mtime
            zastarale = target.exists() and target.stat().st_mtime < zip_mtime
            if zastarale:
                logger.warning(
                    "heslar.ruian_sync.shp_importer._resolve_shp_layer.stale_unpacked",
                    extra={
                        "basename": basename,
                        "unpack_dir": str(unpack_dir),
                        "zip": str(self.shp_path),
                    },
                )
            if not target.exists() or zastarale:
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
                            # Pokud je v ZIPu uložen v podadresáři, přemístit do unpack_dir.
                            extracted = unpack_dir / member
                            if extracted != unpack_dir / member_path.name:
                                extracted.replace(unpack_dir / member_path.name)
                logger.info(
                    "heslar.ruian_sync.shp_importer._resolve_shp_layer.extracted",
                    extra={"basename": basename, "unpack_dir": str(unpack_dir), "zip": str(self.shp_path)},
                )
            if not target.exists():
                raise FileNotFoundError(f"SHP layer {basename} nebyl v archivu {self.shp_path} nalezen.")
            return target

        raise FileNotFoundError(f"SHP cesta není ZIP ani adresář: {self.shp_path}")

    # ------------------------------------------------------------------
    # Geometrie – WKT v EPSG:5514 v konvenci projektu (záporná / West-South)
    # ------------------------------------------------------------------
    #
    # Konvence projektu: ``core.coordTransform.convertToJTSK`` vrací ``[-Y, -X]``
    # (záporné), takže všechna 5514 data v DB (``pian.geom_sjtsk``, ``adb.geom``,
    # ``ruian_katastr.hranice`` po migraci 0013) jsou v této konvenci.
    #
    # SHP soubory z ČÚZK jsou nativně **kladné** EPSG:5514 East-North – proto
    # se při importu **vždy** invertují znaménka. UZSZ ``gml:pos`` může být
    # kladné i záporné – autodetekcí normalizujeme na zápornou formu.

    @staticmethod
    def _negate_wkt(wkt: str) -> str:
        """
        Invertuje znaménka všech čísel ve WKT řetězci.

        Sdílená helper funkce pro přechod mezi kladnou a zápornou konvencí
        EPSG:5514 (WKT obsahuje čísla jen v souřadnicích, ne v klíčových
        slovech, takže regex přes všechna čísla je bezpečný).

        :param wkt: Vstupní WKT.

            :return: WKT se všemi čísly s opačným znaménkem.
        """
        import re

        def _flip(match):
            s = match.group(0)
            if s.startswith("-"):
                return s[1:]
            return "-" + s

        return re.sub(r"-?\d+(?:\.\d+)?", _flip, wkt)

    @classmethod
    def _ensure_negative_wkt(cls, wkt: str) -> str:
        """
        Normalizuje WKT do záporné konvence EPSG:5514 (West-South).

        Autodetekce podle prvního souřadnicového čísla **uvnitř závorek**:
        pokud už je záporné, WKT se vrátí beze změny; pokud je kladné,
        použije se :meth:`_negate_wkt` na invertování všech znamének.

        :param wkt: Vstupní WKT (kladný nebo záporný 5514).

            :return: WKT v EPSG:5514 v záporné konvenci.
        """
        # Najdi první číslo _uvnitř_ souřadnicové části (po první levé závorce).
        # Regex vynechává klíčová slova jako "POLYGON", "MULTIPOLYGON", "POINT"
        # a vždy hledá první číslo za "(" – to je vždy X-souřadnice prvního bodu.
        m = re.search(r"\(\s*\(?\s*\(?\s*(-?)(\d)", wkt)
        if m and m.group(1) == "-":
            return wkt  # už je záporné
        return cls._negate_wkt(wkt)

    @classmethod
    def _geom_to_multipolygon_wkt(cls, geom) -> Optional[str]:
        """
        Vrátí WKT MULTIPOLYGON z GDAL geometrie SHP feature v záporné 5514.

        SHP z ČÚZK je v kladné EPSG:5514 East-North. Konvence projektu je
        záporná (West-South) – helper obalí ``Polygon`` do ``MULTIPOLYGON``
        a invertuje všechna znaménka.

        :param geom: GDAL geometrie z SHP feature (kladná 5514).

            :return: WKT MULTIPOLYGON v EPSG:5514 (záporná forma) nebo ``None``.
        """
        if geom is None:
            return None
        wkt = geom.wkt
        if wkt is None:
            return None
        if wkt.upper().startswith("POLYGON"):
            inner = wkt[wkt.index("(") :]
            wkt = "MULTIPOLYGON(" + inner + ")"
        return cls._ensure_negative_wkt(wkt)

    @classmethod
    def _centroid_wkt(cls, geom, *, kod: Optional[int] = None, level: str = "") -> Optional[str]:
        """
        Vrátí WKT POINT centroidu polygonu v záporné 5514.

        Slouží jako fallback pro definiční bod, pokud ho UZSZ neposkytl.
        Centroid se počítá nad původní SHP geometrií v kladné 5514,
        pak se invertují znaménka do konvence projektu (záporná 5514).

        Při dopočtu se loguje **warning** (u pseudo-prvků v
        :data:`_FALLBACK_EXPECTED` jen **info**) – fallback je signalizace,
        že UZSZ dat chybí (typicky nově vzniklý prvek).

        :param geom: GDAL ``OGRGeometry`` z SHP feature (kladná 5514).
        :param kod: Kód prvku pro logování (volitelné).
        :param level: Úroveň prvku pro logování – ``"kraj"``/``"okres"``/
            ``"katastr"`` (volitelné).

            :return: WKT ``POINT(x y)`` v EPSG:5514 (záporná forma) nebo ``None``.
        """
        if geom is None:
            return None
        try:
            centroid = geom.centroid  # OGRGeometry typu POINT v kladné 5514
            wkt_positive = centroid.wkt if centroid is not None else None
        except Exception as err:  # noqa: BLE001
            logger.warning(
                "heslar.ruian_sync.shp_importer._centroid_wkt.error",
                extra={"error": str(err), "kod": kod, "level": level},
            )
            return None
        if not wkt_positive:
            logger.warning(
                "heslar.ruian_sync.shp_importer._centroid_wkt.empty_centroid",
                extra={"kod": kod, "level": level},
            )
            return None
        wkt = cls._ensure_negative_wkt(wkt_positive)

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
            "heslar.ruian_sync.shp_importer._centroid_wkt.fallback_used",
            extra={
                "kod": kod,
                "level": level,
                "centroid_wkt": wkt,
                "reason": reason,
            },
        )
        return wkt

    @staticmethod
    def _point_wkt(pos_text: str) -> Optional[str]:
        """
        Převede ``gml:pos`` na WKT POINT v záporné EPSG:5514.

        UZSZ může dodávat souřadnice v kladné i záporné formě S-JTSK.
        Konvence projektu je záporná (West-South) – helper normalizuje
        obojí na zápornou formu.

        :param pos_text: Text obsahu ``gml:pos`` (např. ``"751802.14 1177969.41"``
            nebo ``"-751802.14 -1177969.41"``).

            :return: WKT ``POINT(x y)`` v EPSG:5514 (záporná forma) nebo ``None``.
        """
        parts = pos_text.split()
        if len(parts) < 2:
            return None
        try:
            x, y = float(parts[0]), float(parts[1])
        except ValueError:
            return None
        # Normalizace na zápornou formu (konvence projektu – West-South).
        if x > 0 and y > 0:
            x, y = -x, -y
        return f"POINT({x} {y})"

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
