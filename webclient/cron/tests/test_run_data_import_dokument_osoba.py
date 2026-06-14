"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``DokumentOsobaMapper``."""

from unittest.mock import patch

from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from dokument.models import DokumentOsoba
from historie.models import Historie

FILE_KEY = "dokumenty_osoby"


class RunDataImportDokumentOsobaTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``DokumentOsobaMapper``."""

    def _base_payload(self) -> dict:
        return {"dokument": self.dokument.ident_cely, "osoba": self.osoba.ident_cely}

    def test_import_dokument_osoba(self):
        """Ověřuje, že INSERT import vytvoří záznam dokument osoba."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(DokumentOsoba.objects.filter(dokument=self.dokument, osoba=self.osoba).exists())

    def test_update_is_rejected(self):
        """Ověřuje, že UPDATE import záznamu dokument osoba je odmítnut."""
        DokumentOsoba.objects.create(dokument=self.dokument, osoba=self.osoba)
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload(), ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self.assert_import_failed(fake_redis)

    def test_delete_removes_dokument_osoba(self):
        """Ověřuje, že DELETE import smaže záznam dokument osoba."""
        DokumentOsoba.objects.create(dokument=self.dokument, osoba=self.osoba)
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload(), ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self.assert_import_success(fake_redis)
        self.assertFalse(DokumentOsoba.objects.filter(dokument=self.dokument, osoba=self.osoba).exists())

    def test_duplicate_insert_fails(self):
        """Ověřuje, že duplicitní INSERT import záznamu dokument osoba skončí selháním."""
        DokumentOsoba.objects.create(dokument=self.dokument, osoba=self.osoba)
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu dokument osoba označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB.")

        with patch.object(DokumentOsoba, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu dokument osoba označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu dokument osoba nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_delete_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že DELETE neexistujícího záznamu dokument osoba označí import jako selhaný."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload(), ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu dokument osoba nastaví stav failed_lock_lost."""
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
        """Ověřuje, že úspěšný import záznamu dokument osoba zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
