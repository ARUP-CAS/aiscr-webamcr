"""
Aplikace dat ze zdroje RÚIAN na DB heslářů (kraj/okres/katastr).

Vystavuje dvě veřejné funkce:

* :func:`sync_full` – aplikuje úplný stav z stavového VFR souboru;
* :func:`sync_delta` – aplikuje denní změny pro jeden konkrétní den.

Obě funkce zapisují průběh do předaného :class:`heslar.models.RuianSyncRun`
(pole ``*_upserts``, ``*_deletes``, ``affected_*``, ``status``,
``finished_at``, případně ``error``). Vlastní DB operace probíhají
v krátkých transakcích nad jednotlivými prvky, signály v ``heslar/signals.py``
zajistí zápis do Fedora repozitáře.

* **Existující prvek** (kraj/okres/katastr s existujícím ``kod``) – aktualizuje
  pouze pole, která se reálně liší. EN název se přepisuje **jen tehdy, je-li
  v DB prázdný**.
* **Změna geometrie katastru** – aktualizuje ``hranice``/``definicni_bod``
  a vyprázdní ``katastr.pian`` (FK ``pian_id`` → NULL). Sám PIAN zůstává.
* **Přejmenování katastru** – propíše záznam do historie všech navázaných
  Projekt/AZ/SN s ``typ_zmeny=ZMENA_KATASTRU`` a aktualizuje Fedoru;
  NeidentAkce nemá vlastní historii, ale Fedora se aktualizuje také.
* **Smazání katastru** – nejprve přepočítá příslušnost všech navázaných
  Projekt/AZ/SN/NeidentAkce (modul :mod:`heslar.ruian_sync.reassign`),
  pak teprve katastr smaže.
* **Nový prvek** – založí jako nový záznam.
"""

from __future__ import annotations

import logging
import traceback
from datetime import date
from typing import Iterable, Optional, Set, Tuple

from arch_z.models import ArcheologickyZaznam
from core.repository_connector import FedoraError, FedoraTransaction, FedoraTransactionCommitFailedError
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException
from django.db import connection, transaction
from django.db.models import Q
from django.db.models.deletion import RestrictedError
from heslar.models import RuianKatastr, RuianKraj, RuianOkres, RuianSyncRun
from heslar.ruian_sync import reassign as reassign_mod
from heslar.ruian_sync.provider import (
    EVENT_DELETE,
    EVENT_UPSERT,
    LEVEL_KATASTR,
    LEVEL_KRAJ,
    LEVEL_OKRES,
    RuianChangeEvent,
    RuianFullState,
    RuianKatastrDTO,
    RuianKrajDTO,
    RuianOkresDTO,
    RuianSource,
)
from neidentakce.models import NeidentAkce
from pas.models import SamostatnyNalez
from projekt.models import Projekt

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Veřejné API
# ---------------------------------------------------------------------------


def sync_full(
    source: RuianSource,
    run: RuianSyncRun,
) -> None:
    """
    Aplikuje úplný stav z VFR zdroje na DB heslářů RÚIAN.

    Provede diff proti databázi a aplikuje upserty a smazání v pořadí
    kraj → okres → katastr (kvůli FK závislostem). Výsledek
    zapíše do předaného :class:`RuianSyncRun`.

    :param source: Implementace :class:`RuianSource`, typicky :class:`ShpUzszSource`.
    :param run: Záznam o průběhu, do kterého se zapisují countery.
    :raises Exception: Propaguje výjimku ze zdroje nebo z DB; volající (management
        command) zachytí, zaloguje do ``run.error`` a označí běh jako ``failed``.
    """
    logger.debug("heslar.ruian_sync.syncer.sync_full.start", extra={"run_id": run.pk})

    state = source.fetch_full_state()
    try:
        _apply_full_state(state, run)
    except Exception:
        logger.error(
            "heslar.ruian_sync.syncer.sync_full.error",
            extra={"run_id": run.pk, "traceback": traceback.format_exc()},
        )
        raise

    logger.debug("heslar.ruian_sync.syncer.sync_full.end", extra={"run_id": run.pk})


def sync_delta(
    source: RuianSource,
    run: RuianSyncRun,
    day: date,
    *,
    reassign_records: bool = False,
) -> None:
    """
    Aplikuje denní změnový VFR pro jeden konkrétní den.

    Pokud ``reassign_records=True``, po aplikaci dat se navíc spustí
    **cílený spatial reassign** Projekt/AZ/SN, jejichž přiřazení katastru
    mohla daný den ovlivnit změna hranice. Iteruje **jen kandidáty**
    (záznamy ukazující na změněný katastr nebo s geometrií protínající
    jeho novou hranici) – ne celou DB, viz
    :func:`_reassign_records_in_changed_katastry`.

    :param source: Implementace :class:`RuianSource`, typicky :class:`FileVfrSource`.
    :param run: Záznam o průběhu, do kterého se zapisují countery.
    :param day: Den, ke kterému jsou změny v ``source`` platné.
    :param reassign_records: Pokud ``True``, po aplikaci změn proběhne
        spatial reassign Projekt/AZ/SN dotčených změnami hranic (přepočet
        katastru, zápis do historie, aktualizace Fedory). Default ``False``
        – navázané záznamy se nepřepočítávají.
    :raises Exception: Propaguje výjimku zdroje/DB.
    """
    logger.debug(
        "heslar.ruian_sync.syncer.sync_delta.start",
        extra={"run_id": run.pk, "day": day.isoformat(), "reassign_records": reassign_records},
    )

    try:
        hranice_changed_kody = _apply_changes(source.fetch_changes(day), run)
    except Exception:
        logger.error(
            "heslar.ruian_sync.syncer.sync_delta.error",
            extra={"run_id": run.pk, "traceback": traceback.format_exc()},
        )
        raise

    if reassign_records and hranice_changed_kody:
        try:
            _reassign_records_in_changed_katastry(hranice_changed_kody, run)
        except Exception as err:  # noqa: BLE001
            # Reassign chyba nesmí zhatit přijetí denních dat – už jsme
            # úspěšně aplikovali upserty/delete katastrů. Detail jde
            # do run.note + log; další pokus může uživatel udělat ručně
            # přes reassign_all nebo /admin/update-katastry/.
            logger.warning(
                "heslar.ruian_sync.syncer.sync_delta.reassign_failed",
                extra={"run_id": run.pk, "error": str(err)[:500]},
            )
            _append_run_note(run, f"Reassign po hranice change selhal: {err}")
            run.save(update_fields=["note"])

    logger.debug("heslar.ruian_sync.syncer.sync_delta.end", extra={"run_id": run.pk})


