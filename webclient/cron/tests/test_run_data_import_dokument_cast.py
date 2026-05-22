"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``DokumentCastMapper``."""

from unittest.mock import patch

from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from dokument.models import DokumentCast
from historie.models import Historie

FILE_KEY = "dokumenty_casti"


class RunDataImportDokumentCastTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``DokumentCastMapper``."""

    def _base_payload(self, ident_cely="C-FD-991000001-D002") -> dict:
        return {
            "ident_cely": ident_cely,
            "dokument": self.dokument.ident_cely,
            "archeologicky_zaznam": self.az.ident_cely,
            "projekt": None,
            "poznamka": "Část",
        }

    def test_import_dokument_cast(self):
        """Ověřuje, že INSERT import vytvoří záznam dokument cast."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(DokumentCast.objects.filter(ident_cely="C-FD-991000001-D002").exists())

    def test_update_modifies_dokument_cast(self):
        """Ověřuje, že UPDATE import upraví záznam dokument cast."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"ident_cely": self.dokument_cast.ident_cely, "poznamka": "Upravená část"},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_success(fake_redis)
        self.dokument_cast.refresh_from_db()
        self.assertEqual(self.dokument_cast.poznamka, "Upravená část")

    def test_delete_removes_dokument_cast(self):
        """Ověřuje, že DELETE import smaže záznam dokument cast."""
        cast = self._create_dokument_cast("C-FD-991000001-D003")
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"ident_cely": cast.ident_cely},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(DokumentCast.objects.filter(pk=cast.pk).exists())

    def test_duplicate_insert_fails(self):
        """Ověřuje, že duplicitní INSERT import záznamu dokument cast skončí selháním."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload(self.dokument_cast.ident_cely))

        self.assert_import_failed(fake_redis)

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu dokument cast označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB.")

        with patch.object(DokumentCast, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu dokument cast označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu dokument cast nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu dokument cast označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"ident_cely": "C-FD-NOEXIST-D999", "poznamka": "ghost"},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu dokument cast nastaví stav failed_lock_lost."""
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
        """Ověřuje, že úspěšný import záznamu dokument cast zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
