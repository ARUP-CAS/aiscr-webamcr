"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``ExterniZdrojMapper``."""

from unittest.mock import patch

from core.constants import EZ_STAV_ZAPSANY
from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from ez.models import ExterniZdroj
from historie.models import Historie

FILE_KEY = "externi_zdroje"


class RunDataImportExterniZdrojTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``ExterniZdrojMapper``."""

    def _base_payload(self, ident_cely="BIB-9910002") -> dict:
        return {
            "ident_cely": ident_cely,
            "doi": None,
            "typ": self.extra_heslars["ez_typ"].ident_cely,
            "stav": EZ_STAV_ZAPSANY,
            "rok_vydani_vzniku": "2024",
            "nazev": "Externí zdroj",
            "sbornik_nazev": None,
            "edice_rada": None,
            "casopis_denik_nazev": None,
            "casopis_rocnik": None,
            "isbn": None,
            "issn": None,
            "misto": "Praha",
            "vydavatel": "ARUP",
            "datum_rd": None,
            "paginace_titulu": "1-2",
            "link": None,
            "organizace": "ARUP",
            "typ_dokumentu": self.extra_heslars["doc_typ"].ident_cely,
            "poznamka": "Poznámka",
        }

    def test_import_externi_zdroj(self):
        """Ověřuje, že INSERT import vytvoří záznam externi zdroj."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(ExterniZdroj.objects.filter(ident_cely="BIB-9910002").exists())

    def test_update_modifies_externi_zdroj(self):
        """Ověřuje, že UPDATE import upraví záznam externi zdroj."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"ident_cely": self.externi_zdroj.ident_cely, "nazev": "Upravený externí zdroj"},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_success(fake_redis)
        self.externi_zdroj.refresh_from_db()
        self.assertEqual(self.externi_zdroj.nazev, "Upravený externí zdroj")

    def test_delete_removes_externi_zdroj(self):
        """Ověřuje, že DELETE import smaže záznam externi zdroj."""
        ez = self._create_externi_zdroj("BIB-9910003")

        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"ident_cely": ez.ident_cely},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(ExterniZdroj.objects.filter(pk=ez.pk).exists())

    def test_duplicate_insert_fails(self):
        """Ověřuje, že duplicitní INSERT import záznamu externi zdroj skončí selháním."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload(self.externi_zdroj.ident_cely))

        self.assert_import_failed(fake_redis)

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu externi zdroj označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB.")

        with patch.object(ExterniZdroj, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu externi zdroj označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení metadat Fedory pro záznam externi zdroj označí import jako selhaný."""

        def failing_save_metadata(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Fedora.")

        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            save_metadata_side_effect=failing_save_metadata,
        )

        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu externi zdroj nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu externi zdroj označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"ident_cely": "BIB-NOEXIST", "nazev": "ghost"},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu externi zdroj nastaví stav failed_lock_lost."""
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
        """Ověřuje, že úspěšný import záznamu externi zdroj zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