# ---------------------------------------------------------------------------
# Vnitřní logika – plný sync
# ---------------------------------------------------------------------------


def _apply_full_state(
    state: RuianFullState,
    run: RuianSyncRun,
) -> None:
    """
    Aplikuje plný stav (upserty + delete) ve dvou fázích.

    **Fáze 1 – upserty** v pořadí kraj → okres → katastr (zaručí, že nadřazený
    prvek existuje, než dítě upraví svůj FK). Při této fázi se vazby
    (``RuianOkres.kraj``, ``RuianKatastr.okres``) přesměrují na nové záznamy
    nebo zůstanou na stávajících podle dat ze zdroje.

    **Fáze 2 – delete** v reverzním pořadí katastr → okres → kraj (zaručí, že
    při mazání nadřazené úrovně už na ni žádný potomek neukazuje). Mazání
    katastru navíc obsahuje reassign navázaných Projekt/AZ/SN/NeidentAkce,
    viz :func:`_delete_katastr`.

    :param state: Plný stav prvků RÚIAN.
    :param run: Audit záznam, do kterého se zapisují countery.
    """
    # ---- Fáze 1: upserty (kraj → okres → katastr) ----
    print("Fáze 1 – upsert (kraj → okres → katastr)", flush=True)

    db_kraje = {k.kod: k for k in RuianKraj.objects.all()}
    state_kraj_codes = set()
    total_kraje = len(state.kraje)
    _print_section("Upsert krajů", total_kraje)
    last_pct = 0
    for i, kraj_dto in enumerate(state.kraje, 1):
        state_kraj_codes.add(kraj_dto.kod)
        if _upsert_kraj(db_kraje.get(kraj_dto.kod), kraj_dto):
            run.kraj_upserts += 1
        last_pct = _print_progress("kraj upsert", i, total_kraje, last_pct)

    db_okresy = {o.kod: o for o in RuianOkres.objects.select_related("kraj").all()}
    state_okres_codes = set()
    total_okresy = len(state.okresy)
    _print_section("Upsert okresů", total_okresy)
    last_pct = 0
    for i, okres_dto in enumerate(state.okresy, 1):
        state_okres_codes.add(okres_dto.kod)
        if _upsert_okres(db_okresy.get(okres_dto.kod), okres_dto):
            run.okres_upserts += 1
        last_pct = _print_progress("okres upsert", i, total_okresy, last_pct)

    # Existující katastry: načítáme jen ``kod`` (bez geometrií ``hranice``/
    # ``definicni_bod``), abychom se vyhnuli jednomu obřímu SELECTu, který
    # překračoval PostgreSQL ``statement_timeout``. Plný záznam se pak dotahuje
    # cíleně pro každý dotčený ``kod`` v rámci smyčky.
    db_katastr_codes = set(RuianKatastr.objects.values_list("kod", flat=True))
    state_katastr_codes = set()
    total_katastry = len(state.katastry)
    _print_section("Upsert katastrů", total_katastry)
    last_pct = 0
    for i, katastr_dto in enumerate(state.katastry, 1):
        state_katastr_codes.add(katastr_dto.kod)
        existing_katastr = (
            RuianKatastr.objects.select_related("okres").filter(kod=katastr_dto.kod).first()
            if katastr_dto.kod in db_katastr_codes
            else None
        )
        changed, _hranice_changed = _upsert_katastr(existing_katastr, katastr_dto, run)
        if changed:
            run.katastr_upserts += 1
        last_pct = _print_progress("katastr upsert", i, total_katastry, last_pct)

    # ---- Fáze 2: delete (katastr → okres → kraj, reverzně dle FK) ----
    print("Fáze 2 – delete (katastr → okres → kraj)", flush=True)

    # Bezpečnostní pojistka: pokud zdroj NEPOSKYTL žádné prvky dané úrovně
    # (typicky chybí ST_UKSH soubor v adresáři při OB_UKSH módu), syncer
    # NEMAŽE existující záznamy v DB. Prázdná úroveň znamená „nemám data
    # pro tuto úroveň" (≠ „v RÚIAN nic není"). Skip se zaloguje do
    # ``run.note``, aby si operátor všiml.
    if state.katastry:
        to_delete = sorted(db_katastr_codes - state_katastr_codes)
        total_del = len(to_delete)
        _print_section("Mazání chybějících katastrů", total_del)
        last_pct = 0
        for i, kod in enumerate(to_delete, 1):
            katastr_to_delete = RuianKatastr.objects.select_related("okres").filter(kod=kod).first()
            if katastr_to_delete is None:
                continue
            if _delete_katastr(katastr_to_delete, run):
                run.katastr_deletes += 1
            last_pct = _print_progress("katastr delete", i, total_del, last_pct)
    else:
        _append_run_note(run, "Mazání katastrů přeskočeno: zdroj neposkytl žádné KU.")
        logger.warning("heslar.ruian_sync.syncer._apply_full_state.skip_katastr_delete")

    if state.okresy:
        # Načteme okresy znovu (FK z katastrů na ně už nemíří – byly smazány nebo přesměrovány)
        db_okresy = {o.kod: o for o in RuianOkres.objects.all()}
        to_delete = sorted(set(db_okresy) - state_okres_codes)
        total_del = len(to_delete)
        _print_section("Mazání chybějících okresů", total_del)
        last_pct = 0
        for i, kod in enumerate(to_delete, 1):
            if _delete_okres(db_okresy[kod], run):
                run.okres_deletes += 1
            last_pct = _print_progress("okres delete", i, total_del, last_pct)
    else:
        _append_run_note(run, "Mazání okresů přeskočeno: zdroj neposkytl žádné okresy (chybí ST_UKSH?).")
        logger.warning("heslar.ruian_sync.syncer._apply_full_state.skip_okres_delete")

    if state.kraje:
        # Načteme kraje znovu (vazby z okresů by už měly směřovat na zachovávané kraje)
        db_kraje = {k.kod: k for k in RuianKraj.objects.all()}
        to_delete = sorted(set(db_kraje) - state_kraj_codes)
        total_del = len(to_delete)
        _print_section("Mazání chybějících krajů", total_del)
        last_pct = 0
        for i, kod in enumerate(to_delete, 1):
            if _delete_kraj(db_kraje[kod], run):
                run.kraj_deletes += 1
            last_pct = _print_progress("kraj delete", i, total_del, last_pct)
    else:
        _append_run_note(run, "Mazání krajů přeskočeno: zdroj neposkytl žádné kraje (chybí ST_UKSH?).")
        logger.warning("heslar.ruian_sync.syncer._apply_full_state.skip_kraj_delete")

    run.save()


