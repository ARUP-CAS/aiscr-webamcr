"""Jednotkové testy týdenní úlohy ``cron.tasks.update_all_redis_snapshots`` (issue #4438)."""

from unittest import mock

from cron.tasks import update_all_redis_snapshots
from django.test import SimpleTestCase


class UpdateAllRedisSnapshotsTest(SimpleTestCase):
    """Ověřuje, že selhání jedné třídy nezastaví zpracování ostatních tříd."""

    @mock.patch("cron.tasks.RedisConnector.get_connection")
    @mock.patch("cron.tasks._update_redis_snapshots_for_class")
    def test_failing_class_does_not_stop_others(self, update_class, _get_connection):
        """
        Chyba u první třídy se zaloguje, další třídy se zpracují a úloha nakonec skončí chybou.

        :param update_class: Mock ``_update_redis_snapshots_for_class``.
        :param _get_connection: Mock ``RedisConnector.get_connection``.
        """
        first = type("First", (), {})
        second = type("Second", (), {})
        update_class.side_effect = [Exception("canceling statement due to statement timeout"), (10, 2)]

        with self.assertLogs("cron.tasks", level="DEBUG") as logs, self.assertRaisesMessage(RuntimeError, "First"):
            update_all_redis_snapshots(classes=[first, second])

        self.assertEqual([c.args[1] for c in update_class.call_args_list], [first, second])
        messages = [record.getMessage() for record in logs.records]
        self.assertIn("cron.tasks.update_all_redis_snapshots.class_error", messages)
        self.assertIn("cron.tasks.update_all_redis_snapshots.class_end", messages)

    @mock.patch("cron.tasks.RedisConnector.get_connection")
    @mock.patch("cron.tasks._update_redis_snapshots_for_class", return_value=(3, 1))
    def test_success_logs_counts(self, _update_class, _get_connection):
        """
        Úspěšný běh nevyhodí výjimku a do ``class_end`` zaloguje počty v polích šablony.

        :param _update_class: Mock ``_update_redis_snapshots_for_class``.
        :param _get_connection: Mock ``RedisConnector.get_connection``.
        """
        only = type("Only", (), {})

        with self.assertLogs("cron.tasks", level="DEBUG") as logs:
            update_all_redis_snapshots(classes=[only])

        end = next(r for r in logs.records if r.getMessage() == "cron.tasks.update_all_redis_snapshots.class_end")
        self.assertEqual((end.count, end.number), (3, 1))
        self.assertIsInstance(end.duration_s, float)
