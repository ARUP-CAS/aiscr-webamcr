"""
Přepočet příslušnosti záznamů (Projekt, AZ, SN, NeidentAkce) ke katastrům.

Volá se ze :mod:`heslar.ruian_sync.syncer` v případě smazání katastru,
z admin endpointu ``/admin/update-katastry/`` pro hromadný přepočet
vybraných záznamů a z Django shell přes :func:`reassign_all` pro
batch refresh celé DB. Implementuje pravidla z issue #372:

* **AZ** – hlavní katastr se stanoví podle PIAN první DJ (využívá existující
  :func:`core.utils.update_all_katastr_within_akce_or_lokalita`); ostatní
  katastry se dopočítají stejným způsobem.
* **Projekt** – upravuje se pouze ``hlavni_katastr``, M2M ``katastry``
  zůstává beze změny.
* **SN** – přepočítá se ``katastr`` podle ``sn.geom``; pokud geometrie chybí,
  použije se fallback bod (typicky definiční bod původního katastru).
* **NeidentAkce** – přepočítá se ``katastr`` výhradně z ``fallback_point``
  (vlastní geometrii nemá).
"""

from __future__ import annotations

import logging
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from arch_z.models import ArcheologickyZaznam
from core.constants import ZMENA_KATASTRU
from core.repository_connector import (
    FedoraError,
    FedoraTransaction,
    FedoraTransactionCommitFailedError,
)
from core.utils import get_cadastre_from_point
from dj.models import DokumentacniJednotka
from django.db import connection
from heslar import hesla_dynamicka
from heslar.hesla_dynamicka import TYP_DJ_KATASTR
from heslar.models import RuianKatastr
from historie.models import Historie
from neidentakce.models import NeidentAkce
from pas.models import SamostatnyNalez
from projekt.models import Projekt
from uzivatel.models import User

logger = logging.getLogger(__name__)


def _point_to_xy(point) -> Optional[Tuple[float, float]]:
    """
    Převede ``GEOSGeometry`` bod na dvojici ``(x, y)`` v EPSG:4326.

    :param point: Geometrický bod (typicky ``Point`` objektu modelu) nebo ``None``.

        :return: Dvojice ``(x, y)`` ve WGS84, nebo ``None`` pokud byl vstup ``None``
            nebo prázdná geometrie (``EMPTY``).
    """
    if point is None or point.empty:
        return None
    return (point.x, point.y)


def _resolve_target_point(record_point, fallback_point) -> Optional[Tuple[float, float]]:
    """
    Vybere bod, podle kterého se má hledat nový katastr.

    Preferuje vlastní geometrii záznamu; pokud není k dispozici, použije
    ``fallback_point`` (typicky definiční bod původního katastru).

    :param record_point: ``GEOSGeometry`` bod záznamu, nebo ``None``.
    :param fallback_point: Záložní ``GEOSGeometry`` bod, nebo ``None``.

        :return: Dvojice ``(x, y)`` nebo ``None`` (žádná dostupná geometrie).
    """
    return _point_to_xy(record_point) or _point_to_xy(fallback_point)


def _close_or_rollback(fedora_tx: FedoraTransaction, success: bool) -> None:
    """
    Uzavře transakci commitem (při ``success=True``) nebo provede rollback.

    Commit pošle ČUZK Fedoře ``COMMIT`` request a spustí post-commit úlohy;
    rollback pošle ``ROLLBACK``.

    :param fedora_tx: Instance lokální transakce (:class:`FedoraTransaction`).
    :param success: ``True`` = commit, ``False`` = rollback.
    """
    if success:
        fedora_tx.mark_transaction_as_closed()
    else:
        fedora_tx.rollback_transaction()


def _log_katastr_change(historie_vazba_id: Optional[int], old_nazev: str, new_nazev: str) -> None:
    """
    Zapíše záznam do :class:`~historie.models.Historie` při změně katastru záznamu.

    Používá se v batch reassignu (:func:`reassign_all`) a v cíleném reassignu
    po změně hranic katastru. Vzor je shodný s
    :func:`heslar.ruian_sync.syncer._log_katastr_change_for_record`.

    :param historie_vazba_id: PK :class:`~historie.models.HistorieVazby` záznamu.
    :param old_nazev: Název původního katastru (použije ``"?"`` pokud je prázdný).
    :param new_nazev: Název nového katastru.
    """
    if historie_vazba_id is None:
        return
    Historie.objects.create(
        typ_zmeny=ZMENA_KATASTRU,
        uzivatel=User.objects.get(pk=hesla_dynamicka.ADMIN_USER),
        poznamka=f"{old_nazev} -> {new_nazev}",
        vazba_id=historie_vazba_id,
    )
    logger.debug(
        "heslar.ruian_sync.reassign._log_katastr_change",
        extra={"vazba_id": historie_vazba_id, "old": old_nazev, "new": new_nazev},
    )


