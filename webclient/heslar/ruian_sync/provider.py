"""
Abstrakce zdroje dat RÚIAN a konkrétní implementace ``FileVfrSource``.

Modul definuje DTO pro popis kraje, okresu a katastru tak, jak je vrací zdroj
ČÚZK, a abstraktní bázi :class:`RuianSource`, kterou používá vrstva
``syncer`` k aplikaci změn na DB. První konkrétní implementace
:class:`FileVfrSource` načítá lokální VFR soubor (ZIP s GML 3.2.1) – stahování
zajišťuje operátor (resp. cron pro denní změnové soubory) mimo tento modul.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

logger = logging.getLogger(__name__)


@dataclass
class RuianKrajDTO:
    """
    DTO popisující jeden kraj v RÚIAN.

    :param kod: Číselný kód kraje z RÚIAN (primární klíč ze zdroje).
    :param nazev: Český název kraje.
    :param nazev_en: Anglický název kraje, pokud je v RÚIAN k dispozici.
    :param rada_id: Identifikátor rady (jednopísmenný kód).
    :param definicni_bod_wkt: Definiční bod kraje ve WKT (EPSG:4326), pokud je dostupný.
    :param hranice_wkt: Hranice kraje ve WKT (MultiPolygon, EPSG:4326), pokud jsou dostupné.
    """

    kod: int
    nazev: str
    nazev_en: Optional[str] = None
    rada_id: str = ""
    definicni_bod_wkt: Optional[str] = None
    hranice_wkt: Optional[str] = None


@dataclass
class RuianOkresDTO:
    """
    DTO popisující jeden okres v RÚIAN.

    :param kod: Číselný kód okresu z RÚIAN.
    :param nazev: Český název okresu.
    :param nazev_en: Anglický název okresu, pokud je v RÚIAN k dispozici.
    :param spz: SPZ kód okresu (max. 3 znaky).
    :param kraj_kod: Kód nadřazeného kraje.
    :param definicni_bod_wkt: Definiční bod okresu ve WKT (EPSG:4326).
    :param hranice_wkt: Hranice okresu ve WKT (MultiPolygon, EPSG:4326).
    """

    kod: int
    nazev: str
    kraj_kod: int
    nazev_en: Optional[str] = None
    spz: str = ""
    definicni_bod_wkt: Optional[str] = None
    hranice_wkt: Optional[str] = None


@dataclass
class RuianKatastrDTO:
    """
    DTO popisující jeden katastr v RÚIAN.

    :param kod: Číselný kód katastru z RÚIAN.
    :param nazev: Český název katastru.
    :param okres_kod: Kód nadřazeného okresu.
    :param definicni_bod_wkt: Definiční bod katastru ve WKT (Point, EPSG:4326).
    :param hranice_wkt: Hranice katastru ve WKT (MultiPolygon, EPSG:4326).
    """

    kod: int
    nazev: str
    okres_kod: int
    definicni_bod_wkt: Optional[str] = None
    hranice_wkt: Optional[str] = None


#: Druhy událostí ve změnovém VFR souboru, které syncer rozlišuje.
EVENT_UPSERT = "upsert"
EVENT_DELETE = "delete"

#: Úrovně RÚIAN prvků – pořadí odpovídá závislosti FK (kraj < okres < katastr).
LEVEL_KRAJ = "kraj"
LEVEL_OKRES = "okres"
LEVEL_KATASTR = "katastr"


@dataclass
class RuianChangeEvent:
    """
    Jedna událost ze změnového VFR souboru.

    Pro ``upsert`` musí být ``payload`` instance některého DTO
    (:class:`RuianKrajDTO`, :class:`RuianOkresDTO`, :class:`RuianKatastrDTO`).
    Pro ``delete`` stačí ``kod`` – DTO může být ``None``.

    :param level: Úroveň prvku (``kraj``/``okres``/``katastr``).
    :param event_type: Typ události (``upsert``/``delete``).
    :param kod: Kód prvku, kterého se událost týká.
    :param payload: DTO s novým stavem (jen u ``upsert``); ``None`` pro ``delete``.
    """

    level: str
    event_type: str
    kod: int
    payload: Optional[object] = None


@dataclass
class RuianFullState:
    """
    Kompletní stav prvků RÚIAN získaný ze stavového VFR.

    :param kraje: Seznam DTO všech krajů.
    :param okresy: Seznam DTO všech okresů.
    :param katastry: Seznam DTO všech katastrů.
    """

    kraje: list = field(default_factory=list)
    okresy: list = field(default_factory=list)
    katastry: list = field(default_factory=list)


class RuianSource(ABC):
    """
    Abstraktní rozhraní zdroje dat RÚIAN.

    Konkrétní implementace načítá data buď ze stavových VFR souborů
    (:meth:`fetch_full_state`), nebo z denních změnových VFR souborů
    (:meth:`fetch_changes`). Modul ``syncer`` zavolá jednu z metod podle
    režimu běhu.
    """

    #: Identifikátor zdroje ukládaný do ``RuianSyncRun.source``.
    source_id: str = "abstract"

    @abstractmethod
    def fetch_full_state(self) -> RuianFullState:
        """
        Vrací kompletní stav krajů/okresů/katastrů.

        Volaná při módu ``full`` (prvotní sync nebo ruční přerovnání).

        :return: Instance :class:`RuianFullState` s naplněnými seznamy DTO.
        :raises NotImplementedError: Pokud daný zdroj plný stav nepodporuje.
        """

    @abstractmethod
    def fetch_changes(self, day: date) -> Iterable[RuianChangeEvent]:
        """
        Generátor událostí (upsert/delete) pro daný den.

        Volaná cronem v módu ``delta`` pro každý den, který má ještě
        navázat (od ``RuianSyncRun.last_successful().data_valid_to + 1`` po dnešek).

        :param day: Den, ke kterému jsou změny platné.
        :return: Iterable :class:`RuianChangeEvent` v pořadí kraj → okres → katastr.
        :raises NotImplementedError: Pokud daný zdroj inkrementy nepodporuje.
        """


class FileVfrSource(RuianSource):
    """
    Zdroj RÚIAN dat čtoucí lokální **denní změnový** VFR soubor (ZIP/XML, GML 3.2.1).

    Používá se Celery cronem (:func:`cron.tasks.sync_ruian_changes`) pro
    inkrementální aktualizaci heslářů z ``ST_ZKSH`` souborů (originální
    hranice; generalizovanou variantu ``ZKSG`` projekt nepoužívá).

    Pro plný (initial) sync používej :class:`ShpUzszSource`.
    """

    source_id = "file_vfr"

    def __init__(self, path: Path):
        """
        :param path: Absolutní cesta k VFR souboru (ZIP nebo nezabalené XML/GML).

            :raises FileNotFoundError: Pokud cesta neexistuje.
        """
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"VFR cesta nenalezena: {self.path}")

    def fetch_full_state(self) -> RuianFullState:
        """
        Plný sync přes VFR není podporován.

        :return: Nevrací se – metoda vždy vyhodí výjimku.
        :raises NotImplementedError: Vždy. Pro plný sync použij
            :class:`heslar.ruian_sync.shp_importer.ShpUzszSource`
            (SHP + ``ST_UZSZ`` v jednom průchodu).
        """
        raise NotImplementedError(
            "FileVfrSource je určen pouze pro denní změnový VFR. " "Pro plný sync použij ShpUzszSource (SHP + ST_UZSZ)."
        )

    def fetch_changes(self, day: date) -> Iterable[RuianChangeEvent]:
        """
        Načte denní změnový VFR jako sekvenci událostí.

        :param day: Den, ke kterému jsou změny platné.

            :return: Iterable :class:`RuianChangeEvent` (upserty + DELETE pro zaniklé prvky).
        """
        from heslar.ruian_sync import vfr_parser

        logger.debug(
            "heslar.ruian_sync.FileVfrSource.fetch_changes.start",
            extra={"path": str(self.path), "day": day.isoformat()},
        )
        return vfr_parser.parse_changes(self.path)

    @classmethod
    def download_for_day(cls, day: date, target_dir: Path) -> "Optional[FileVfrSource]":
        """
        Stáhne denní změnový VFR (``ZKSH``) pro daný den z ČÚZK do ``target_dir``.

        Pokud server vrátí HTTP 404 (= ten den nebyly v RÚIAN žádné změny),
        vrací ``None`` a volající cron daný den přeskočí.

        :param day: Den, pro který se má soubor stáhnout.
        :param target_dir: Cílový adresář (typicky ``/vol/data-migrace/ruian_delta/``).

            :return: Instance :class:`FileVfrSource` se staženým souborem,
                nebo ``None`` při HTTP 404.
        """
        from heslar.ruian_sync import vfr_download

        path = vfr_download.download_change_file(day, Path(target_dir))
        if path is None:
            return None
        return cls(path)