# ---------------------------------------------------------------------------
# Vnitřní logika – inkrementální sync
# ---------------------------------------------------------------------------


def _apply_changes(events: Iterable[RuianChangeEvent], run: RuianSyncRun) -> Set[int]:
    """
    Aplikuje sekvenci :class:`RuianChangeEvent` na DB ve dvou fázích.

    **Fáze 1 – upserty** v pořadí kraj → okres → katastr (vazby se přesměrují
    na existující/nově vytvořené záznamy).

    **Fáze 2 – delete** v reverzním pořadí katastr → okres → kraj (zaručí,
    že na mazaný prvek už nemíří žádný RESTRICT FK).

    Návratová hodnota dává volajícímu (typicky :func:`sync_delta`) informaci,
    kterých katastrů se **změnila hranice** – ta sada je nutná pro následný
    spatial reassign navázaných Projekt/AZ/SN (viz parametr
    ``reassign_records`` v :func:`sync_delta`).

    :param events: Iterable událostí ze změnového VFR.
    :param run: Audit záznam, do kterého se zapisují countery.

        :return: Množina ``kod`` katastrů, u kterých došlo ke změně polygonu
            ``hranice`` (= kandidáti pro spatial reassign). Mazané katastry
            ve výsledku **nejsou** – ty řeší ``_delete_katastr`` přímo.
    """
    # Setříděné batche podle úrovně, abychom neporušili FK pořadí
    bucket = {LEVEL_KRAJ: [], LEVEL_OKRES: [], LEVEL_KATASTR: []}
    for ev in events:
        if ev.level not in bucket:
            logger.warning("heslar.ruian_sync.syncer._apply_changes.unknown_level", extra={"level": ev.level})
            continue
        bucket[ev.level].append(ev)

    # ---- Fáze 1: upserty (kraj → okres → katastr) ----
    db_kraje = {k.kod: k for k in RuianKraj.objects.all()}
    for ev in bucket[LEVEL_KRAJ]:
        if ev.event_type == EVENT_UPSERT:
            if _upsert_kraj(db_kraje.get(ev.kod), ev.payload):
                run.kraj_upserts += 1

    db_okresy = {o.kod: o for o in RuianOkres.objects.all()}
    for ev in bucket[LEVEL_OKRES]:
        if ev.event_type == EVENT_UPSERT:
            if _upsert_okres(db_okresy.get(ev.kod), ev.payload):
                run.okres_upserts += 1

    hranice_changed_kody: Set[int] = set()
    db_katastry = {k.kod: k for k in RuianKatastr.objects.all()}
    for ev in bucket[LEVEL_KATASTR]:
        if ev.event_type == EVENT_UPSERT:
            changed, hranice_changed = _upsert_katastr(db_katastry.get(ev.kod), ev.payload, run)
            if changed:
                run.katastr_upserts += 1
            if hranice_changed:
                hranice_changed_kody.add(ev.kod)

    # ---- Fáze 2: delete (katastr → okres → kraj, reverzně dle FK) ----
    db_katastry = {k.kod: k for k in RuianKatastr.objects.all()}
    for ev in bucket[LEVEL_KATASTR]:
        if ev.event_type == EVENT_DELETE and ev.kod in db_katastry:
            if _delete_katastr(db_katastry[ev.kod], run):
                run.katastr_deletes += 1

    db_okresy = {o.kod: o for o in RuianOkres.objects.all()}
    for ev in bucket[LEVEL_OKRES]:
        if ev.event_type == EVENT_DELETE and ev.kod in db_okresy:
            if _delete_okres(db_okresy[ev.kod], run):
                run.okres_deletes += 1

    db_kraje = {k.kod: k for k in RuianKraj.objects.all()}
    for ev in bucket[LEVEL_KRAJ]:
        if ev.event_type == EVENT_DELETE and ev.kod in db_kraje:
            if _delete_kraj(db_kraje[ev.kod], run):
                run.kraj_deletes += 1

    run.save()
    return hranice_changed_kody


# ---------------------------------------------------------------------------
# Upserty / mazání jednotlivých úrovní
# ---------------------------------------------------------------------------


@transaction.atomic
def _upsert_kraj(existing: Optional[RuianKraj], dto: RuianKrajDTO) -> bool:
    """
    Vytvoří nebo aktualizuje :class:`RuianKraj`.

    :param existing: Stávající záznam v DB nebo ``None``.
    :param dto: Nová data ze zdroje.

        :return: ``True`` pokud došlo k vytvoření nebo skutečné změně, jinak ``False``.
    """
    if existing is None:
        kraj = RuianKraj(
            kod=dto.kod,
            nazev=dto.nazev,
            rada_id=dto.rada_id or "",
            nazev_en=dto.nazev_en or dto.nazev,
            definicni_bod=_geos_or_none(dto.definicni_bod_wkt),
            hranice=_geos_or_none(dto.hranice_wkt),
        )
        kraj.save()
        return True

    changed = False
    if existing.nazev != dto.nazev:
        existing.nazev = dto.nazev
        changed = True
    if dto.rada_id and existing.rada_id != dto.rada_id:
        existing.rada_id = dto.rada_id
        changed = True
    # EN název doplnit jen pokud je v DB prázdný
    new_en = dto.nazev_en if dto.nazev_en else dto.nazev
    if not existing.nazev_en and new_en:
        existing.nazev_en = new_en
        changed = True
    new_db = _geos_or_none(dto.definicni_bod_wkt)
    if new_db is not None and existing.definicni_bod != new_db:
        existing.definicni_bod = new_db
        changed = True
    new_hr = _geos_or_none(dto.hranice_wkt)
    if new_hr is not None and existing.hranice != new_hr:
        existing.hranice = new_hr
        changed = True
    if changed:
        existing.save()
    return changed


