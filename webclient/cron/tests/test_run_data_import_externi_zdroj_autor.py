"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``ExterniZdrojAutorMapper``."""

from unittest.mock import patch

from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from ez.models import ExterniZdrojAutor
from historie.models import Historie

FILE_KEY = "externi_zdroje_autori"


class RunDataImportExterniZdrojAutorTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``ExterniZdrojAutorMapper``."""

    def _base_payload(self, poradi=1) -> dict:
        return {
            "externi_zdroj": self.externi_zdroj.ident_cely,
            "autor": self.osoba.ident_cely,
            "poradi": poradi,
        }

    def test_import_externi_zdroj_autor(self):
        """Ověřuje, že INSERT import vytvoří záznam externi zdroj autor."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(ExterniZdrojAutor.objects.filter(externi_zdroj=self.externi_zdroj, autor=self.osoba).exists())

    def test_update_is_rejected(self):
        """Ověřuje, že UPDATE import záznamu externi zdroj autor je odmítnut."""
        ExterniZdrojAutor.objects.create(externi_zdroj=self.externi_zdroj, autor=self.osoba, poradi=1)

        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(2),
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)

    def test_delete_removes_externi_zdroj_autor(self):
        """Ověřuje, že DELETE import smaže záznam externi zdroj autor."""
        ExterniZdrojAutor.objects.create(externi_zdroj=self.externi_zdroj, autor=self.osoba, poradi=1)

        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"externi_zdroj": self.externi_zdroj.ident_cely, "autor": self.osoba.ident_cely},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(ExterniZdrojAutor.objects.filter(externi_zdroj=self.externi_zdroj, autor=self.osoba).exists())

    def test_duplicate_insert_fails(self):
        """Ověřuje, že duplicitní INSERT import záznamu externi zdroj autor skončí selháním."""
        ExterniZdrojAutor.objects.create(externi_zdroj=self.externi_zdroj, autor=self.osoba, poradi=1)
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu externi zdroj autor označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB.")

        with patch.object(ExterniZdrojAutor, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu externi zdroj autor označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu externi zdroj autor nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_delete_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že DELETE neexistujícího záznamu externi zdroj autor označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"externi_zdroj": self.externi_zdroj.ident_cely, "autor": self.osoba.ident_cely},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu externi zdroj autor nastaví stav failed_lock_lost."""
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
        """Ověřuje, že úspěšný import záznamu externi zdroj autor zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
