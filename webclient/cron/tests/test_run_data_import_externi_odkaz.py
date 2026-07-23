"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``ExterniOdkazMapper``."""

from unittest.mock import patch

from arch_z.models import ExterniOdkaz
from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from historie.models import Historie

FILE_KEY = "externi_odkazy"


class RunDataImportExterniOdkazTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``ExterniOdkazMapper``."""

    def _base_payload(self) -> dict:
        return {
            "externi_zdroj": self.externi_zdroj.ident_cely,
            "archeologicky_zaznam": self.az.ident_cely,
            "paginace": "5",
        }

    def _create_existing_odkaz(self) -> ExterniOdkaz:
        odkaz = ExterniOdkaz(externi_zdroj=self.externi_zdroj, archeologicky_zaznam=self.az, paginace="5")
        odkaz.suppress_signal = True
        odkaz.save()
        return odkaz

    def test_import_externi_odkaz(self):
        """Ověřuje, že INSERT import vytvoří záznam externi odkaz."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(
            ExterniOdkaz.objects.filter(externi_zdroj=self.externi_zdroj, archeologicky_zaznam=self.az).exists()
        )

    def test_update_modifies_externi_odkaz(self):
        """Ověřuje, že UPDATE import upraví záznam externi odkaz."""
        odkaz = self._create_existing_odkaz()
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"id": f"exto-{odkaz.pk}", "paginace": "10"},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_success(fake_redis)
        odkaz.refresh_from_db()
        self.assertEqual(odkaz.paginace, "10")

    def test_delete_removes_externi_odkaz(self):
        """Ověřuje, že DELETE import smaže záznam externi odkaz."""
        odkaz = self._create_existing_odkaz()
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"id": f"exto-{odkaz.pk}"},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(ExterniOdkaz.objects.filter(pk=odkaz.pk).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu externi odkaz označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB.")

        with patch.object(ExterniOdkaz, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu externi odkaz označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu externi odkaz nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu externi odkaz označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"id": "exto-999999", "paginace": "99"},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)

    def test_delete_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že DELETE neexistujícího záznamu externi odkaz označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"id": "exto-999999"},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu externi odkaz nastaví stav failed_lock_lost."""
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
        """Ověřuje, že úspěšný import záznamu externi odkaz zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