def _delete_kraj(kraj: RuianKraj, run: Optional[RuianSyncRun] = None) -> bool:
    """
    Smaže :class:`RuianKraj`. FK z okresů je RESTRICT, takže předpokládá,
    že žádný okres na něj už neukazuje (mazání by mělo proběhnout po okresech
    – viz :func:`_apply_full_state` / :func:`_apply_changes`).

    Pokud přesto na kraj ukazují okresy (typicky historické záznamy, které
    syncer ignoruje a nechává v DB), záznam neumažeme a pokračujeme dál; výpis
    bude v ``run.note``.

    :param kraj: Záznam ke smazání.
    :param run: Audit záznam pro zápis do ``note``; volitelný (zachovává API).

        :return: ``True`` pokud bylo smazáno, jinak ``False``.
    """
    logger.debug("heslar.ruian_sync.syncer._delete_kraj", extra={"kod": kraj.kod})
    try:
        with transaction.atomic():
            kraj.delete()
    except RestrictedError as err:
        logger.warning(
            "heslar.ruian_sync.syncer._delete_kraj.restricted",
            extra={"kod": kraj.kod, "nazev": kraj.nazev, "error": str(err)},
        )
        if run is not None:
            _append_run_note(run, f"Kraj {kraj.kod} ({kraj.nazev}) nelze smazat: {err}")
        return False
    except FedoraError as err:
        # DB delete proběhl, jen Fedora kontejner neexistoval (viz _delete_katastr).
        logger.warning(
            "heslar.ruian_sync.syncer._delete_kraj.fedora_error",
            extra={"kod": kraj.kod, "nazev": kraj.nazev, "error": str(err)},
        )
        if run is not None:
            _append_run_note(
                run,
                f"Kraj {kraj.kod} ({kraj.nazev}) smazán z DB, " f"Fedora kontejner nenalezen: {err}",
            )
        return True
    return True


@transaction.atomic
def _upsert_okres(existing: Optional[RuianOkres], dto: RuianOkresDTO) -> bool:
    """
    Vytvoří nebo aktualizuje :class:`RuianOkres`.

    :param existing: Stávající záznam nebo ``None``.
    :param dto: Nová data.

        :return: ``True`` při vytvoření nebo změně, jinak ``False``.
    """
    kraj = RuianKraj.objects.filter(kod=dto.kraj_kod).first()
    if existing is None:
        if kraj is None:
            logger.error(
                "heslar.ruian_sync.syncer._upsert_okres.missing_kraj",
                extra={"okres_kod": dto.kod, "kraj_kod": dto.kraj_kod},
            )
            return False
        okres = RuianOkres(
            kod=dto.kod,
            nazev=dto.nazev,
            kraj=kraj,
            spz=dto.spz or "",
            nazev_en=dto.nazev_en or dto.nazev,
            definicni_bod=_geos_or_none(dto.definicni_bod_wkt),
            hranice=_geos_or_none(dto.hranice_wkt),
        )
        okres.save()
        return True

    changed = False
    if existing.nazev != dto.nazev:
        existing.nazev = dto.nazev
        changed = True
    if kraj is not None and existing.kraj_id != kraj.id:
        existing.kraj = kraj
        changed = True
    if dto.spz and existing.spz != dto.spz:
        existing.spz = dto.spz
        changed = True
    new_en = dto.nazev_en if dto.nazev_en else dto.nazev
    if not existing.nazev_en and new_en:
        existing.nazev_en = new_en
        changed = True
    new_db = _geos_or_none(dto.definicni_bod_wkt)
    if new_db is not None and existing.definicni_bod != new_db:
        existing.definicni_bod = new_db
        changed = True
    new_hr = _geos_or_none(dto.hranice_wkt)
    if new_hr is not None and existing.hranice != new_hr:
        existing.hranice = new_hr
        changed = True
    if changed:
        existing.save()
    return changed


def _delete_okres(okres: RuianOkres, run: Optional[RuianSyncRun] = None) -> bool:
    """
    Smaže :class:`RuianOkres`. Předpokládá, že už na něj neukazuje žádný katastr.

    Pokud RESTRICT FK delete zablokuje (typicky stále existující katastry, které
    nebylo možno přepsat během reassignu), záznam ponecháme a pokračujeme dál;
    detail bude v ``run.note``.

    :param okres: Záznam ke smazání.
    :param run: Audit záznam pro zápis do ``note``; volitelný.

        :return: ``True`` pokud bylo smazáno, jinak ``False``.
    """
    logger.debug("heslar.ruian_sync.syncer._delete_okres", extra={"kod": okres.kod})
    try:
        with transaction.atomic():
            okres.delete()
    except RestrictedError as err:
        logger.warning(
            "heslar.ruian_sync.syncer._delete_okres.restricted",
            extra={"kod": okres.kod, "nazev": okres.nazev, "error": str(err)},
        )
        if run is not None:
            _append_run_note(run, f"Okres {okres.kod} ({okres.nazev}) nelze smazat: {err}")
        return False
    except FedoraError as err:
        # DB delete proběhl, jen Fedora kontejner neexistoval (viz _delete_katastr).
        logger.warning(
            "heslar.ruian_sync.syncer._delete_okres.fedora_error",
            extra={"kod": okres.kod, "nazev": okres.nazev, "error": str(err)},
        )
        if run is not None:
            _append_run_note(
                run,
                f"Okres {okres.kod} ({okres.nazev}) smazán z DB, " f"Fedora kontejner nenalezen: {err}",
            )
        return True
    return True