def _log_az_ostatni_change(
    historie_vazba_id: Optional[int],
    to_add: set,
    to_remove: set,
) -> None:
    """
    Zapíše agregovaný záznam do :class:`~historie.models.Historie` při změně
    M2M ``katastry`` archeologického záznamu.

    Přidané katastry jsou uvozeny ``+``, odebrané ``-``.
    Příklad poznámky: ``"+Jehnědí, -Horní Sloupnice"``.

    :param historie_vazba_id: PK :class:`~historie.models.HistorieVazby` záznamu.
    :param to_add: Množina PK katastrů, které byly přidány do M2M.
    :param to_remove: Množina PK katastrů, které byly odebrány z M2M.
    """
    if not historie_vazba_id or (not to_add and not to_remove):
        return
    names = {k.pk: k.nazev for k in RuianKatastr.objects.filter(pk__in=to_add | to_remove).only("pk", "nazev")}
    parts = [f"+{names.get(pk, pk)}" for pk in sorted(to_add)]
    parts += [f"-{names.get(pk, pk)}" for pk in sorted(to_remove)]
    Historie.objects.create(
        typ_zmeny=ZMENA_KATASTRU,
        uzivatel=User.objects.get(pk=hesla_dynamicka.ADMIN_USER),
        poznamka=", ".join(parts),
        vazba_id=historie_vazba_id,
    )
    logger.debug(
        "heslar.ruian_sync.reassign._log_az_ostatni_change",
        extra={"vazba_id": historie_vazba_id, "poznamka": ", ".join(parts)},
    )


