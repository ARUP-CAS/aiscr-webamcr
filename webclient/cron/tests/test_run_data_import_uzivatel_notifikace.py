"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``UzivatelNotifikaceMapper``."""

from unittest.mock import patch

from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from historie.models import Historie

FILE_KEY = "uzivatele_notifikace"


class RunDataImportUzivatelNotifikaceTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``UzivatelNotifikaceMapper``."""

    def _base_payload(self) -> dict:
        return {"uzivatel": self.other_user.ident_cely, "notifikace": self.notification_type.ident_cely}

    def test_import_uzivatel_notifikace(self):
        """Ověřuje, že INSERT import vytvoří záznam uzivatel notifikace."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(
            self.other_user.notification_types.filter(ident_cely=self.notification_type.ident_cely).exists()
        )

    def test_update_is_rejected(self):
        """Ověřuje, že UPDATE import záznamu uzivatel notifikace je odmítnut."""
        self.other_user.notification_types.add(self.notification_type)
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload(), ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self.assert_import_failed(fake_redis)

    def test_delete_removes_uzivatel_notifikace(self):
        """Ověřuje, že DELETE import smaže záznam uzivatel notifikace."""
        self.other_user.notification_types.add(self.notification_type)
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload(), ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self.assert_import_success(fake_redis)
        self.assertFalse(
            self.other_user.notification_types.filter(ident_cely=self.notification_type.ident_cely).exists()
        )

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu uzivatel notifikace označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu uzivatel notifikace nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu uzivatel notifikace nastaví stav failed_lock_lost."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            refresh_lock_side_effect=[True, False, False, False, False, False],
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self.assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Ověřuje, že úspěšný import záznamu uzivatel notifikace zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
