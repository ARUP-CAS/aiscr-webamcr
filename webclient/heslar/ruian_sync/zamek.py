"""
Zámek serializující běhy synchronizace RÚIAN.

Sdílí ho plánovaný denní sync (:func:`cron.tasks.sync_ruian_changes`) i ruční
plný sync (``manage.py aktualizuj_ruian_shp``). Obojí sahá na tytéž hesláře
a čte tutéž kotvu :meth:`heslar.models.RuianSyncRun.last_successful`, takže
souběh jednoho s druhým vede ke ztrátě dat – proto zámek nebydlí v cronu,
ale u samotné synchronizace.
"""

import contextlib
import logging

logger = logging.getLogger(__name__)

#: Klíč Postgres advisory locku serializujícího běhy synchronizace RÚIAN.
#: Advisory lock (ne Redis) proto, že drží po celou dobu session a nemůže
#: uprostřed běhu vypršet – catch-up přes desítky dní i plný sync trvají
#: klidně hodiny, takže jakýkoli TTL by musel mít heartbeat. Uvolní se i
#: tvrdým pádem procesu, protože ho Postgres pustí se zánikem spojení.
RUIAN_SYNC_LOCK_KEY = 372_004_066


@contextlib.contextmanager
def ruian_sync_lock():
    """
    Zajistí, že synchronizace RÚIAN neběží ve dvou instancích současně.

    Souběžné běhy by četly stejnou kotvu ``RuianSyncRun.last_successful()``,
    stahovaly do stejné cílové cesty (včetně ``.tmp``) a dvakrát aplikovaly
    tytéž změny do DB, historie i Fedory.

    Chrání i dvojici *plný sync × denní delta*: plný sync trvá hodiny a delta
    spuštěná mezitím by měla novější ``started_at``, stala by se
    ``last_successful()`` a plný sync by pak přes ni zapsal svůj starší
    snapshot – změny toho dne by zmizely.

    :return: Generátor vracející ``True``, když byl zámek získán, jinak
        ``False``; volající v tom případě běh přeskočí.
    """
    from django.db import connection as db_connection

    with db_connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [RUIAN_SYNC_LOCK_KEY])
        ziskan = bool(cursor.fetchone()[0])
    try:
        yield ziskan
    finally:
        if ziskan:
            with db_connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [RUIAN_SYNC_LOCK_KEY])
