"""
Zámky zabraňující souběhu dlouhých plánovaných úloh.

Vzor je stejný jako u :func:`heslar.ruian_sync.zamek.ruian_sync_lock`: Postgres advisory lock
na úrovni session. Nemá TTL, takže nemůže vypršet uprostřed několikahodinového běhu, a uvolní se
i při tvrdém pádu procesu, protože ho Postgres pustí se zánikem spojení.
"""

import contextlib
import logging

logger = logging.getLogger(__name__)

#: Klíč zámku úlohy :func:`cron.tasks.delete_personal_data_canceled_projects`.
LOCK_DELETE_PERSONAL_DATA_CANCELED_PROJECTS = 372_004_101
#: Klíč zámku úlohy :func:`cron.tasks.delete_reporter_data_ten_years`.
LOCK_DELETE_REPORTER_DATA_TEN_YEARS = 372_004_102
#: Klíč zámku úlohy :func:`cron.tasks.cancel_old_projects`.
LOCK_CANCEL_OLD_PROJECTS = 372_004_103
#: Klíč zámku úlohy :func:`cron.tasks.delete_unsubmited_projects`.
LOCK_DELETE_UNSUBMITED_PROJECTS = 372_004_104


@contextlib.contextmanager
def cron_task_lock(key: int):
    """
    Zajistí, že úloha se stejným ``key`` neběží ve dvou instancích současně.

    Souběžné běhy by procházely stejný seznam projektů a zapisovaly do stejných záznamů ve Fedoře,
    což vede ke konfliktu transakcí (HTTP 409) a ke ztrátě zbytku práce druhého běhu.

    :param key: Celočíselný klíč Postgres advisory locku, jedinečný pro každou úlohu.
    :return: Generátor vracející ``True``, když byl zámek získán, jinak ``False``; volající
        v druhém případě běh přeskočí.
    """
    from django.db import connection as db_connection

    with db_connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [key])
        ziskan = bool(cursor.fetchone()[0])
    try:
        yield ziskan
    finally:
        if ziskan:
            with db_connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [key])
