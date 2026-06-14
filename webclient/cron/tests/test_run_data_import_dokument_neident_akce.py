"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``NeidentAkceMapper``."""

from unittest.mock import patch

from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from historie.models import Historie
from neidentakce.models import NeidentAkce

FILE_KEY = "dokumenty_neident_akce"


class RunDataImportDokumentNeidentAkceTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``NeidentAkceMapper``."""

    def _base_payload(self) -> dict:
        return {
            "dokument_cast": self.dokument_cast.ident_cely,
            "rok_zahajeni": 2020,
            "rok_ukonceni": 2021,
            "katastr": f"ruian-{self.katastr.kod}",
            "lokalizace": "Lokalizace",
            "popis": "Popis",
            "poznamka": "Poznámka",
            "pian": "PIAN text",
        }

    def _create_existing_neident(self) -> NeidentAkce:
        return NeidentAkce.objects.create(
            dokument_cast=self.dokument_cast,
            rok_zahajeni=1999,
            popis="Původní",
        )

    def test_insert_writes_neident_akce_to_database(self):
        """Ověřuje, že INSERT import zapíše záznam neident akce do databáze."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(NeidentAkce.objects.filter(dokument_cast=self.dokument_cast).exists())

    def test_update_modifies_existing_neident_akce(self):
        """Ověřuje, že UPDATE import upraví existující záznam neident akce."""
        self._create_existing_neident()
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {**self._base_payload(), "popis": "Aktualizovaný popis"},
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_success(fake_redis)
        record = NeidentAkce.objects.get(dokument_cast=self.dokument_cast)
        self.assertEqual(record.popis, "Aktualizovaný popis")

    def test_delete_removes_neident_akce_from_database(self):
        """Ověřuje, že DELETE import smaže záznam neident akce z databáze."""
        self._create_existing_neident()
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"dokument_cast": self.dokument_cast.ident_cely},
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(NeidentAkce.objects.filter(dokument_cast=self.dokument_cast).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu dokument neident akce označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB při ukládání NeidentAkce.")

        with patch.object(NeidentAkce, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu dokument neident akce označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu dokument neident akce nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu dokument neident akce označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {**self._base_payload(), "dokument_cast": "C-FD-991000001-D999"},
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)

    def test_insert_over_existing_record_overwrites_it(self):
        """``NeidentAkce.dokument_cast`` je OneToOneField s ``primary_key=True``.

        Opakovaný INSERT se shodným PK proto stávající řádek přepíše (Django ``save``
        na existující PK = UPDATE). Test ověřuje, že záznam zůstane právě jeden a má
        nové hodnoty.
        """
        self._create_existing_neident()
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        records = NeidentAkce.objects.filter(dokument_cast=self.dokument_cast)
        self.assertEqual(records.count(), 1)
        self.assertEqual(records.first().popis, "Popis")

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu dokument neident akce nastaví stav failed_lock_lost."""
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
        """Ověřuje, že úspěšný import záznamu dokument neident akce zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
