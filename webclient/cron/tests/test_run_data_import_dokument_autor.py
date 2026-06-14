"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``DokumentAutorMapper``."""

from unittest.mock import patch

from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from dokument.models import DokumentAutor
from historie.models import Historie

FILE_KEY = "dokumenty_autori"


class RunDataImportDokumentAutorTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``DokumentAutorMapper``."""

    def _base_payload(self, poradi=1) -> dict:
        return {"dokument": self.dokument.ident_cely, "autor": self.osoba.ident_cely, "poradi": poradi}

    def test_import_dokument_autor(self):
        """Ověřuje, že INSERT import vytvoří záznam dokument autor."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(DokumentAutor.objects.filter(dokument=self.dokument, autor=self.osoba).exists())

    def test_update_is_rejected(self):
        """Ověřuje, že UPDATE import záznamu dokument autor je odmítnut."""
        DokumentAutor.objects.create(dokument=self.dokument, autor=self.osoba, poradi=1)

        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload(2), ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self.assert_import_failed(fake_redis)

    def test_delete_removes_dokument_autor(self):
        """Ověřuje, že DELETE import smaže záznam dokument autor."""
        DokumentAutor.objects.create(dokument=self.dokument, autor=self.osoba, poradi=1)

        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"dokument": self.dokument.ident_cely, "autor": self.osoba.ident_cely},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(DokumentAutor.objects.filter(dokument=self.dokument, autor=self.osoba).exists())

    def test_duplicate_insert_fails(self):
        """Ověřuje, že duplicitní INSERT import záznamu dokument autor skončí selháním."""
        DokumentAutor.objects.create(dokument=self.dokument, autor=self.osoba, poradi=1)
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_missing_dokument_fails(self):
        """Ověřuje, že chybějící dokument při importu záznamu dokument autor způsobí selhání."""
        fake_redis, _ = self.run_import(
            FILE_KEY, {"dokument": "C-FD-000000999", "autor": self.osoba.ident_cely, "poradi": 1}
        )

        self.assert_import_failed(fake_redis)

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu dokument autor označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB.")

        with patch.object(DokumentAutor, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu dokument autor označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu dokument autor nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_delete_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že DELETE neexistujícího záznamu dokument autor označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"dokument": self.dokument.ident_cely, "autor": self.osoba.ident_cely},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu dokument autor nastaví stav failed_lock_lost."""
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
        """Ověřuje, že úspěšný import záznamu dokument autor zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