@transaction.atomic
def _upsert_katastr(
    existing: Optional[RuianKatastr],
    dto: RuianKatastrDTO,
    run: RuianSyncRun,
) -> Tuple[bool, bool]:
    """
    Vytvoří nebo aktualizuje :class:`RuianKatastr`.

    Při změně názvu propíše záznam do historie navázaných Projekt/AZ/SN
    a aktualizuje Fedoru pro Projekt/AZ/SN/NeidentAkce.
    Při změně geometrie vyprázdní FK ``pian`` (PIAN samotný zůstává).

    :param existing: Stávající záznam nebo ``None``.
    :param dto: Nová data.
    :param run: Audit záznam (countery se zde inkrementují u ``affected_*``).

    :return: Dvojice ``(changed, hranice_changed)``. ``changed`` značí,
        že proběhl insert/update (libovolné pole), ``hranice_changed`` je
        ``True`` pouze pokud došlo ke změně polygonu ``hranice`` (= klíčová
        informace pro následný spatial reassign navázaných Projekt/AZ/SN).
        U vytvoření nového katastru je ``hranice_changed=True`` (nová
        hranice se objevuje v DB).
    """
    okres = RuianOkres.objects.filter(kod=dto.okres_kod).first()
    if existing is None:
        if okres is None:
            logger.error(
                "heslar.ruian_sync.syncer._upsert_katastr.missing_okres",
                extra={"katastr_kod": dto.kod, "okres_kod": dto.okres_kod},
            )
            return (False, False)
        katastr = RuianKatastr(
            kod=dto.kod,
            nazev=dto.nazev,
            okres=okres,
            definicni_bod=_geos_or_none(dto.definicni_bod_wkt),
            hranice=_geos_or_none(dto.hranice_wkt),
        )
        katastr.save()
        return (True, True)

    changed = False
    name_changed = False
    hranice_changed = False
    old_nazev = existing.nazev

    if existing.nazev != dto.nazev:
        existing.nazev = dto.nazev
        changed = True
        name_changed = True
    if okres is not None and existing.okres_id != okres.id:
        existing.okres = okres
        changed = True

    new_db = _geos_or_none(dto.definicni_bod_wkt)
    new_hr = _geos_or_none(dto.hranice_wkt)
    geometry_changed = False
    if new_db is not None and existing.definicni_bod != new_db:
        existing.definicni_bod = new_db
        geometry_changed = True
        changed = True
    if new_hr is not None and existing.hranice != new_hr:
        existing.hranice = new_hr
        geometry_changed = True
        hranice_changed = True
        changed = True

    if geometry_changed:
        existing.pian = None  # FK pian_id → NULL, samotný PIAN zůstává

    if changed:
        existing.save()

    if name_changed:
        affected = _log_katastr_rename(existing, old_nazev=old_nazev, new_nazev=dto.nazev)
        run.affected_projekt += affected.get("projekt", 0)
        run.affected_az += affected.get("az", 0)
        run.affected_sn += affected.get("sn", 0)
        run.affected_neident_akce += affected.get("neident_akce", 0)

    return (changed, hranice_changed)


# ---------------------------------------------------------------------------
# Cílený spatial reassign po denní změně hranic
# ---------------------------------------------------------------------------


#: SQL kandidátů Projekt: projekty s vyplněným ``geom``, které buď ukazují
#: na změněný katastr přes ``hlavni_katastr`` FK, nebo jejich bod nově padá
#: do polygonu změněného katastru (nově by tam patřily). Spatial index nad
#: ``hranice`` zajistí, že join je rychlý i pro velké sady projektů.
_SQL_PROJEKT_CANDIDATES = """
    SELECT DISTINCT p.id
    FROM projekt p
    JOIN ruian_katastr k ON k.kod = ANY(%s::int[])
    WHERE p.geom IS NOT NULL
      AND (p.hlavni_katastr = k.id OR ST_Intersects(k.hranice, p.geom))
"""

#: SQL kandidátů AZ: AZ ukazující ``hlavni_katastr`` na změněný katastr
#: NEBO mající alespoň jednu DJ s PIANem, který nově protíná hranici
#: změněného katastru.
_SQL_AZ_CANDIDATES = """
    SELECT DISTINCT az.id
    FROM archeologicky_zaznam az
    JOIN ruian_katastr k ON k.kod = ANY(%s::int[])
    WHERE az.hlavni_katastr = k.id
       OR EXISTS (
           SELECT 1
           FROM dokumentacni_jednotka dj
           JOIN pian p ON dj.pian = p.id
           WHERE dj.archeologicky_zaznam = az.id
             AND p.geom IS NOT NULL
             AND ST_Intersects(k.hranice, p.geom)
       )
"""

#: SQL kandidátů SN: SN s vyplněným ``geom`` ukazující na změněný katastr
#: nebo jehož bod nově padá do polygonu změněného katastru.
_SQL_SN_CANDIDATES = """
    SELECT DISTINCT s.id
    FROM samostatny_nalez s
    JOIN ruian_katastr k ON k.kod = ANY(%s::int[])
    WHERE s.geom IS NOT NULL
      AND (s.katastr = k.id OR ST_Intersects(k.hranice, s.geom))
"""


def _reassign_records_in_changed_katastry(
    kody: Set[int],
    run: RuianSyncRun,
) -> None:
    """
    Cílený spatial reassign Projekt/AZ/SN dotčených změnou hranic katastrů.

    Strategie pro výkon (jádro problému *„jak najít dotčené piany,
    aniž bych procházel všechny záznamy"*):

    1. Sada ``kody`` katastrů, které **se v tomhle dni změnily** (hranice),
       je typicky desítky až nízké stovky kódů – nikoliv tisíce.
    2. Pro každou entitu se spustí **jedna** SQL query, která:

       * joinuje záznam s ``ruian_katastr`` jen přes ``kod = ANY(<changed>)``
         – mizivá pravá tabulka;
       * filtrem ``record.hlavni_katastr = k.id`` nachytá staré přiřazení;
       * filtrem ``ST_Intersects(k.hranice, record.geom)`` (resp. ``pian.geom``
         u AZ) nachytá nové přiřazení (pian nově padá do změněné hranice).

       Spatial index nad ``ruian_katastr.hranice`` / ``pian.geom`` udělá ze
       ST_Intersects rychlou operaci.

    3. Na **jen** vrácených kandidátech se zavolá ``reassign_*`` – reassign
       funkce uvnitř udělá další porovnání (např. ``_update_az_katastry_if_changed``
       skipne save, pokud se reálně nic nemění).

    NeidentAkce do reassignu vůbec nezahrnujeme – nemá vlastní geometrii;
    při změně hranice (nikoli delete) zůstává anchored na svůj katastr.

    Outputy: countery ``run.affected_projekt`` / ``_az`` / ``_sn`` se navýší
    o počet záznamů, kterým se reálně změnil katastr (vs. záznamy, kde
    reassign zjistil unchanged).

    :param kody: Množina kódů katastrů, jejichž hranice se v tomhle delta
        změnila (vrací :func:`_apply_changes`).
    :param run: Audit záznam – navyšují se ``affected_*`` countery
        a poznámka ``note`` při chybě.
    """
    if not kody:
        return

    kody_list = list(kody)
    logger.debug(
        "heslar.ruian_sync.syncer._reassign_records_in_changed_katastry.start",
        extra={"changed_kody_count": len(kody_list)},
    )
    print(
        f"Cílený reassign po změně hranic: {len(kody_list)} změněných katastrů",
        flush=True,
    )

    # Prostorové dotazy pro každý kandidátní záznam mohou přesáhnout globální
    # statement_timeout (90 s). Reassign je batch operace – timeout vypínáme
    # lokálně pro tuto session a obnovíme ho po dokončení.
    with connection.cursor() as _cur:
        _cur.execute("SET statement_timeout = 0")
    try:
        _reassign_records_in_changed_katastry_inner(kody_list, run)
    finally:
        with connection.cursor() as _cur:
            _cur.execute("RESET statement_timeout")


