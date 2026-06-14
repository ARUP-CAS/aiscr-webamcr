"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``DokumentJazykMapper``."""

from unittest.mock import patch

from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from dokument.models import DokumentJazyk
from historie.models import Historie

FILE_KEY = "dokumenty_jazyky"


class RunDataImportDokumentJazykTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``DokumentJazykMapper``."""

    def _base_payload(self) -> dict:
        return {"dokument": self.dokument.ident_cely, "jazyk": self.extra_heslars["jazyk"].ident_cely}

    def test_import_dokument_jazyk(self):
        """Ověřuje, že INSERT import vytvoří záznam dokument jazyk."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(DokumentJazyk.objects.filter(dokument=self.dokument).exists())

    def test_update_is_rejected(self):
        """Ověřuje, že UPDATE import záznamu dokument jazyk je odmítnut."""
        DokumentJazyk.objects.create(dokument=self.dokument, jazyk=self.extra_heslars["jazyk"])
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload(), ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self.assert_import_failed(fake_redis)

    def test_delete_removes_dokument_jazyk(self):
        """Ověřuje, že DELETE import smaže záznam dokument jazyk."""
        DokumentJazyk.objects.create(dokument=self.dokument, jazyk=self.extra_heslars["jazyk"])
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload(), ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self.assert_import_success(fake_redis)
        self.assertFalse(DokumentJazyk.objects.filter(dokument=self.dokument).exists())

    def test_duplicate_insert_fails(self):
        """Ověřuje, že duplicitní INSERT import záznamu dokument jazyk skončí selháním."""
        DokumentJazyk.objects.create(dokument=self.dokument, jazyk=self.extra_heslars["jazyk"])
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_missing_jazyk_fails(self):
        """Ověřuje, že chybějící jazyk při importu záznamu dokument jazyk způsobí selhání."""
        fake_redis, _ = self.run_import(FILE_KEY, {"dokument": self.dokument.ident_cely, "jazyk": "HES-REM-NOTFOUND"})

        self.assert_import_failed(fake_redis)

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu dokument jazyk označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB.")

        with patch.object(DokumentJazyk, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu dokument jazyk označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu dokument jazyk nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_delete_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že DELETE neexistujícího záznamu dokument jazyk označí import jako selhaný."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload(), ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu dokument jazyk nastaví stav failed_lock_lost."""
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
        """Ověřuje, že úspěšný import záznamu dokument jazyk zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
