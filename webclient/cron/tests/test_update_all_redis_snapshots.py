"""Jednotkové testy týdenní úlohy ``cron.tasks.update_all_redis_snapshots`` (issue #4438)."""

from unittest import mock

from cron.tasks import _update_redis_snapshots_for_class, update_all_redis_snapshots
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


class _FakePipeline:
    """Náhrada Redis pipeline: zaznamenává příkazy a ``exists`` vyhodnocuje proti množině existujících klíčů."""

    def __init__(self, existing):
        """
        Vytvoří pipeline nad množinou existujících klíčů.

        :param existing: Klíče, které v Redis „existují“.
        """
        self.existing = existing
        self.pending = []
        self.executed = []

    def exists(self, key):
        """
        Zařadí ověření existence klíče.

        :param key: Klíč v Redis.
        """
        self.pending.append(("exists", key))

    def delete(self, key):
        """
        Zařadí smazání klíče.

        :param key: Klíč v Redis.
        """
        self.pending.append(("delete", key))

    def hset(self, key, mapping):
        """
        Zařadí zápis hashe.

        :param key: Klíč v Redis.
        :param mapping: Zapisovaná data.
        """
        self.pending.append(("hset", key))

    def execute(self):
        """
        Provede zařazené příkazy a vrátí jejich výsledky (u ``exists`` 1/0).

        :return: Seznam výsledků v pořadí příkazů.
        """
        results = [int(key in self.existing) if cmd == "exists" else True for cmd, key in self.pending]
        self.executed.append(self.pending)
        self.pending = []
        return results


class _FakeModel:
    """Náhrada třídy modelu s ``redis_snapshot_id`` a dávkovým ``generate_redis_snapshots``."""

    generated = []

    def __init__(self, pk):
        """
        Vytvoří záznam s daným primárním klíčem.

        :param pk: Primární klíč záznamu.
        """
        self.pk = pk
        self.redis_snapshot_id = f"fake_{pk}"

    @classmethod
    def generate_redis_snapshots(cls, records):
        """
        Zaznamená dávku a vrátí snapshoty pro všechny záznamy kromě pk 3 (jako by mezitím zmizel).

        :param records: Záznamy dávky.
        :return: Slovník ``{redis_snapshot_id: data}``.
        """
        cls.generated.append([record.pk for record in records])
        return {record.redis_snapshot_id: {"pk": str(record.pk)} for record in records if record.pk != 3}


class UpdateRedisSnapshotsForClassTest(SimpleTestCase):
    """Ověřuje dávkové ověření existence klíčů a dávkové generování snapshotů jedné třídy."""

    def setUp(self):
        """Připraví záznamy 1–5 a vyprázdní záznam vygenerovaných dávek."""
        _FakeModel.generated = []
        _FakeModel.objects = mock.Mock()
        self.items = [_FakeModel(pk) for pk in range(1, 6)]

    def _run(self, existing, rewrite_existing):
        """
        Spustí zpracování třídy s dávkou velikosti 2.

        :param existing: Klíče, které v Redis existují.
        :param rewrite_existing: Hodnota parametru ``rewrite_existing``.
        :return: N-tice (výsledek funkce, pipeline).
        """
        pipe = _FakePipeline(existing)
        r = mock.Mock(pipeline=mock.Mock(return_value=pipe))
        with (
            mock.patch("cron.tasks.REDIS_SNAPSHOT_BATCH_SIZE", 2),
            mock.patch("cron.tasks.iter_pk_chunks", return_value=iter(self.items)),
        ):
            result = _update_redis_snapshots_for_class(r, _FakeModel, rewrite_existing)
        return result, pipe

    def test_generates_only_missing_keys_per_batch(self):
        """Bez ``rewrite_existing`` se generují jen chybějící klíče, po dávkách a bez mazání."""
        result, pipe = self._run(existing={"fake_2", "fake_4"}, rewrite_existing=False)

        self.assertEqual(result, (5, 2))
        self.assertEqual(_FakeModel.generated, [[1], [3], [5]])
        writes = [cmd for batch in pipe.executed for cmd in batch if cmd[0] != "exists"]
        self.assertEqual(writes, [("hset", "fake_1"), ("hset", "fake_5")])

    def test_rewrite_existing_regenerates_all_without_exists(self):
        """S ``rewrite_existing`` se existence neověřuje a každý klíč se před zápisem smaže."""
        result, pipe = self._run(existing={"fake_1"}, rewrite_existing=True)

        self.assertEqual(result, (5, 4))
        self.assertEqual(_FakeModel.generated, [[1, 2], [3, 4], [5]])
        commands = [cmd for batch in pipe.executed for cmd in batch]
        self.assertNotIn("exists", [cmd for cmd, _ in commands])
        self.assertEqual(commands[:2], [("delete", "fake_1"), ("hset", "fake_1")])

    def test_batch_without_missing_keys_skips_generation(self):
        """Když v dávce žádný klíč nechybí, snapshoty se negenerují."""
        result, _pipe = self._run(existing={f"fake_{pk}" for pk in range(1, 6)}, rewrite_existing=False)

        self.assertEqual(result, (5, 0))
        self.assertEqual(_FakeModel.generated, [])
