"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``KomponentaMapper``."""

from unittest.mock import patch

from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from historie.models import Historie
from komponenta.models import Komponenta

FILE_KEY = "komponenty"


class RunDataImportKomponentaTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``KomponentaMapper``."""

    def _base_payload(self, ident_cely="C-202399001A-K002") -> dict:
        return {
            "ident_cely": ident_cely,
            "vazba": self.dj.ident_cely,
            "obdobi": self.extra_heslars["obdobi"].ident_cely,
            "areal": self.extra_heslars["areal"].ident_cely,
            "jistota": True,
            "presna_datace": "Datace",
            "poznamka": "Komponenta",
        }

    def test_import_komponenta(self):
        """Ověřuje, že INSERT import vytvoří záznam komponenta."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(Komponenta.objects.filter(ident_cely="C-202399001A-K002").exists())

    def test_update_modifies_komponenta(self):
        """Ověřuje, že UPDATE import upraví záznam komponenta."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"ident_cely": self.komponenta.ident_cely, "poznamka": "Upravená komponenta"},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_success(fake_redis)
        self.komponenta.refresh_from_db()
        self.assertEqual(self.komponenta.poznamka, "Upravená komponenta")

    def test_delete_removes_komponenta(self):
        """Ověřuje, že DELETE import smaže záznam komponenta."""
        komponenta = self._create_komponenta("C-202399001A-K003")

        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"ident_cely": komponenta.ident_cely},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(Komponenta.objects.filter(pk=komponenta.pk).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu komponenta označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB při ukládání Komponenty.")

        with patch.object(Komponenta, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu komponenta označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_failure_mid_batch_rolls_back_all_inserted_records(self):
        """Ověřuje, že selhání uprostřed dávky vrátí vložené záznamy komponenta zpět."""
        call_count = {"n": 0}
        original_save = Komponenta.save

        def failing_second_save(self, *args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise RuntimeError("Simulované selhání druhého záznamu.")
            return original_save(self, *args, **kwargs)

        with patch.object(Komponenta, "save", failing_second_save):
            fake_redis, _ = self.run_import_records(
                FILE_KEY,
                [
                    self._base_payload("C-202399001A-K010"),
                    self._base_payload("C-202399001A-K011"),
                    self._base_payload("C-202399001A-K012"),
                ],
            )

        self.assert_import_failed(fake_redis)
        self.assertFalse(
            Komponenta.objects.filter(
                ident_cely__in=["C-202399001A-K010", "C-202399001A-K011", "C-202399001A-K012"]
            ).exists()
        )

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu komponenta nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu komponenta označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"ident_cely": "C-NOEXIST-K999", "poznamka": "ghost"},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)

    def test_insert_of_duplicate_ident_marks_import_as_failed(self):
        """Ověřuje, že INSERT duplicitního ident pro záznam komponenta označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(self.komponenta.ident_cely),
        )

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu komponenta nastaví stav failed_lock_lost."""
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
        """Ověřuje, že úspěšný import záznamu komponenta zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
