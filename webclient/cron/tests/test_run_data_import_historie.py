"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``HistorieMapper``."""

from unittest.mock import patch

from core.constants import IMPORT
from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from historie.models import Historie

HISTORIE_FILE_KEY = "historie"


class RunDataImportHistorieTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``HistorieMapper``."""

    def _base_payload(self) -> dict:
        return {
            "vazba": self.dokument.ident_cely,
            "uzivatel": self.user.ident_cely,
            "datum_zmeny": "2024-01-02 10:00:00",
            "typ_zmeny": IMPORT,
            "poznamka": "Import historie",
        }

    def _create_existing_historie(self) -> Historie:
        return Historie.objects.create(
            typ_zmeny=IMPORT,
            uzivatel=self.user,
            vazba=self.dokument.historie,
            poznamka="Původní",
        )

    def test_insert_writes_historie_to_database(self):
        """Ověřuje, že INSERT import zapíše záznam historie do databáze."""
        fake_redis, _ = self.run_import(HISTORIE_FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(Historie.objects.filter(poznamka="Import historie").exists())

    def test_update_modifies_existing_historie(self):
        """Ověřuje, že UPDATE import upraví existující záznam historie."""
        existing = self._create_existing_historie()
        fake_redis, _ = self.run_import(
            HISTORIE_FILE_KEY,
            {"id": f"hist-{existing.id}", **self._base_payload(), "poznamka": "Updated"},
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_success(fake_redis)
        existing.refresh_from_db()
        self.assertEqual(existing.poznamka, "Updated")

    def test_delete_removes_historie_from_database(self):
        """Ověřuje, že DELETE import smaže záznam historie z databáze."""
        existing = self._create_existing_historie()
        fake_redis, _ = self.run_import(
            HISTORIE_FILE_KEY,
            {"id": f"hist-{existing.id}"},
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(Historie.objects.filter(pk=existing.pk).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu historie označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB při ukládání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(HISTORIE_FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_failure_mid_batch_rolls_back_all_inserted_records(self):
        """Ověřuje, že selhání uprostřed dávky vrátí vložené záznamy historie zpět."""
        call_count = {"n": 0}
        original_save = Historie.save

        def failing_second_save(self, *args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise RuntimeError("Simulované selhání druhého záznamu.")
            return original_save(self, *args, **kwargs)

        with patch.object(Historie, "save", failing_second_save):
            fake_redis, _ = self.run_import_records(
                HISTORIE_FILE_KEY,
                [
                    {**self._base_payload(), "poznamka": "batch-1"},
                    {**self._base_payload(), "poznamka": "batch-2"},
                    {**self._base_payload(), "poznamka": "batch-3"},
                ],
            )

        self.assert_import_failed(fake_redis)
        self.assertFalse(
            Historie.objects.filter(poznamka__in=["batch-1", "batch-2", "batch-3"]).exists(),
        )

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu historie nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            HISTORIE_FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu historie označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            HISTORIE_FILE_KEY,
            {"id": "hist-999999", **self._base_payload()},
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)

    def test_delete_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že DELETE neexistujícího záznamu historie označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            HISTORIE_FILE_KEY,
            {"id": "hist-999999"},
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu historie nastaví stav failed_lock_lost."""
        fake_redis, _ = self.run_import(
            HISTORIE_FILE_KEY,
            self._base_payload(),
            refresh_lock_side_effect=[True, False, False, False, False, False],
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self.assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Ověřuje, že úspěšný import záznamu historie zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(HISTORIE_FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