def _compute_az_katastr_assignment(
    az_ident_cely: str,
    *,
    exclude_kod: Optional[int] = None,
) -> Tuple[Optional[int], List[int]]:
    """
    Vrátí cílové přiřazení katastrů pro AZ podle PIAN intersect jeho DJ.

    Jedna lehčí SQL query nahrazuje původní dvoudílný UNION
    z :func:`core.utils.get_all_pians_with_akce`. Vrací **pouze** ID
    katastrů (původní query tahala i ``ST_AsText(geom)``, ``pian.ident_cely``,
    katastr nazev atd., které reassign vůbec nepoužíval – pro AZ
    s mnoha DJ to znamenalo desítky kB zbytečných dat).

    Pořadí výsledků je zachováno shodně se starou implementací: v rámci
    každé DJ jsou napřed katastry obsahující **centroid PIANu**
    (= "majoritní" katastr, kde polygon převážně leží), pak ostatní
    abecedně podle ``katastr.nazev``; mezi DJ se řadí podle
    ``dj.ident_cely``. Determinismus volby *hlavního* katastru
    (= první unikátní katastr v pořadí) tak zůstává shodný s předchozí
    implementací přes ``core.utils.get_all_pians_with_akce``, jejíž první
    UNION větev vybírala katastr s centroidem PIANu prvního DJ.

    :param az_ident_cely: Identifikátor archeologického záznamu
        (např. ``"M-CHEB-202200095"``); jeho DJ se vyhledají přes
        ``ident_cely LIKE '<az>-%'``.
    :param exclude_kod: Volitelný kód katastru, který se vyloučí z prostorové
        query (typicky mazaný katastr v ``_delete_katastr``).

        :return: Dvojice ``(hlavni_id, ostatni_ids)``. ``hlavni_id`` je ID
            prvního unikátního katastru v deterministickém pořadí, ostatní
            jsou všechny další unikátní katastry. Pokud AZ nemá DJ
            s PIAN intersectem, vrací ``(None, [])``.
    """
    query = """
        SELECT k.id
        FROM (
            SELECT dj.ident_cely AS dj_ident_cely, pian.geom AS pian_geom
            FROM public.dokumentacni_jednotka dj
            JOIN public.pian pian ON dj.pian = pian.id
            WHERE dj.ident_cely LIKE %s
              AND pian.geom IS NOT NULL
        ) dp
        JOIN public.ruian_katastr k ON ST_Intersects(k.hranice, dp.pian_geom)
        WHERE %s::int IS NULL OR k.kod <> %s::int
        ORDER BY dp.dj_ident_cely,
                 ST_Intersects(k.hranice,
                     CASE
                         WHEN ST_GeometryType(dp.pian_geom) = 'ST_LineString'
                             THEN ST_LineInterpolatePoint(dp.pian_geom, 0.5)
                         WHEN ST_GeometryType(dp.pian_geom) IN ('ST_Polygon', 'ST_MultiPolygon')
                             THEN ST_PointOnSurface(dp.pian_geom)
                         ELSE ST_Centroid(dp.pian_geom)
                     END
                 ) DESC,
                 k.nazev
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [f"{az_ident_cely}-%", exclude_kod, exclude_kod])
        rows = cursor.fetchall()

    hlavni_id: Optional[int] = None
    ostatni_ids: List[int] = []
    seen = set()
    for (katastr_id,) in rows:
        if katastr_id in seen:
            continue
        seen.add(katastr_id)
        if hlavni_id is None:
            hlavni_id = katastr_id
        else:
            ostatni_ids.append(katastr_id)
    return hlavni_id, ostatni_ids


def _update_az_katastry_if_changed(
    az: ArcheologickyZaznam,
    *,
    exclude_kod: Optional[int] = None,
) -> bool:
    """
    Aktualizuje ``hlavni_katastr`` a M2M ``katastry`` AZ podle PIAN intersect.

    **Save se volá jen pokud se reálně něco mění** – pokud nový hlavní
    katastr i nová sada ostatních se rovnají stávajícím, AZ se vůbec
    nesaveuje a Fedora ``UPDATE_METADATA`` neproběhne. Při batch reassignu
    nad tisíci AZ záznamy to ušetří většinu I/O.

    Lokální Fedora transakce se otevírá **až ve chvíli**, kdy je jisté,
    že proběhne zápis – nezakládáme tedy v ČUZK Fedoře prázdnou transakci
    pro AZ, které se nemění.

    M2M se aktualizuje **delta-only** přes ``add()`` + ``remove()``
    (původní ``katastry.set(...)`` smazal všechny rows a založil je znovu).

    :param az: Archeologický záznam.
    :param exclude_kod: Volitelný kód katastru vyloučený z prostorové query.

        :return: ``True`` pokud byly provedeny změny (proběhl save),
            ``False`` pokud nový stav je identický se stávajícím.
    """
    new_hlavni_id, new_ostatni_ids = _compute_az_katastr_assignment(az.ident_cely, exclude_kod=exclude_kod)

    if new_hlavni_id is None:
        # AZ nemá DJ s PIAN intersectem – necháme stávající stav,
        # volající (reassign_az) se případně zkusí dostat přes fallback_point.
        logger.debug(
            "heslar.ruian_sync.reassign._update_az_katastry_if_changed.no_pian",
            extra={"ident_cely": az.ident_cely},
        )
        return False

    current_ostatni = set(az.katastry.values_list("pk", flat=True))
    new_ostatni = set(new_ostatni_ids)
    hlavni_changed = new_hlavni_id != az.hlavni_katastr_id
    ostatni_changed = new_ostatni != current_ostatni

    if not hlavni_changed and not ostatni_changed:
        logger.debug(
            "heslar.ruian_sync.reassign._update_az_katastry_if_changed.unchanged",
            extra={"ident_cely": az.ident_cely},
        )
        return False

    old_hlavni_nazev = az.hlavni_katastr.nazev if hlavni_changed and az.hlavni_katastr else "?"
    to_add: set = set()
    to_remove: set = set()
    if hlavni_changed:
        new_hlavni_nazev = RuianKatastr.objects.values_list("nazev", flat=True).get(pk=new_hlavni_id)
        _log_katastr_change(az.historie_id, old_hlavni_nazev, new_hlavni_nazev)
    if ostatni_changed:
        to_add = new_ostatni - current_ostatni
        to_remove = current_ostatni - new_ostatni
        _log_az_ostatni_change(az.historie_id, to_add, to_remove)
    fedora_tx = FedoraTransaction()
    success = False
    try:
        if hlavni_changed:
            az.hlavni_katastr_id = new_hlavni_id
        if ostatni_changed:
            if to_add:
                az.katastry.add(*to_add)
            if to_remove:
                az.katastry.remove(*to_remove)
        az.active_transaction = fedora_tx
        az.save()
        success = True
    finally:
        _close_or_rollback(fedora_tx, success)
    return True


def reassign_az(
    az: ArcheologickyZaznam,
    fallback_point=None,
    *,
    exclude_kod: Optional[int] = None,
) -> Optional[RuianKatastr]:
    """
    Přepočítá ``hlavni_katastr`` a M2M ``katastry`` archeologického záznamu.

    Pokud má AZ alespoň jednu DJ, deleguje výpočet na lokální optimalizovanou
    funkci :func:`_update_az_katastry_if_changed`, která:

    * spustí jednu lehkou SQL query (jen ID katastrů – ne geometry/pian
      metadata jako původní :func:`core.utils.update_all_katastr_within_akce_or_lokalita`);
    * **skipne save**, pokud nový hlavní katastr i M2M jsou stejné jako
      stávající (žádný Fedora ``UPDATE_METADATA`` request);
    * lokální Fedora transakci otevírá až ve chvíli, kdy je jistý zápis;
    * M2M aktualizuje delta-only přes ``add()`` + ``remove()``.

    Pokud první DJ je typu *celokatastr* (``TYP_DJ_KATASTR``), přepočet se
    neprovádí – zachovává se původní semantika ``core.utils`` utility.

    Pokud AZ žádnou DJ nemá, spočítá pouze ``hlavni_katastr`` z
    ``fallback_point`` (definiční bod původního katastru).

    :param az: Instance :class:`ArcheologickyZaznam`, která má být přepočítána.
    :param fallback_point: ``Point`` (EPSG:4326) použitý, pokud AZ nemá DJ;
        typicky definiční bod původního katastru.
    :param exclude_kod: Volitelný kód katastru, který se vyloučí ze spatial
        intersect (používá se při mazání katastru – aby se mazaný katastr,
        který je do okamžiku ``katastr.delete()`` stále v DB, nevybral zpět).

        :return: Nový ``hlavni_katastr`` po přepočtu nebo ``None`` (nepodařilo se určit).
    """
    logger.debug("heslar.ruian_sync.reassign.reassign_az.start", extra={"ident_cely": az.ident_cely})

    first_dj = DokumentacniJednotka.objects.filter(archeologicky_zaznam=az).order_by("ident_cely").first()
    if first_dj is not None:
        # Celokatastr DJ nemá smysl řešit PIAN intersectem – původní
        # `update_all_katastr_within_akce_or_lokalita` v tomto případě
        # vůbec nic nedělala. Zachováváme stejné chování.
        if first_dj.typ_id == TYP_DJ_KATASTR:
            return az.hlavni_katastr

        changed = _update_az_katastry_if_changed(az, exclude_kod=exclude_kod)
        if changed:
            az.refresh_from_db()
        return az.hlavni_katastr

    target = _resolve_target_point(None, fallback_point)
    if target is None:
        logger.warning("heslar.ruian_sync.reassign.reassign_az.no_geometry", extra={"ident_cely": az.ident_cely})
        return None

    new_katastr = get_cadastre_from_point(target, exclude_kod=exclude_kod)
    if new_katastr is None:
        return None

    if new_katastr.pk != az.hlavni_katastr_id:
        old_nazev = az.hlavni_katastr.nazev if az.hlavni_katastr else "?"
        _log_katastr_change(az.historie_id, old_nazev, new_katastr.nazev)
        fedora_tx = FedoraTransaction()
        success = False
        try:
            az.hlavni_katastr = new_katastr
            az.active_transaction = fedora_tx
            az.save()
            success = True
        finally:
            _close_or_rollback(fedora_tx, success)
    return new_katastr


def reassign_projekt(
    projekt: Projekt,
    fallback_point=None,
    *,
    exclude_kod: Optional[int] = None,
) -> Optional[RuianKatastr]:
    """
    Přepočítá ``hlavni_katastr`` projektu.

    M2M ``katastry`` projektu se záměrně neupravuje (viz zadání issue #372 –
    *„pro projekty se další katastry ponechají beze změny, upraví se pouze
    hlavní katastr"*).

    Pro každé volání které opravdu zapisuje se uvnitř vytvoří lokální Fedora
    transakce a po dokončení save se buď commitne nebo rollbackne – viz
    :func:`reassign_az`.

    :param projekt: Instance :class:`Projekt`, která má být přepočítána.
    :param fallback_point: ``Point`` (EPSG:4326) použitý, pokud projekt nemá ``geom``.
    :param exclude_kod: Volitelný kód katastru vyloučený ze spatial query
        (viz :func:`reassign_az`).

        :return: Nový ``hlavni_katastr`` po přepočtu nebo ``None``.
    """
    logger.debug("heslar.ruian_sync.reassign.reassign_projekt.start", extra={"ident_cely": projekt.ident_cely})

    target = _resolve_target_point(projekt.geom, fallback_point)
    if target is None:
        logger.warning(
            "heslar.ruian_sync.reassign.reassign_projekt.no_geometry",
            extra={"ident_cely": projekt.ident_cely},
        )
        return None

    new_katastr = get_cadastre_from_point(target, exclude_kod=exclude_kod)
    if new_katastr is None:
        return None

    if new_katastr.pk != projekt.hlavni_katastr_id:
        old_nazev = projekt.hlavni_katastr.nazev if projekt.hlavni_katastr else "?"
        _log_katastr_change(projekt.historie_id, old_nazev, new_katastr.nazev)
        fedora_tx = FedoraTransaction()
        success = False
        try:
            projekt.hlavni_katastr = new_katastr
            projekt.active_transaction = fedora_tx
            projekt.save()
            success = True
        finally:
            _close_or_rollback(fedora_tx, success)
    return new_katastr


def reassign_projekt_dalsi_katastr(
    projekt: Projekt,
    old_katastr: RuianKatastr,
    fallback_point=None,
    *,
    exclude_kod: Optional[int] = None,
) -> None:
    """
    Nahradí mazaný katastr v M2M ``katastry`` projektu prostorovým náhradníkem.

    Pokud prostorový náhradník existuje a ještě není v ``projekt.katastry``,
    přidá ho. Vždy odebere ``old_katastr`` z M2M a zapíše změnu do
    :class:`~historie.models.Historie`. Fedora metadata se aktualizují
    přes ``projekt.save()`` s lokální transakcí.

    Pokud ``old_katastr`` v M2M projektu není, funkce je no-op.

    :param projekt: Instance :class:`Projekt`.
    :param old_katastr: Katastr odebíraný z M2M (mazaný katastr).
    :param fallback_point: Záložní ``Point`` (EPSG:4326) pro spatial query
        (typicky definiční bod mazaného katastru).
    :param exclude_kod: Kód katastru vyloučený ze spatial query
        (viz :func:`reassign_az`).
    """
    logger.debug(
        "heslar.ruian_sync.reassign.reassign_projekt_dalsi_katastr.start",
        extra={"ident_cely": projekt.ident_cely, "old_katastr_kod": old_katastr.kod},
    )

    current = set(projekt.katastry.values_list("pk", flat=True))
    if old_katastr.pk not in current:
        return

    target = _resolve_target_point(projekt.geom, fallback_point)
    new_katastr = get_cadastre_from_point(target, exclude_kod=exclude_kod) if target else None

    to_add: set = set()
    to_remove: set = {old_katastr.pk}

    if new_katastr is not None and new_katastr.pk not in current:
        to_add = {new_katastr.pk}

    if to_add:
        projekt.katastry.add(*to_add)
    projekt.katastry.remove(old_katastr)

    fedora_tx = FedoraTransaction()
    success = False
    try:
        projekt.active_transaction = fedora_tx
        projekt.save()
        success = True
    finally:
        _close_or_rollback(fedora_tx, success)

    _log_az_ostatni_change(projekt.historie_id, to_add, to_remove)


def reassign_sn(
    sn: SamostatnyNalez,
    fallback_point=None,
    *,
    exclude_kod: Optional[int] = None,
) -> Optional[RuianKatastr]:
    """
    Přepočítá ``katastr`` samostatného nálezu.

    Pro každé volání které opravdu zapisuje se uvnitř vytvoří lokální Fedora
    transakce a po dokončení save se buď commitne nebo rollbackne – viz
    :func:`reassign_az`.

    :param sn: Instance :class:`SamostatnyNalez`.
    :param fallback_point: ``Point`` (EPSG:4326) použitý, pokud SN nemá ``geom``.
    :param exclude_kod: Volitelný kód katastru vyloučený ze spatial query
        (viz :func:`reassign_az`).

        :return: Nový ``katastr`` po přepočtu nebo ``None``.
    """
    logger.debug("heslar.ruian_sync.reassign.reassign_sn.start", extra={"ident_cely": sn.ident_cely})

    target = _resolve_target_point(sn.geom, fallback_point)
    if target is None:
        logger.warning("heslar.ruian_sync.reassign.reassign_sn.no_geometry", extra={"ident_cely": sn.ident_cely})
        return None

    new_katastr = get_cadastre_from_point(target, exclude_kod=exclude_kod)
    if new_katastr is None:
        return None

    if new_katastr.pk != sn.katastr_id:
        old_nazev = sn.katastr.nazev if sn.katastr else "?"
        _log_katastr_change(sn.historie_id, old_nazev, new_katastr.nazev)
        fedora_tx = FedoraTransaction()
        success = False
        try:
            sn.katastr = new_katastr
            sn.active_transaction = fedora_tx
            sn.save()
            success = True
        finally:
            _close_or_rollback(fedora_tx, success)
    return new_katastr


def reassign_neident_akce(
    neident_akce: NeidentAkce,
    fallback_point=None,
    *,
    exclude_kod: Optional[int] = None,
) -> Optional[RuianKatastr]:
    """
    Přepočítá ``katastr`` neidentifikované akce.

    NeidentAkce nemá vlastní geometrii (``pian`` a ``lokalizace`` jsou pouze
    textová pole), proto se pro spatial query vždy použije ``fallback_point``
    – typicky definiční bod původního katastru.

    :param neident_akce: Instance :class:`NeidentAkce`.
    :param fallback_point: ``Point`` (EPSG:4326) – typicky definiční bod
        původního (mazaného) katastru.
    :param exclude_kod: Volitelný kód katastru vyloučený ze spatial query
        (viz :func:`reassign_az`).

        :return: Nový ``katastr`` po přepočtu nebo ``None``.
    """
    logger.debug(
        "heslar.ruian_sync.reassign.reassign_neident_akce.start",
        extra={"pk": neident_akce.pk},
    )

    target = _point_to_xy(fallback_point)
    if target is None:
        logger.warning(
            "heslar.ruian_sync.reassign.reassign_neident_akce.no_geometry",
            extra={"pk": neident_akce.pk},
        )
        return None

    new_katastr = get_cadastre_from_point(target, exclude_kod=exclude_kod)
    if new_katastr is None:
        return None

    if new_katastr.pk != neident_akce.katastr_id:
        neident_akce.katastr = new_katastr
        neident_akce.save()
    return new_katastr


# ---------------------------------------------------------------------------
# Batch helper pro Django shell
# ---------------------------------------------------------------------------


#: Entity podporované v :func:`reassign_all`. NeidentAkce **není** v seznamu
#: záměrně: nemá vlastní geometrii, takže batch reassign by spatial query
#: pouštěl proti vlastnímu ``katastr.definicni_bod`` a vždy by skončil
#: zpět u téhož katastru (no-op). NeidentAkce se přepočítává jen v rámci
#: :func:`heslar.ruian_sync.syncer._delete_katastr`, kde ``exclude_kod``
#: zařídí, že spatial query mazaný katastr přeskočí a najde nejbližší jiný.
_REASSIGN_MODELS = ("projekt", "az", "sn")


def _print_progress(label: str, current: int, total: int, last_pct: int) -> int:
    """
    Vypíše progress (1% throttle) na stdout a vrátí naposledy vypsané procento.

    :param label: Krátký prefix řádku (např. ``"projekt"``).
    :param current: Kolik záznamů již zpracováno (1-based).
    :param total: Celkový počet záznamů ke zpracování.
    :param last_pct: Naposledy vypsané procento – aby se nevypisovalo pro každý záznam.

        :return: Nové ``last_pct`` (vrátí se stejná hodnota, pokud se ještě
            nevypsalo nové procento).
    """
    if total <= 0:
        return last_pct
    pct = int(current * 100 / total)
    if pct > last_pct:
        print(f"  {label}: {current}/{total} ({pct}%)", flush=True)
        return pct
    return last_pct


def _iter_pk_chunks(queryset, chunk_size: int = 1000) -> Iterator:
    """
    Iteruje queryset po dávkách řazených podle PK (keyset pagination).

    Náhrada za ``QuerySet.iterator()``, který je v této konfiguraci k ničemu:
    default DB má ``DISABLE_SERVER_SIDE_CURSORS = True``, takže
    ``iterator()`` nestreamuje, ale natáhne celý resultset do paměti procesu
    naráz. Tato funkce drží v paměti vždy jen ``chunk_size`` záznamů – každou
    dávku získá samostatným dotazem ``... WHERE pk > last_pk ORDER BY pk LIMIT n``.

    Keyset paginace je bezpečná i při souběžném mutování záznamů, protože reassign
    nemění PK ani příslušnost záznamu do iterované množiny (AZ stále má DJ apod.).

    :param queryset: Queryset ke zpracování (přeřadí se podle ``pk``).
    :param chunk_size: Počet záznamů načtených na jednu dávku.

        :return: Generátor instancí modelu.
    """
    ordered = queryset.order_by("pk")
    last_pk = 0
    while True:
        chunk = list(ordered.filter(pk__gt=last_pk)[:chunk_size])
        if not chunk:
            break
        for obj in chunk:
            yield obj
        last_pk = chunk[-1].pk


def reassign_all(
    *,
    only_models: Optional[Iterable[str]] = None,
) -> Dict[str, Dict[str, int]]:
    """
    Batch helper pro Django shell: přepočítá příslušnost ke katastru
    pro Projekt / AZ / SN, které mají co přepočítávat.

    Iteruje **jen záznamy schopné reálné změny** v batch módu
    (bez ``exclude_kod``):

    * **Projekt** s vyplněným ``geom``;
    * **AZ** s alespoň jednou DJ (PIAN intersect);
    * **SN** s vyplněným ``geom``.

    Záznamy bez vlastní geometrie / DJ se v batch módu vůbec neiterují
    – spatial query z vlastního ``katastr.definicni_bod`` by vždy vrátila
    zpět tentýž katastr (no-op). Zbytečně by se jen pálily SQL queries.

    **NeidentAkce není podporovaná** ze stejného důvodu (nemá vlastní
    geometrii vůbec). Přepočítává se jen v
    :func:`heslar.ruian_sync.syncer._delete_katastr`, kde ``exclude_kod``
    zařídí smysluplnost spatial query.

    Použití v shell::

        from heslar.ruian_sync.reassign import reassign_all

        # Plný refresh:
        result = reassign_all()

        # Jen vybraná entita:
        result = reassign_all(only_models=["sn"])

    :param only_models: Volitelná podmnožina entit ke zpracování. Akceptuje
        ``"projekt"``, ``"az"``, ``"sn"``. ``None`` = vše.

        :return: Slovník ``{entita: {"changed": N, "unchanged": N, "skipped": N,
            "errors": N}}`` pro každou zpracovanou entitu.
    """
    if only_models is None:
        targets = set(_REASSIGN_MODELS)
    else:
        targets = {m for m in only_models if m in _REASSIGN_MODELS}
        unknown = set(only_models) - set(_REASSIGN_MODELS)
        if unknown:
            print(f"reassign_all: ignoruji neznámé entity {sorted(unknown)}", flush=True)

    result: Dict[str, Dict[str, int]] = {}

    if "projekt" in targets:
        result["projekt"] = _reassign_all_projekt()
    if "az" in targets:
        result["az"] = _reassign_all_az()
    if "sn" in targets:
        result["sn"] = _reassign_all_sn()

    print("reassign_all – shrnutí:", flush=True)
    for entita, counts in result.items():
        print(
            f"  {entita}: changed={counts['changed']}, "
            f"unchanged={counts['unchanged']}, "
            f"skipped={counts['skipped']}, "
            f"errors={counts['errors']}",
            flush=True,
        )
    return result


def _reassign_all_projekt() -> Dict[str, int]:
    """
    Iteruje všechny :class:`Projekt` s vyplněným ``geom`` a volá
    :func:`reassign_projekt`.

    Projekt **bez** ``geom`` se přeskakuje – v batch módu (bez ``exclude_kod``)
    by ``reassign_projekt`` použil fallback bod = vlastní
    ``hlavni_katastr.definicni_bod`` a spatial query by vždy našla
    zpět tentýž katastr (no-op se zbytečným SQL). Smysl má jen pro
    projekty s vlastní geometrií, kde nový stav RÚIAN může vrátit jiný
    katastr.

        :return: Countery ``changed`` / ``unchanged`` / ``skipped`` / ``errors``.
    """
    counts = {"changed": 0, "unchanged": 0, "skipped": 0, "errors": 0}
    qs = Projekt.objects.filter(geom__isnull=False).select_related("hlavni_katastr").defer("hlavni_katastr__hranice")
    total = qs.count()
    print(f"Projekt: zpracovávám {total} záznamů (jen s geom)", flush=True)
    last_pct = -1
    for idx, projekt in enumerate(_iter_pk_chunks(qs), start=1):
        old_pk = projekt.hlavni_katastr_id
        try:
            new_kat = reassign_projekt(projekt)
        except (FedoraError, FedoraTransactionCommitFailedError, ValueError) as err:
            logger.warning(
                "heslar.ruian_sync.reassign.reassign_all.projekt_error",
                extra={"ident_cely": projekt.ident_cely, "error": str(err)[:500]},
            )
            counts["errors"] += 1
            last_pct = _print_progress("projekt", idx, total, last_pct)
            continue
        if new_kat is None:
            counts["skipped"] += 1
        elif new_kat.pk != old_pk:
            counts["changed"] += 1
        else:
            counts["unchanged"] += 1
        last_pct = _print_progress("projekt", idx, total, last_pct)
    return counts


def _reassign_all_az() -> Dict[str, int]:
    """
    Iteruje všechny :class:`ArcheologickyZaznam` **s alespoň jednou DJ**
    a volá :func:`reassign_az`.

    AZ **bez DJ** se přeskakuje – v batch módu (bez ``exclude_kod``) by
    ``reassign_az`` použil fallback bod = vlastní
    ``hlavni_katastr.definicni_bod`` a spatial query by vždy našla
    zpět tentýž katastr (no-op). Smysl má jen AZ s DJ, kde PIAN intersect
    může vrátit jinou sadu katastrů (např. po posunu hranice).

    Filtrace přes ``Exists`` subquery místo ``.distinct()`` – ušetří
    deduplikaci a vrátí každý AZ jen jednou.

        :return: Countery ``changed`` / ``unchanged`` / ``skipped`` / ``errors``.
    """
    from django.db.models import Exists, OuterRef

    counts = {"changed": 0, "unchanged": 0, "skipped": 0, "errors": 0}
    has_dj = DokumentacniJednotka.objects.filter(archeologicky_zaznam=OuterRef("pk"))
    qs = (
        ArcheologickyZaznam.objects.filter(Exists(has_dj))
        .select_related("hlavni_katastr")
        .defer("hlavni_katastr__hranice")
    )
    total = qs.count()
    print(f"AZ: zpracovávám {total} záznamů (jen s DJ)", flush=True)
    last_pct = -1
    for idx, az in enumerate(_iter_pk_chunks(qs), start=1):
        old_pk = az.hlavni_katastr_id
        try:
            new_kat = reassign_az(az)
        except (FedoraError, FedoraTransactionCommitFailedError, ValueError) as err:
            logger.warning(
                "heslar.ruian_sync.reassign.reassign_all.az_error",
                extra={"ident_cely": az.ident_cely, "error": str(err)[:500]},
            )
            counts["errors"] += 1
            last_pct = _print_progress("az", idx, total, last_pct)
            continue
        if new_kat is None:
            counts["skipped"] += 1
        elif new_kat.pk != old_pk:
            counts["changed"] += 1
        else:
            counts["unchanged"] += 1
        last_pct = _print_progress("az", idx, total, last_pct)
    return counts


def _reassign_all_sn() -> Dict[str, int]:
    """
    Iteruje všechny :class:`SamostatnyNalez` s vyplněným ``geom`` a volá
    :func:`reassign_sn`.

    SN **bez** ``geom`` se přeskakuje – v batch módu (bez ``exclude_kod``)
    by ``reassign_sn`` použil fallback bod = vlastní
    ``katastr.definicni_bod`` a spatial query by vždy našla zpět tentýž
    katastr (no-op). Smysl má jen pro SN s vlastní geometrií.

        :return: Countery ``changed`` / ``unchanged`` / ``skipped`` / ``errors``.
    """
    counts = {"changed": 0, "unchanged": 0, "skipped": 0, "errors": 0}
    qs = SamostatnyNalez.objects.filter(geom__isnull=False).select_related("katastr").defer("katastr__hranice")
    total = qs.count()
    print(f"SN: zpracovávám {total} záznamů (jen s geom)", flush=True)
    last_pct = -1
    for idx, sn in enumerate(_iter_pk_chunks(qs), start=1):
        old_pk = sn.katastr_id
        try:
            new_kat = reassign_sn(sn)
        except (FedoraError, FedoraTransactionCommitFailedError, ValueError) as err:
            logger.warning(
                "heslar.ruian_sync.reassign.reassign_all.sn_error",
                extra={"ident_cely": sn.ident_cely, "error": str(err)[:500]},
            )
            counts["errors"] += 1
            last_pct = _print_progress("sn", idx, total, last_pct)
            continue
        if new_kat is None:
            counts["skipped"] += 1
        elif new_kat.pk != old_pk:
            counts["changed"] += 1
        else:
            counts["unchanged"] += 1
        last_pct = _print_progress("sn", idx, total, last_pct)
    return counts
