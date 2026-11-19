"""Testy plánovaných úloh mazajících osobní údaje projektů: zámek proti souběhu, atomicita a opakování při konfliktu Fedory."""

import contextlib
import datetime
from unittest.mock import MagicMock, call, patch

from core.repository_connector import FedoraUpdatedByAnotherTransactionError
from cron import tasks
from cron.zamek import (
    LOCK_CANCEL_OLD_PROJECTS,
    LOCK_DELETE_PERSONAL_DATA_CANCELED_PROJECTS,
    LOCK_DELETE_REPORTER_DATA_TEN_YEARS,
    LOCK_DELETE_UNSUBMITED_PROJECTS,
    cron_task_lock,
)
from django.db import OperationalError
from django.test import SimpleTestCase

LOG_PREFIX = "core.cron.test"


def _conflict():
    """Vytvoří chybu odpovídající odpovědi Fedory 409."""
    return FedoraUpdatedByAnotherTransactionError("url", "conflict", 409)


class ProcessProjectInFedoraTransactionTest(SimpleTestCase):
    """Testy pomocné funkce zpracovávající jeden projekt v atomické DB a Fedora transakci."""

    def setUp(self):
        """Nahradí Projekt, Fedora transakci, ``transaction.atomic`` a ``time.sleep`` mocky."""
        patchers = {
            "projekt": patch.object(tasks, "Projekt"),
            "fedora_transaction": patch.object(tasks, "FedoraTransaction"),
            "transaction": patch.object(tasks, "transaction"),
            "sleep": patch.object(tasks.time, "sleep"),
            "snapshot": patch.object(tasks, "update_single_redis_snapshot"),
        }
        self.mocks = {name: patcher.start() for name, patcher in patchers.items()}
        for patcher in patchers.values():
            self.addCleanup(patcher.stop)
        self.mocks["transaction"].atomic.return_value = contextlib.nullcontext()
        self.items = []

        def _get(pk):
            """Vrací pokaždé nový mock projektu, aby šlo ověřit opětovné načtení."""
            item = MagicMock(name=f"projekt_{pk}")
            item.ident_cely = "C-202100001"
            item.hlavni_katastr = "katastr"
            item.katastry.all.return_value = []
            self.items.append(item)
            return item

        self.mocks["projekt"].objects.get.side_effect = _get
        # ``select_for_update()`` vrací stejný manažer, takže ``get`` zůstává jediným místem načtení projektu.
        self.mocks["projekt"].objects.select_for_update.return_value = self.mocks["projekt"].objects
        self.transactions = []

        def _new_transaction():
            """Vrací pokaždé novou Fedora transakci."""
            tx = MagicMock(name="fedora_transaction")
            tx.uid = f"tx-{len(self.transactions) + 1}"
            self.transactions.append(tx)
            return tx

        self.mocks["fedora_transaction"].side_effect = _new_transaction
        # ``transaction.atomic()`` se musí vytvořit nově pro každý pokus.
        self.mocks["transaction"].atomic.side_effect = lambda: contextlib.nullcontext()

    def _run(self, is_pending=lambda item: True, apply_changes=None):
        """Spustí zpracování projektu s pk 1."""
        return tasks._process_project_in_fedora_transaction(1, is_pending, apply_changes or MagicMock(), LOG_PREFIX)

    def test_success_saves_metadata_inside_atomic_and_closes_fedora_transaction_after(self):
        """Metadata se uloží přímo, signál je potlačen a Fedora transakce se uzavře až po atomic bloku."""
        order = []
        self.mocks["transaction"].atomic.side_effect = None
        atomic = MagicMock()
        atomic.__enter__.side_effect = lambda *a: order.append("atomic_enter")
        atomic.__exit__.side_effect = lambda *a: order.append("atomic_exit") or False
        self.mocks["transaction"].atomic.return_value = atomic
        apply_changes = MagicMock(side_effect=lambda item: order.append("apply"))

        def _save_metadata(tx):
            order.append("save_metadata")

        def _get(pk):
            item = MagicMock()
            item.hlavni_katastr = "katastr"
            item.katastry.all.return_value = []
            item.save_metadata.side_effect = _save_metadata
            self.items.append(item)
            return item

        self.mocks["projekt"].objects.get.side_effect = _get

        def _new_tx():
            tx = MagicMock()
            tx.mark_transaction_as_closed.side_effect = lambda: order.append("fedora_close")
            self.transactions.append(tx)
            return tx

        self.mocks["fedora_transaction"].side_effect = _new_tx
        self.mocks["snapshot"].delay.side_effect = lambda *a: order.append("snapshot")

        self.assertTrue(self._run(apply_changes=apply_changes))

        self.assertEqual(order, ["atomic_enter", "apply", "save_metadata", "atomic_exit", "snapshot", "fedora_close"])
        item = self.items[0]
        self.assertIs(item.suppress_signal, True)
        item.save.assert_called_once_with()
        item.save_metadata.assert_called_once_with(self.transactions[0])
        self.assertIs(item.active_transaction, self.transactions[0])

    def test_project_is_loaded_with_row_lock_inside_atomic_block(self):
        """Projekt se načítá s ``select_for_update()`` uvnitř atomic bloku, aby ověření stavu proběhlo pod zámkem."""
        order = []
        atomic = MagicMock()
        atomic.__enter__.side_effect = lambda *a: order.append("atomic_enter")
        atomic.__exit__.side_effect = lambda *a: order.append("atomic_exit") or False
        self.mocks["transaction"].atomic.side_effect = None
        self.mocks["transaction"].atomic.return_value = atomic
        self.mocks["projekt"].objects.select_for_update.side_effect = (
            lambda **kwargs: order.append("lock") or self.mocks["projekt"].objects
        )

        self.assertTrue(self._run(is_pending=lambda item: order.append("is_pending") or True))

        self.assertEqual(order[:3], ["atomic_enter", "lock", "is_pending"])
        self.mocks["projekt"].objects.select_for_update.assert_called_once_with(nowait=True)

    def _lock_error(self, pgcode):
        """Nastaví ``select_for_update`` tak, aby selhalo chybou ``OperationalError`` s daným kódem ovladače."""
        cause = Exception("driver error")
        cause.pgcode = pgcode
        error = OperationalError("could not obtain lock")
        error.__cause__ = cause
        self.mocks["projekt"].objects.select_for_update.side_effect = error

    def test_row_locked_by_another_transaction_skips_project_without_fedora_transaction(self):
        """Řádek držený jinou transakcí se přeskočí s varováním; Fedora transakce ani zápisy nevzniknou."""
        self._lock_error(tasks.PG_LOCK_NOT_AVAILABLE)
        apply_changes = MagicMock()

        with self.assertLogs(tasks.logger, level="WARNING") as logs:
            self.assertFalse(self._run(apply_changes=apply_changes))

        apply_changes.assert_not_called()
        self.mocks["fedora_transaction"].assert_not_called()
        self.mocks["sleep"].assert_not_called()
        self.mocks["snapshot"].delay.assert_not_called()
        self.assertTrue(any(f"{LOG_PREFIX}.do.project.locked_skipped" in line for line in logs.output))

    def test_other_operational_error_on_lock_is_logged_as_error_not_as_skip(self):
        """Jiná chyba DB při zamykání (např. ztráta spojení) se nezamění za držený zámek a zaloguje se jako chyba."""
        self._lock_error("08006")

        with self.assertLogs(tasks.logger, level="WARNING") as logs:
            self.assertFalse(self._run())

        self.assertFalse(any("locked_skipped" in line for line in logs.output))
        self.assertTrue(any(f"{LOG_PREFIX}.do.project.error" in line for line in logs.output))

    def test_snapshot_is_refreshed_once_after_commit(self):
        """Po úspěšném commitu se jednou zařadí obnova Redis snapshotu projektu."""
        self.assertTrue(self._run())

        self.mocks["snapshot"].delay.assert_called_once_with("Projekt", 1)

    def test_snapshot_is_not_refreshed_when_project_is_skipped_or_fails(self):
        """Při přeskočení projektu ani při chybě před commitem se snapshot neobnovuje."""
        self._run(is_pending=lambda item: False)
        with self.assertLogs(tasks.logger, level="ERROR"):
            self._run(apply_changes=MagicMock(side_effect=RuntimeError("boom")))

        self.mocks["snapshot"].delay.assert_not_called()

    def test_snapshot_enqueue_failure_does_not_fail_committed_project(self):
        """Chyba při zařazení snapshotu se jen zaloguje, potvrzený projekt zůstane zpracovaný."""
        self.mocks["snapshot"].delay.side_effect = RuntimeError("broker down")

        with self.assertLogs(tasks.logger, level="WARNING") as logs:
            self.assertTrue(self._run())

        self.assertTrue(any("snapshot_refresh_failed" in line for line in logs.output))
        self.transactions[0].mark_transaction_as_closed.assert_called_once_with()

    def test_main_cadastre_is_removed_from_additional_cadastres(self):
        """Hlavní katastr se před uložením metadat odebere z m2m pole, jak to dělal signál."""
        self.mocks["projekt"].objects.get.side_effect = None
        item = MagicMock()
        item.hlavni_katastr = "katastr"
        item.katastry.all.return_value = ["katastr"]
        self.mocks["projekt"].objects.get.return_value = item

        self.assertTrue(self._run())

        item.katastry.remove.assert_called_once_with("katastr")

    def test_not_pending_project_is_skipped_without_fedora_transaction(self):
        """Projekt zpracovaný jiným během se přeskočí a nezačne se pro něj Fedora transakce."""
        apply_changes = MagicMock()

        self.assertFalse(self._run(is_pending=lambda item: False, apply_changes=apply_changes))

        apply_changes.assert_not_called()
        self.mocks["fedora_transaction"].assert_not_called()

    def test_conflict_is_retried_with_fresh_project_and_transaction(self):
        """Po HTTP 409 se projekt načte znovu, vznikne nová Fedora transakce a druhý pokus uspěje."""
        failing_first = {"done": False}

        def _get(pk):
            item = MagicMock()
            item.hlavni_katastr = "katastr"
            item.katastry.all.return_value = []
            if not failing_first["done"]:
                failing_first["done"] = True
                item.save_metadata.side_effect = _conflict()
            self.items.append(item)
            return item

        self.mocks["projekt"].objects.get.side_effect = _get

        self.assertTrue(self._run())

        self.assertEqual(len(self.items), 2)
        self.assertEqual(len(self.transactions), 2)
        self.mocks["sleep"].assert_called_once_with(tasks.FEDORA_CONFLICT_RETRY_DELAY_SECONDS)
        self.transactions[0].mark_transaction_as_closed.assert_not_called()
        self.transactions[0].rollback_transaction.assert_called()
        self.transactions[1].mark_transaction_as_closed.assert_called_once_with()

    def test_conflict_after_all_attempts_returns_false_and_never_closes_transaction(self):
        """Trvalý konflikt skončí po posledním pokusu chybou a Fedora transakce se nikdy neuzavře."""
        self.mocks["projekt"].objects.get.side_effect = None
        item = MagicMock()
        item.hlavni_katastr = "katastr"
        item.katastry.all.return_value = []
        item.save_metadata.side_effect = _conflict()
        self.mocks["projekt"].objects.get.return_value = item

        with self.assertLogs(tasks.logger, level="ERROR") as logs:
            self.assertFalse(self._run())

        self.assertEqual(self.mocks["fedora_transaction"].call_count, tasks.FEDORA_CONFLICT_MAX_ATTEMPTS)
        self.assertEqual(
            self.mocks["sleep"].call_args_list,
            [
                call(tasks.FEDORA_CONFLICT_RETRY_DELAY_SECONDS * attempt)
                for attempt in range(1, tasks.FEDORA_CONFLICT_MAX_ATTEMPTS)
            ],
        )
        for tx in self.transactions:
            tx.mark_transaction_as_closed.assert_not_called()
        self.assertTrue(any(f"{LOG_PREFIX}.do.project.error" in line for line in logs.output))

    def test_other_error_is_not_retried_and_rolls_back_fedora_transaction(self):
        """Jiná chyba se neopakuje, vrátí Fedora transakci zpět a nepřeruší volající."""
        apply_changes = MagicMock(side_effect=RuntimeError("boom"))

        with self.assertLogs(tasks.logger, level="ERROR"):
            self.assertFalse(self._run(apply_changes=apply_changes))

        self.assertEqual(self.mocks["fedora_transaction"].call_count, 1)
        self.mocks["sleep"].assert_not_called()
        self.transactions[0].rollback_transaction.assert_called_once_with()
        self.transactions[0].mark_transaction_as_closed.assert_not_called()

    def test_failed_rollback_does_not_hide_original_error(self):
        """Chyba při vracení Fedora transakce zpět se jen zaloguje a zpracování skončí řízeně."""
        apply_changes = MagicMock(side_effect=RuntimeError("boom"))

        def _new_tx():
            tx = MagicMock()
            tx.rollback_transaction.side_effect = RuntimeError("rollback failed")
            self.transactions.append(tx)
            return tx

        self.mocks["fedora_transaction"].side_effect = _new_tx

        with self.assertLogs(tasks.logger, level="WARNING"):
            self.assertFalse(self._run(apply_changes=apply_changes))


