"""
HTTP klient pro stahování **denních změnových** VFR souborů z ČÚZK.

Modul stahuje **vždy variantu ZKSH** = denní změnový (Z), kompletní (K),
současná RÚIAN (S), s **originálními** hranicemi katastrů (H).
Generalizované hranice (varianta ``ZKSG``) ani jiné kombinace
projekt nepoužívá – pro účely AMČR jsou potřeba pouze originální hranice
(``ZKSH``), proto v API nejsou žádné parametry varianty.

Plný (initial) sync se z VFR **nestahuje** – používá se SHP + ``ST_UZSZ``
přes :class:`heslar.ruian_sync.shp_importer.ShpUzszSource`.

Konvence názvu souboru (z PDF *DL058RR2 v4.0 kap. 4.2.4*)::

    <YYYYMMDD>_ST_ZKSH.xml.zip

Příklad: ``20260501_ST_ZKSH.xml.zip`` = denní změnový pro celou ČR
ke dni 1. 5. 2026 s originálními hranicemi.

Stahování probíhá streamovaně (``requests.get(stream=True)``).

URL pro stahování (``base_url``, ``atom_feed_url``, ``prefer_atom``)
se načítají z DB záznamu :class:`core.setting_models.CustomAdminSettings`
se skupinou ``ruian_sync`` a item_id ``vfr_download``. Hodnoty se čtou
**fresh při každém volání**, takže admin může URL přepsat za běhu bez
restartu workeru. Pokud DB záznam neexistuje (např. před spuštěním
migrací) nebo má neplatný JSON, použijí se modulové defaulty.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from lxml import etree

logger = logging.getLogger(__name__)


#: Pevná varianta VFR souborů, kterou AMČR používá – kompletní sada
#: s originálními hranicemi katastrů (ne generalizovanými).
_VARIANT = "ZKSH"

#: Default chunk size pro streamované stahování (8 MB).
_DEFAULT_CHUNK_SIZE = 8 * 1024 * 1024

#: HTTP timeout v sekundách pro celé spojení (headers + body); pro velké
#: soubory záměrně dlouhý.
_DEFAULT_TIMEOUT = 600

#: Skupina a id záznamu v ``CustomAdminSettings`` s konfigurací stahování.
_SETTINGS_GROUP = "ruian_sync"
_SETTINGS_ITEM = "vfr_download"

#: Modulové defaulty – použijí se, pokud DB záznam chybí nebo je neplatný.
#: Soubory leží ploše v ``vdp.cuzk.gov.cz/vymenny_format/soucasna/``
#: (žádné rozdělení po letech/měsících v cestě), retence sahá zhruba
#: rok zpět. ATOM feed ``RUIAN-S-K-Z`` listuje pouze posledních ~15 dnů
#: jako *novinky*, ale starší soubory v té cestě stejně existují.
#: ``target_dir`` je cílový adresář pro stažené VFR ZIP soubory na lokálním
#: filesystému kontejneru (mapuje se z hostitelského ``/home/migrace``).
_DEFAULTS = {
    "base_url": "https://vdp.cuzk.gov.cz/vymenny_format/soucasna/",
    "atom_feed_url": "https://atom.cuzk.gov.cz/RUIAN-S-K-Z/RUIAN-S-K-Z.xml",
    "prefer_atom": False,
    "target_dir": "/vol/data-migrace/ruian_delta/",
}


# ---------------------------------------------------------------------------
# Konfigurace z CustomAdminSettings
# ---------------------------------------------------------------------------


def _load_settings() -> dict:
    """
    Načte konfiguraci z :class:`CustomAdminSettings` (skupina ``ruian_sync``,
    item ``vfr_download``) a sloučí ji s modulovými defaulty.

    Záznam v DB má JSON ``value`` s klíči ``base_url`` / ``atom_feed_url`` /
    ``prefer_atom``. Chybějící klíče se doplní z :data:`_DEFAULTS`.

    Chyby (DB záznam neexistuje, neplatný JSON, ProgrammingError při
    migraci) se tiše ignorují a vrátí se čisté defaulty – sync nesmí
    spadnout kvůli chybějící konfiguraci.

        :return: Slovník s klíči ``base_url``, ``atom_feed_url``, ``prefer_atom``.
    """
    merged = dict(_DEFAULTS)
    try:
        from core.setting_models import CustomAdminSettings

        obj = CustomAdminSettings.objects.filter(item_group=_SETTINGS_GROUP, item_id=_SETTINGS_ITEM).first()
        if obj is None:
            return merged
        payload = json.loads(obj.value)
        if isinstance(payload, dict):
            for key in _DEFAULTS:
                if key in payload and payload[key] is not None:
                    merged[key] = payload[key]
    except Exception as err:  # noqa: BLE001 — fallback na defaulty
        logger.debug(
            "heslar.ruian_sync.vfr_download._load_settings.fallback",
            extra={"error": str(err)},
        )
    return merged


def _get_setting(key: str) -> Any:
    """
    Vrátí konkrétní hodnotu z konfigurace (s fallback na default).

    :param key: Klíč v JSON konfiguraci (``base_url`` / ``atom_feed_url`` /
        ``prefer_atom`` / ``target_dir``).

        :return: Hodnota z DB nebo z :data:`_DEFAULTS`.
    """
    return _load_settings().get(key, _DEFAULTS.get(key))


def get_target_dir() -> Path:
    """
    Vrátí cílový adresář pro stažené denní změnové VFR ZIP soubory.

    Hodnota se čte z :class:`CustomAdminSettings` (skupina ``ruian_sync``,
    item ``vfr_download``, klíč ``target_dir``); fallback je modulový default
    z :data:`_DEFAULTS`. Adresář **nemusí existovat** – :func:`download_change_file`
    ho vytvoří přes ``Path.parent.mkdir(parents=True, exist_ok=True)``.

        :return: Cesta jako :class:`pathlib.Path`.
    """
    return Path(_get_setting("target_dir"))


# ---------------------------------------------------------------------------
# URL builders
# ---------------------------------------------------------------------------


def _change_filename(day: date) -> str:
    """
    Sestaví název denního změnového VFR souboru pro variantu ``ZKSH``.

    :param day: Datum platnosti dat.

        :return: Název souboru ``YYYYMMDD_ST_ZKSH.xml.zip``.
    """
    return f"{day.strftime('%Y%m%d')}_ST_{_VARIANT}.xml.zip"


def build_change_url(day: date) -> str:
    """
    Sestaví URL pro stažení denního změnového VFR (varianta ``ZKSH``).

    Cesta na serveru je plochá – ``vdp.cuzk.gov.cz/vymenny_format/soucasna/``
    obsahuje všechny soubory přímo, bez rozdělení po letech či měsících.

    :param day: Konkrétní den, pro který se má soubor stáhnout.

        :return: Plně kvalifikovaná URL k dennímu změnovému VFR souboru.
    """
    return urljoin(_get_setting("base_url"), _change_filename(day))


# ---------------------------------------------------------------------------
# Streaming download
# ---------------------------------------------------------------------------


def _stream_to_file(
    url: str,
    target_path: Path,
    *,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    timeout: int = _DEFAULT_TIMEOUT,
) -> Optional[Path]:
    """
    Stáhne URL streamovaně do lokálního souboru.

    :param url: URL ke stažení.
    :param target_path: Cílová cesta na disku.
    :param chunk_size: Velikost chunku v bytech.
    :param timeout: HTTP timeout v sekundách.

        :return: ``target_path`` při úspěchu, ``None`` při HTTP 404.
        :raises requests.HTTPError: Při jiných HTTP chybách než 404.
        :raises requests.RequestException: Při síťové chybě.
    """
    logger.debug("heslar.ruian_sync.vfr_download._stream_to_file.start", extra={"url": url})
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_name(target_path.name + ".tmp")
    try:
        with requests.get(url, stream=True, timeout=timeout) as resp:
            if resp.status_code == 404:
                logger.debug("heslar.ruian_sync.vfr_download._stream_to_file.not_found", extra={"url": url})
                return None
            resp.raise_for_status()
            with open(temp_path, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if chunk:
                        fh.write(chunk)
        temp_path.rename(target_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise
    logger.debug(
        "heslar.ruian_sync.vfr_download._stream_to_file.end",
        extra={"url": url, "size": target_path.stat().st_size, "path": str(target_path)},
    )
    return target_path


def download_change_file(day: date, target_dir: Path) -> Optional[Path]:
    """
    Stáhne denní změnový VFR (``ZKSH``) pro daný den do ``target_dir``.

    Pokud server vrátí HTTP 404, znamená to, že daný den nebyly v RÚIAN
    žádné změny (typicky víkend nebo státní svátek) – funkce vrací
    ``None`` a cron tento den přeskočí.

    :param day: Konkrétní den.
    :param target_dir: Cílový adresář.

        :return: Cesta ke staženému souboru, nebo ``None`` při 404.
    """
    if bool(_get_setting("prefer_atom")):
        try:
            return download_via_atom(day, target_dir)
        except Exception as err:  # noqa: BLE001 — fallback na deterministické URL
            logger.warning(
                "heslar.ruian_sync.vfr_download.download_change_file.atom_failed",
                extra={"day": day.isoformat(), "error": str(err)},
            )

    url = build_change_url(day)
    filename = url.rsplit("/", 1)[-1]
    target_path = Path(target_dir) / filename
    return _stream_to_file(url, target_path)


# ---------------------------------------------------------------------------
# ATOM feed fallback
# ---------------------------------------------------------------------------


def _parse_atom_feed(feed_url: str, timeout: int = 60) -> list:
    """
    Stáhne a parsuje ATOM feed; vrací seznam ``(title, href)`` dvojic.

    :param feed_url: URL ATOM feedu (např. https://atom.cuzk.gov.cz/...).
    :param timeout: HTTP timeout v sekundách.

        :return: Seznam dvojic ``(entry_title, entry_link_href)``.
        :raises requests.HTTPError: Při HTTP chybě.
    """
    logger.debug("heslar.ruian_sync.vfr_download._parse_atom_feed.start", extra={"url": feed_url})
    resp = requests.get(feed_url, timeout=timeout)
    resp.raise_for_status()
    root = etree.fromstring(resp.content)
    entries = []
    ns = "{http://www.w3.org/2005/Atom}"
    for entry in root.findall(f"{ns}entry"):
        title_el = entry.find(f"{ns}title")
        link_el = entry.find(f"{ns}link")
        if title_el is None or link_el is None:
            continue
        title = (title_el.text or "").strip()
        href = link_el.get("href", "")
        if href:
            entries.append((title, href))
    return entries


def download_via_atom(
    day: date,
    target_dir: Path,
    *,
    feed_url: Optional[str] = None,
) -> Optional[Path]:
    """
    Stáhne ``ZKSH`` soubor pro daný den přes ATOM feed (fallback k deterministické URL).

    Hledá v ATOM feedu položku, jejíž URL obsahuje očekávaný název souboru
    (``<YYYYMMDD>_ST_ZKSH.xml.zip``). Pokud taková položka neexistuje, vrací
    ``None``.

    :param day: Den platnosti.
    :param target_dir: Cílový adresář.
    :param feed_url: Volitelný override ATOM feedu (jinak se vezme
        ``atom_feed_url`` z :class:`CustomAdminSettings`).

        :return: Cesta ke staženému souboru nebo ``None``.
    """
    feed = feed_url or _get_setting("atom_feed_url")
    expected_filename = _change_filename(day)
    for _title, href in _parse_atom_feed(feed):
        if expected_filename in href:
            target_path = Path(target_dir) / expected_filename
            return _stream_to_file(href, target_path)
    logger.debug(
        "heslar.ruian_sync.vfr_download.download_via_atom.not_found",
        extra={"day": day.isoformat(), "expected": expected_filename},
    )
    return None