def _reassign_records_in_changed_katastry_inner(kody_list: list, run: RuianSyncRun) -> None:
    # --- Projekt ---
    with connection.cursor() as cursor:
        cursor.execute(_SQL_PROJEKT_CANDIDATES, [kody_list])
        projekt_ids = [row[0] for row in cursor.fetchall()]
    print(f"  Projekt kandidátů: {len(projekt_ids)}", flush=True)
    for projekt in Projekt.objects.filter(pk__in=projekt_ids).select_related("hlavni_katastr"):
        old_pk = projekt.hlavni_katastr_id
        try:
            new_kat = reassign_mod.reassign_projekt(projekt)
        except (FedoraError, FedoraTransactionCommitFailedError, ValueError) as err:
            logger.warning(
                "heslar.ruian_sync.syncer._reassign_records_in_changed_katastry.projekt_error",
                extra={"ident_cely": projekt.ident_cely, "error": str(err)[:500]},
            )
            continue
        if new_kat is not None and new_kat.pk != old_pk:
            run.affected_projekt += 1

    # --- AZ ---
    with connection.cursor() as cursor:
        cursor.execute(_SQL_AZ_CANDIDATES, [kody_list])
        az_ids = [row[0] for row in cursor.fetchall()]
    print(f"  AZ kandidátů:      {len(az_ids)}", flush=True)
    for az in ArcheologickyZaznam.objects.filter(pk__in=az_ids).select_related("hlavni_katastr"):
        old_pk = az.hlavni_katastr_id
        try:
            new_kat = reassign_mod.reassign_az(
                az,
                fallback_point=az.hlavni_katastr.definicni_bod if az.hlavni_katastr else None,
            )
        except (FedoraError, FedoraTransactionCommitFailedError, ValueError) as err:
            logger.warning(
                "heslar.ruian_sync.syncer._reassign_records_in_changed_katastry.az_error",
                extra={"ident_cely": az.ident_cely, "error": str(err)[:500]},
            )
            continue
        if new_kat is not None and new_kat.pk != old_pk:
            run.affected_az += 1

    # --- SN ---
    with connection.cursor() as cursor:
        cursor.execute(_SQL_SN_CANDIDATES, [kody_list])
        sn_ids = [row[0] for row in cursor.fetchall()]
    print(f"  SN kandidátů:      {len(sn_ids)}", flush=True)
    for sn in SamostatnyNalez.objects.filter(pk__in=sn_ids).select_related("katastr"):
        old_pk = sn.katastr_id
        try:
            new_kat = reassign_mod.reassign_sn(sn)
        except (FedoraError, FedoraTransactionCommitFailedError, ValueError) as err:
            logger.warning(
                "heslar.ruian_sync.syncer._reassign_records_in_changed_katastry.sn_error",
                extra={"ident_cely": sn.ident_cely, "error": str(err)[:500]},
            )
            continue
        if new_kat is not None and new_kat.pk != old_pk:
            run.affected_sn += 1

    run.save(update_fields=["affected_projekt", "affected_az", "affected_sn"])
    logger.debug("heslar.ruian_sync.syncer._reassign_records_in_changed_katastry.end")