class CronTaskLockTest(SimpleTestCase):
    """Testy zámku proti souběžnému běhu cron úlohy (:func:`cron.zamek.cron_task_lock`)."""

    def _run_lock(self, acquired):
        """Spustí zámek nad falešným kurzorem a vrátí kurzor a hodnotu předanou do těla ``with``."""
        cursor = MagicMock()
        cursor.fetchone.return_value = (acquired,)
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        with patch("django.db.connection", connection):
            with cron_task_lock(123) as value:
                pass
        return cursor, value

    def test_acquired_lock_is_released(self):
        """Získaný zámek se po skončení bloku uvolní stejným klíčem."""
        cursor, value = self._run_lock(True)

        self.assertIs(value, True)
        self.assertEqual(
            [c.args for c in cursor.execute.call_args_list],
            [("SELECT pg_try_advisory_lock(%s)", [123]), ("SELECT pg_advisory_unlock(%s)", [123])],
        )

    def test_not_acquired_lock_is_not_released(self):
        """Nezískaný zámek se neuvolňuje, aby se neshodil zámek držený jinou instancí."""
        cursor, value = self._run_lock(False)

        self.assertIs(value, False)
        self.assertEqual([c.args for c in cursor.execute.call_args_list], [("SELECT pg_try_advisory_lock(%s)", [123])])

    def test_lock_is_released_when_body_raises(self):
        """Zámek se uvolní i při výjimce v těle ``with``."""
        cursor = MagicMock()
        cursor.fetchone.return_value = (True,)
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        with patch("django.db.connection", connection):
            with self.assertRaises(ValueError):
                with cron_task_lock(7):
                    raise ValueError("fail")

        self.assertEqual(cursor.execute.call_args_list[-1].args, ("SELECT pg_advisory_unlock(%s)", [7]))


