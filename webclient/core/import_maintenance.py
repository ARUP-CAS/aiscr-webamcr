"""Ochrana probíhající odstávky před ukončením během hromadného importu."""

from datetime import datetime

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from redis.exceptions import RedisError

from .connectors import RedisConnector
from .models import OdstavkaSystemu


class MaintenanceImportConflict(Exception):
    """Odmítnutí změny odstávky, která by zpřístupnila aplikaci během importu."""


def lock_maintenance_configuration():
    """Zamkne konfiguraci odstávky do konce transakce volajícího.

    :return: Aktuální řádky odstávky; stejný zámek používá upload i administrace odstávky.
    """
    return list(OdstavkaSystemu.objects.select_for_update().order_by("pk"))


def maintenance_is_active(maintenance):
    """Vyhodnotí řádek odstávky bez cache podle stávajících pravidel aplikace.

    :param maintenance: Uložená nebo navrhovaná konfigurace odstávky.
    :return: Zda je odstávka zapnutá, zveřejněná a její začátek již nastal.
    """
    from .utils import get_timezone

    return bool(
        maintenance.status
        and maintenance.info_od <= datetime.today().date()
        and get_timezone().localize(datetime.combine(maintenance.datum_odstavky, maintenance.cas_odstavky))
        <= datetime.now(get_timezone())
    )


def import_is_protected() -> bool:
    """Zjistí, zda Redis eviduje aktivní nebo nedokončený import.

    :return: ``True``, pokud import drží lock nebo jeho aktivní ukazatel není v terminální fázi.
    :raises MaintenanceImportConflict: Stav importu nelze bezpečně ověřit.
    """
    try:
        from cron import tasks

        connection = RedisConnector.get_connection_decode()
        if connection.get(RedisConnector.IMPORT_DATA_LOCK_KEY):
            return True
        job_id = connection.get(RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY)
        return bool(job_id) and connection.get(f"import_data_phase_{job_id}") not in tasks.IMPORT_TERMINAL_PHASES
    except RedisError as exc:
        raise MaintenanceImportConflict(
            _("Maintenance cannot be ended because the import status could not be verified. Please try again later.")
        ) from exc


def ensure_maintenance_change_allowed(current, replacement=None, import_protected=None):
    """Odmítne ukončení aktivní odstávky, pokud import ještě drží ochranu.

    Volající musí držet zámek konfigurace až do uložení nebo smazání odstávky.

    :param current: Aktuální zamčený řádek odstávky.
    :param replacement: Navrhovaná konfigurace; ``None`` znamená smazání.
    :param import_protected: Předem načtený stav ochrany importu; bez hodnoty se načte z Redis.
    :raises MaintenanceImportConflict: Import běží nebo nelze jeho stav bezpečně ověřit.
    """
    if not maintenance_is_active(current) or (replacement is not None and maintenance_is_active(replacement)):
        return
    if import_protected is None:
        import_protected = import_is_protected()
    elif not import_protected:
        # The preflight snapshot can become stale while this caller waits for the row lock.
        import_protected = import_is_protected()
    if import_protected:
        raise MaintenanceImportConflict(
            _(
                "Maintenance cannot be ended while an import is active. Complete or cancel the import first. "
                "For a failed worker, use the existing manual import reset procedure."
            )
        )


def acquire_import_lock_during_maintenance(connection, token, ttl_seconds):
    """Ověří odstávku a získá importní lock atomicky vůči změnám její konfigurace.

    :param connection: Dekódující Redis spojení importního formuláře.
    :param token: Vlastnický token nového importu.
    :param ttl_seconds: Doba platnosti importního locku.
    :return: ``True`` při získání locku, ``False`` při obsazeném slotu, ``None`` bez odstávky.
    """
    # Check the occupied fast path before acquiring the maintenance row lock. The atomic SET NX
    # below remains authoritative because another request may claim the Redis lock while waiting
    # for the database transaction.
    if connection.get(RedisConnector.IMPORT_DATA_LOCK_KEY):
        return False
    with transaction.atomic():
        configurations = lock_maintenance_configuration()
        if not any(maintenance_is_active(row) for row in configurations):
            return None
        return RedisConnector.acquire_import_lock(connection, token, ttl_seconds)