def _delete_katastr(
    katastr: RuianKatastr,
    run: RuianSyncRun,
) -> bool:
    """
    Přepočítá příslušnost všech navázaných záznamů na nový katastr a původní smaže.

    Pořadí:

    1. Projekt: union query (hlavni_katastr nebo M2M) → ``reassign_projekt``
       pro hlavní katastr + ``reassign_projekt_dalsi_katastr`` pro M2M;
       oba kroky zapisují do Historie a aktualizují Fedoru.
    2. AZ: union query → ``reassign_az`` přepočítá v jednom průchodu
       ``hlavni_katastr`` i M2M; Historie a Fedora jsou řešeny uvnitř
       ``reassign_az`` resp. ``_update_az_katastry_if_changed``.
    3. SN/NeidentAkce: přepočítá FK katastr.
    4. Smaže :class:`RuianKatastr` (signál odstraní kontejner ve Fedoře).

    PIAN navázaný na katastr (``RuianKatastr.pian``) **se neměří** – zůstává.

    :param katastr: Záznam ke smazání.
    :param run: Audit záznam (countery ``affected_*``).

        :return: ``True`` pokud byl katastr smazán.
    """
    logger.debug("heslar.ruian_sync.syncer._delete_katastr.start", extra={"kod": katastr.kod})
    fallback_point = katastr.definicni_bod  # bod původního katastru
    katastr_kod = katastr.kod  # kód mazaného katastru pro vyloučení ze spatial query

    # ---- Projekty: hlavní katastr + M2M dalších katastrů ----
    #
    # Union query zachytí projekty kde mazaný katastr figuruje jako hlavní
    # NEBO jako jeden z dalších (M2M), nebo obojí najednou.
    #
    # reassign_projekt přepočítá pouze hlavni_katastr.
    # reassign_projekt_dalsi_katastr nahradí mazaný katastr v M2M prostorovým
    # náhradníkem, odebere starý záznam a zapíše změnu do Historie.
    affected_projekty = (
        Projekt.objects.filter(Q(hlavni_katastr=katastr) | Q(katastry=katastr))
        .distinct()
        .select_related("hlavni_katastr")
    )
    for projekt in affected_projekty:
        hlavni_was_deleted = projekt.hlavni_katastr_id == katastr.pk
        if hlavni_was_deleted:
            try:
                reassign_mod.reassign_projekt(
                    projekt,
                    fallback_point=fallback_point,
                    exclude_kod=katastr_kod,
                )
            except (FedoraError, FedoraTransactionCommitFailedError, ValueError) as err:
                logger.warning(
                    "heslar.ruian_sync.syncer._delete_katastr.reassign_projekt_fedora_error",
                    extra={"katastr_kod": katastr.kod, "ident_cely": projekt.ident_cely, "error": str(err)[:500]},
                )
                continue
        try:
            reassign_mod.reassign_projekt_dalsi_katastr(
                projekt,
                katastr,
                fallback_point=fallback_point,
                exclude_kod=katastr_kod,
            )
        except (FedoraError, FedoraTransactionCommitFailedError, ValueError) as err:
            logger.warning(
                "heslar.ruian_sync.syncer._delete_katastr.reassign_projekt_dalsi_fedora_error",
                extra={"katastr_kod": katastr.kod, "ident_cely": projekt.ident_cely, "error": str(err)[:500]},
            )
        run.affected_projekt += 1

    # ---- AZ: hlavní katastr + M2M dalších katastrů ----
    #
    # Union query zachytí AZ kde mazaný katastr figuruje jako hlavní NEBO jako
    # jeden z dalších (M2M). reassign_az → _update_az_katastry_if_changed
    # přepočítá obojí v jednom průchodu: hlavni_katastr i M2M sadu, zapíše
    # historii pro M2M přes _log_az_ostatni_change (to_remove obsahuje mazaný
    # katastr, to_add jeho náhradníky). _log_katastr_change se volá navíc
    # jen tehdy, když se měnil i hlavni_katastr.
    #
    # Výjimky kde reassign_az M2M nepřepočítá (AZ s celokatastr DJ nebo bez DJ)
    # jsou edge case; pokud M2M záznam zůstane, katastr.delete() selže s
    # RestrictedError a operátor dostane upozornění přes run.note.
    affected_az = (
        ArcheologickyZaznam.objects.filter(Q(hlavni_katastr=katastr) | Q(katastry=katastr))
        .distinct()
        .select_related("hlavni_katastr")
    )
    for az in affected_az:
        hlavni_was_deleted = az.hlavni_katastr_id == katastr.pk
        try:
            reassign_mod.reassign_az(
                az,
                fallback_point=fallback_point,
                exclude_kod=katastr_kod,
            )
        except (FedoraError, FedoraTransactionCommitFailedError, ValueError) as err:
            logger.warning(
                "heslar.ruian_sync.syncer._delete_katastr.reassign_az_fedora_error",
                extra={"katastr_kod": katastr.kod, "ident_cely": az.ident_cely, "error": str(err)[:500]},
            )
            continue
        run.affected_az += 1

    # SN – FK katastr, historie stejně jako Projekt/AZ
    for sn in SamostatnyNalez.objects.filter(katastr=katastr):
        try:
            reassign_mod.reassign_sn(
                sn,
                fallback_point=fallback_point,
                exclude_kod=katastr_kod,
            )
        except (FedoraError, FedoraTransactionCommitFailedError, ValueError) as err:
            logger.warning(
                "heslar.ruian_sync.syncer._delete_katastr.reassign_sn_fedora_error",
                extra={"katastr_kod": katastr.kod, "ident_cely": sn.ident_cely, "error": str(err)[:500]},
            )
            continue
        run.affected_sn += 1

    # NeidentAkce (FK katastr s RESTRICT, bez vlastní geometrie i bez ident_cely).
    # Spatial query proběhne výhradně z `fallback_point` (definiční bod původního
    # katastru). Fedora zápis řídí `post_save` signál v `neidentakce.signals`,
    # který si vytváří vlastní transakci nad nadřazeným dokumentem.
    for neident_akce in NeidentAkce.objects.filter(katastr=katastr):
        try:
            reassign_mod.reassign_neident_akce(
                neident_akce,
                fallback_point=fallback_point,
                exclude_kod=katastr_kod,
            )
        except (FedoraError, FedoraTransactionCommitFailedError, ValueError) as err:
            logger.warning(
                "heslar.ruian_sync.syncer._delete_katastr.reassign_neident_akce_fedora_error",
                extra={
                    "katastr_kod": katastr.kod,
                    "neident_akce_pk": neident_akce.pk,
                    "error": str(err)[:500],
                },
            )
            continue
        run.affected_neident_akce += 1

    # Po reassignech by FK z Projekt/AZ/SN/NeidentAkce neměl ukazovat na původní katastr.
    # Pokud přesto stále ukazuje (např. reassign vrátil týž katastr, protože spatial
    # query našla daný polygon zpět – fallback_point je definiční bod mazaného
    # katastru a leží v jeho vlastním polygonu), RESTRICT FK delete zablokuje.
    # V tomto případě záznam ponecháme, zalogujeme do run.note a pokračujeme dál
    # – operátor pak uvidí v adminu seznam katastrů, které je potřeba zkontrolovat
    # a vyřešit ručně.
    try:
        katastr.delete()
    except RestrictedError as err:
        logger.warning(
            "heslar.ruian_sync.syncer._delete_katastr.restricted",
            extra={"kod": katastr.kod, "nazev": katastr.nazev, "error": str(err)},
        )
        _append_run_note(run, f"Katastr {katastr.kod} ({katastr.nazev}) nelze smazat: {err}")
        return False
    except FedoraError as err:
        # DB delete proběhl úspěšně (atomic transakce už commitla – pre_delete
        # signál naplánuje record_deletion přes transaction.on_commit, takže
        # výjimka přijde až po commitu). Fedora kontejner pro tento katastr
        # neexistoval (typicky 404 v testovacím prostředí, kde RUIAN záznamy
        # do Fedory nikdy nešly), což pro náš účel znamená "nic ke smazání".
        # Záznam v DB je pryč, sync pokračuje.
        logger.warning(
            "heslar.ruian_sync.syncer._delete_katastr.fedora_error",
            extra={"kod": katastr.kod, "nazev": katastr.nazev, "error": str(err)},
        )
        _append_run_note(
            run,
            f"Katastr {katastr.kod} ({katastr.nazev}) smazán z DB, "
            f"Fedora kontejner nenalezen (404 nebo jiná chyba): {err}",
        )
        return True
    logger.debug("heslar.ruian_sync.syncer._delete_katastr.deleted", extra={"kod": katastr.kod})
    return True


# ---------------------------------------------------------------------------
# Pomocné funkce
# ---------------------------------------------------------------------------


def _geos_or_none(wkt: Optional[str]):
    """
    Převede WKT řetězec na ``GEOSGeometry`` v EPSG:4326, nebo vrátí ``None``.

    Defenzivně chytá :class:`GEOSException` a :class:`ValueError` – pokud GEOS
    odmítne WKT (typicky kvůli neuzavřenému prstenu nebo invalidní topologii
    zděděné z VFR), funkce vrátí ``None``, zaloguje warning a sync pokračuje.
    Konkrétní geometrii prvku tím necháme nezměněnou v DB; popisné údaje
    (název, kódy) se aktualizují normálně.

    :param wkt: WKT reprezentace geometrie nebo ``None``.

        :return: ``GEOSGeometry`` nebo ``None`` (i při chybě parsování).
    """
    if not wkt:
        return None
    try:
        return GEOSGeometry(wkt, srid=4326)
    except (GEOSException, ValueError) as err:
        logger.warning(
            "heslar.ruian_sync.syncer._geos_or_none.invalid_wkt",
            extra={"wkt_prefix": wkt[:120], "wkt_length": len(wkt), "error": str(err)},
        )
        return None