class DeleteProjectDataTasksTest(SimpleTestCase):
    """Testy chování úloh :func:`cron.tasks.delete_personal_data_canceled_projects` a ``delete_reporter_data_ten_years``."""

    def setUp(self):
        """Nahradí dotaz na projekty a zpracování jednoho projektu mocky."""
        projekt_patcher = patch.object(tasks, "Projekt")
        process_patcher = patch.object(tasks, "_process_project_in_fedora_transaction")
        self.projekt = projekt_patcher.start()
        self.process = process_patcher.start()
        self.addCleanup(projekt_patcher.stop)
        self.addCleanup(process_patcher.stop)
        chain = self.projekt.objects.filter.return_value.filter.return_value
        chain.filter.return_value.distinct.return_value.values_list.return_value = [1, 2, 3]
        chain.distinct.return_value.values_list.return_value = [1, 2, 3]

    @staticmethod
    def _lock(acquired):
        """Vytvoří náhradu ``cron_task_lock`` vracející zadanou hodnotu."""

        @contextlib.contextmanager
        def _lock(key):
            yield acquired

        return _lock

    def test_personal_data_task_skips_when_lock_is_held(self):
        """Druhá instance úlohy se přeskočí, aniž by sáhla na projekty."""
        with patch.object(tasks, "cron_task_lock", self._lock(False)):
            with self.assertLogs(tasks.logger, level="WARNING") as logs:
                tasks.delete_personal_data_canceled_projects()

        self.projekt.objects.filter.assert_not_called()
        self.process.assert_not_called()
        self.assertTrue(any("do.already_running" in line for line in logs.output))

    def test_reporter_data_task_skips_when_lock_is_held(self):
        """Stejné chování platí pro úlohu mazající data oznamovatele po deseti letech."""
        with patch.object(tasks, "cron_task_lock", self._lock(False)):
            with self.assertLogs(tasks.logger, level="WARNING"):
                tasks.delete_reporter_data_ten_years()

        self.projekt.objects.filter.assert_not_called()
        self.process.assert_not_called()

    def test_personal_data_task_continues_after_failed_project(self):
        """Selhání jednoho projektu nezastaví zpracování dalších."""
        self.process.side_effect = [False, True, True]

        with patch.object(tasks, "cron_task_lock", self._lock(True)):
            tasks.delete_personal_data_canceled_projects()

        self.assertEqual([c.args[0] for c in self.process.call_args_list], [1, 2, 3])

    def test_reporter_data_task_continues_after_failed_project(self):
        """Selhání jednoho projektu nezastaví zpracování dalších ani u úlohy po deseti letech."""
        self.process.side_effect = [True, False, True]

        with patch.object(tasks, "cron_task_lock", self._lock(True)):
            tasks.delete_reporter_data_ten_years()

        self.assertEqual([c.args[0] for c in self.process.call_args_list], [1, 2, 3])

    def test_personal_data_task_recognises_already_anonymised_project(self):
        """Projekt s odstraněnými údaji, vrácený ze zrušení nebo nedávno znovu zrušený úloha nepovažuje za čekající."""
        with patch.object(tasks, "cron_task_lock", self._lock(True)):
            tasks.delete_personal_data_canceled_projects()
        is_pending = self.process.call_args_list[0].args[1]

        def _cancelled_project(days_ago):
            """Vytvoří zrušený projekt s oznamovatelem; ``days_ago`` je stáří posledního zrušení (``None`` = bez záznamu)."""
            item = MagicMock()
            item.stav = tasks.PROJEKT_STAV_ZRUSENY
            item.has_oznamovatel.return_value = True
            item.oznamovatel.email = "a@example.org"
            when = None if days_ago is None else datetime.datetime.now() - datetime.timedelta(days=days_ago)
            last_cancel = item.historie.historie.filter.return_value.order_by.return_value.values_list.return_value
            last_cancel.first.return_value = when
            return item

        pending = _cancelled_project(400)
        recancelled = _cancelled_project(10)
        without_cancel_history = _cancelled_project(None)
        restored = MagicMock()
        restored.stav = tasks.PROJEKT_STAV_ZAPSANY
        restored.has_oznamovatel.return_value = True
        restored.oznamovatel.email = "a@example.org"
        done = MagicMock()
        done.stav = tasks.PROJEKT_STAV_ZRUSENY
        done.has_oznamovatel.return_value = True
        done.oznamovatel.email = f"2026-11-07: {tasks.UDAJ_ODSTRANEN}"
        without_reporter = MagicMock()
        without_reporter.stav = tasks.PROJEKT_STAV_ZRUSENY
        without_reporter.has_oznamovatel.return_value = False

        self.assertTrue(is_pending(pending))
        self.assertFalse(is_pending(restored))
        self.assertFalse(is_pending(recancelled))
        self.assertFalse(is_pending(without_cancel_history))
        self.assertFalse(is_pending(done))
        self.assertFalse(is_pending(without_reporter))

    def test_personal_data_task_overwrites_all_reporter_fields_and_archives_documents(self):
        """Změny projektu přepíšou všechny osobní údaje oznamovatele a odstraní dokumentaci."""
        with patch.object(tasks, "cron_task_lock", self._lock(True)):
            tasks.delete_personal_data_canceled_projects()
        apply_changes = self.process.call_args_list[0].args[2]

        item = MagicMock()
        apply_changes(item)

        values = {
            item.oznamovatel.email,
            item.oznamovatel.adresa,
            item.oznamovatel.odpovedna_osoba,
            item.oznamovatel.telefon,
            item.oznamovatel.poznamka,
        }
        self.assertEqual(len(values), 1)
        self.assertIn(tasks.UDAJ_ODSTRANEN, values.pop())
        item.oznamovatel.save.assert_called_once_with()
        item.archive_project_documentation.assert_called_once_with()


