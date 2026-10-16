"""Jednotkové testy liveness signálu celery workeru (``cron.tasks.record_celery_worker_task_done``)."""

from unittest import mock

from cron.tasks import (
    CELERY_WORKER_LAST_TASK_DONE_KEY_PREFIX,
    celery_worker_liveness_ping,
    record_celery_worker_task_done,
)
from django.conf import settings
from django.test import SimpleTestCase

import redis


class CeleryWorkerLivenessTest(SimpleTestCase):
    """Ověřuje zápis času poslední dokončené úlohy a napojení pingu na beat."""

    @mock.patch("cron.tasks.time.time", return_value=1_700_000_000.7)
    @mock.patch("cron.tasks.RedisConnector.get_connection")
    def test_handler_writes_unix_time_to_key(self, get_connection, _time):
        """
        Handler zapíše celočíselný unix čas pod klíč daného workeru čtený healthcheckem.

        :param get_connection: Mock ``RedisConnector.get_connection``.
        :param _time: Mock ``time.time`` s pevnou hodnotou.
        """
        record_celery_worker_task_done(task=_task_on("worker1@amcr"), task_id="x")

        get_connection.return_value.set.assert_called_once_with(
            f"{CELERY_WORKER_LAST_TASK_DONE_KEY_PREFIX}:worker1@amcr", 1_700_000_000
        )

    @mock.patch("cron.tasks.RedisConnector.get_connection")
    def test_handler_skips_task_without_hostname(self, get_connection):
        """
        Úloha spuštěná mimo worker (např. eager) nemá hostname a klíč se nezapisuje.

        :param get_connection: Mock ``RedisConnector.get_connection``.
        """
        record_celery_worker_task_done(task=_task_on(None), task_id="x")

        get_connection.assert_not_called()

    @mock.patch("cron.tasks.RedisConnector.get_connection")
    def test_handler_swallows_redis_error(self, get_connection):
        """
        Nedostupný Redis nesmí vyhodit výjimku do vykonávané úlohy.

        :param get_connection: Mock ``RedisConnector.get_connection``, jehož ``set`` selže.
        """
        get_connection.return_value.set.side_effect = redis.ConnectionError("down")

        with self.assertLogs("cron.tasks", level="WARNING"):
            record_celery_worker_task_done(task=_task_on("worker1@amcr"), task_id="x")

    def test_key_matches_healthcheck_script(self):
        """Prefix klíče musí odpovídat ``LIVENESS_KEY`` ve ``scripts/run-healthcheck_celery.sh``."""
        script = settings.BASE_DIR.parent / "scripts" / "run-healthcheck_celery.sh"
        if not script.exists():
            self.skipTest("scripts/ není v image k dispozici")
        self.assertIn(
            f'LIVENESS_KEY="{CELERY_WORKER_LAST_TASK_DONE_KEY_PREFIX}:${{WORKER_NAME}}"',
            script.read_text(encoding="utf-8"),
        )

    def test_beat_schedule_points_to_ping_task(self):
        """Položka v ``CELERY_BEAT_SCHEDULE`` odkazuje na registrovanou ping úlohu a neukládá výsledek."""
        entry = settings.CELERY_BEAT_SCHEDULE["celery_worker_liveness_ping"]

        self.assertEqual(entry["task"], celery_worker_liveness_ping.name)
        self.assertTrue(celery_worker_liveness_ping.ignore_result)
        self.assertEqual(entry["options"]["expires"], entry["schedule"])


def _task_on(hostname):
    """
    Vrátí zástupnou úlohu, jejíž aktuální požadavek běží na zadaném workeru.

    :param hostname: Hostname workeru v ``task.request.hostname``, nebo ``None``.
    :return: Mock úlohy s nastaveným ``request.hostname``.
    """
    return mock.Mock(request=mock.Mock(hostname=hostname))