def _append_run_note(run: RuianSyncRun, message: str) -> None:
    """
    Připojí jeden řádek k poli ``RuianSyncRun.note``.

    Použití pro neúspěšné mazání prvků (RESTRICT FK), které nezpůsobí pád
    celého běhu, ale operátor by je měl vidět v adminu.

    :param run: Audit záznam.
    :param message: Text, který se přidá na samostatný řádek do ``note``.
    """
    existing = run.note or ""
    new_note = (existing + "\n" + message).strip() if existing else message
    run.note = new_note
    run.save(update_fields=["note"])


def _print_section(label: str, total: int) -> None:
    """
    Vypíše hlavičku jedné fáze syncu na stdout (pro interaktivní sledování).

    Vytiskne se jen pokud ``total > 0`` – prázdná fáze se přeskočí beze stopy
    v konzoli (info se zaloguje přes standardní logger).

    :param label: Lidsky čitelný popis fáze (např. ``"Fáze 1: upsert katastrů"``).
    :param total: Celkový počet záznamů, které se v této fázi zpracují.
    """
    if total <= 0:
        return
    print(f"  {label} ({total})...", flush=True)


def _print_progress(label: str, current: int, total: int, last_pct: int) -> int:
    """
    Vytiskne řádek progresu na stdout, **pouze pokud** procento vzrostlo o ≥ 1.

    Slouží pro interaktivní sledování dlouho běžících fází (zejména upsert /
    delete katastrů, kterých je řádově 13 000 a běh trvá minuty). Návratová
    hodnota se používá v dalším volání pro throttling – volající si drží
    ``last_pct`` proměnnou.

    Příklad použití::

        last_pct = 0
        total = len(state.katastry)
        for i, dto in enumerate(state.katastry, 1):
            _upsert_katastr(...)
            last_pct = _print_progress("katastr upsert", i, total, last_pct)

    :param label: Krátký popis fáze pro identifikaci v konzoli.
    :param current: Pořadí aktuálně zpracovaného prvku (1-based).
    :param total: Celkový počet prvků k zpracování.
    :param last_pct: Procento, které bylo naposledy vytištěno (0 na začátku).

        :return: Aktuální procento (k uložení do ``last_pct`` pro další volání).
    """
    if total <= 0:
        return last_pct
    pct = int(current * 100 / total)
    if pct > last_pct or current == total:
        print(f"    {label}: {current}/{total} ({pct} %)", flush=True)
        return pct
    return last_pct


def _log_katastr_rename(katastr: RuianKatastr, old_nazev: str, new_nazev: str) -> dict:
    """
    Zapíše záznam do historie a aktualizuje Fedoru pro všechny záznamy
    navázané na přejmenovaný katastr (Projekt, AZ, SN, NeidentAkce).

    :param katastr: Přejmenovaný katastr.
    :param old_nazev: Původní název.
    :param new_nazev: Nový název.

        :return: Slovník s počty dotčených záznamů
            ``{"projekt": int, "az": int, "sn": int, "neident_akce": int}``.
    """
    counts = {"projekt": 0, "az": 0, "sn": 0, "neident_akce": 0}

    for projekt in Projekt.objects.filter(Q(hlavni_katastr=katastr) | Q(katastry=katastr)).distinct():
        reassign_mod._log_katastr_change(projekt.historie_id, old_nazev, new_nazev)
        fedora_tx = FedoraTransaction()
        success = False
        try:
            projekt.active_transaction = fedora_tx
            projekt.save()
            success = True
        except (FedoraError, FedoraTransactionCommitFailedError) as err:
            logger.warning(
                "heslar.ruian_sync.syncer._log_katastr_rename.projekt_fedora_error",
                extra={"ident_cely": projekt.ident_cely, "error": str(err)[:500]},
            )
        finally:
            fedora_tx.mark_transaction_as_closed() if success else fedora_tx.rollback_transaction()
        counts["projekt"] += 1

    for az in ArcheologickyZaznam.objects.filter(Q(hlavni_katastr=katastr) | Q(katastry=katastr)).distinct():
        reassign_mod._log_katastr_change(az.historie_id, old_nazev, new_nazev)
        fedora_tx = FedoraTransaction()
        success = False
        try:
            az.active_transaction = fedora_tx
            az.save()
            success = True
        except (FedoraError, FedoraTransactionCommitFailedError) as err:
            logger.warning(
                "heslar.ruian_sync.syncer._log_katastr_rename.az_fedora_error",
                extra={"ident_cely": az.ident_cely, "error": str(err)[:500]},
            )
        finally:
            fedora_tx.mark_transaction_as_closed() if success else fedora_tx.rollback_transaction()
        counts["az"] += 1

    for sn in SamostatnyNalez.objects.filter(katastr=katastr):
        reassign_mod._log_katastr_change(sn.historie_id, old_nazev, new_nazev)
        fedora_tx = FedoraTransaction()
        success = False
        try:
            sn.active_transaction = fedora_tx
            sn.save()
            success = True
        except (FedoraError, FedoraTransactionCommitFailedError) as err:
            logger.warning(
                "heslar.ruian_sync.syncer._log_katastr_rename.sn_fedora_error",
                extra={"ident_cely": sn.ident_cely, "error": str(err)[:500]},
            )
        finally:
            fedora_tx.mark_transaction_as_closed() if success else fedora_tx.rollback_transaction()
        counts["sn"] += 1

    # NeidentAkce nemá historii; Fedora update zajistí post_save signál přes nadřazený dokument.
    for neident_akce in NeidentAkce.objects.filter(katastr=katastr):
        try:
            neident_akce.save()
        except (FedoraError, FedoraTransactionCommitFailedError) as err:
            logger.warning(
                "heslar.ruian_sync.syncer._log_katastr_rename.neident_akce_fedora_error",
                extra={"pk": neident_akce.pk, "error": str(err)[:500]},
            )
        counts["neident_akce"] += 1

    return counts