class DailyProjectTasksLockTest(SimpleTestCase):
    """Testy zámku úloh :func:`cron.tasks.cancel_old_projects` a ``delete_unsubmited_projects`` proti souběhu."""

    @staticmethod
    def _lock(acquired, keys):
        """Vytvoří náhradu ``cron_task_lock`` vracející zadanou hodnotu a zapisující použité klíče do ``keys``."""

        @contextlib.contextmanager
        def _lock(key):
            keys.append(key)
            yield acquired

        return _lock

    def _assert_skipped(self, task, key):
        """Ověří, že úloha s drženým zámkem zaloguje ``already_running`` a nesáhne na model ``Projekt``."""
        keys = []
        with patch.object(tasks, "Projekt") as model, patch.object(tasks, "cron_task_lock", self._lock(False, keys)):
            with self.assertLogs(tasks.logger, level="WARNING") as logs:
                task()

        model.objects.filter.assert_not_called()
        self.assertEqual(keys, [key])
        self.assertTrue(any("do.already_running" in line for line in logs.output))

    def test_cancel_old_projects_skips_when_lock_is_held(self):
        """Druhá instance úlohy rušící staré projekty se přeskočí."""
        self._assert_skipped(tasks.cancel_old_projects, LOCK_CANCEL_OLD_PROJECTS)

    def test_delete_unsubmited_projects_skips_when_lock_is_held(self):
        """Druhá instance úlohy mazající nepodané projekty se přeskočí."""
        self._assert_skipped(tasks.delete_unsubmited_projects, LOCK_DELETE_UNSUBMITED_PROJECTS)

    def test_lock_keys_are_unique(self):
        """Každá úloha používá vlastní klíč zámku, aby se úlohy navzájem neblokovaly."""
        keys = [
            LOCK_DELETE_PERSONAL_DATA_CANCELED_PROJECTS,
            LOCK_DELETE_REPORTER_DATA_TEN_YEARS,
            LOCK_CANCEL_OLD_PROJECTS,
            LOCK_DELETE_UNSUBMITED_PROJECTS,
        ]
        self.assertEqual(len(keys), len(set(keys)))
