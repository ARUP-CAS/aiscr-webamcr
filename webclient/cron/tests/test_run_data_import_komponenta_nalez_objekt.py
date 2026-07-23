"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``KomponentaNalezObjektMapper``."""

from unittest.mock import patch

from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from historie.models import Historie
from nalez.models import NalezObjekt

FILE_KEY = "komponenty_nalezy_objekty"


class RunDataImportKomponentaNalezObjektTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``KomponentaNalezObjektMapper``."""

    def _base_payload(self) -> dict:
        return {
            "komponenta": self.komponenta.ident_cely,
            "druh": self.extra_heslars["objekt_druh"].ident_cely,
            "specifikace": self.extra_heslars["objekt_specifikace"].ident_cely,
            "pocet": "1",
            "poznamka": "Objekt",
        }

    def _create_existing(self) -> NalezObjekt:
        return NalezObjekt.objects.create(
            komponenta=self.komponenta,
            druh=self.extra_heslars["objekt_druh"],
            specifikace=self.extra_heslars["objekt_specifikace"],
            pocet=1,
        )

    def test_import_komponenta_nalez_objekt(self):
        """Ověřuje, že INSERT import vytvoří záznam komponenta nalez objekt."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(NalezObjekt.objects.filter(komponenta=self.komponenta).exists())

    def test_update_modifies_komponenta_nalez_objekt(self):
        """Ověřuje, že UPDATE import upraví záznam komponenta nalez objekt."""
        nalez = self._create_existing()
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"id": f"nalo-{nalez.pk}", "pocet": "3"},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_success(fake_redis)
        nalez.refresh_from_db()
        self.assertEqual(nalez.pocet, "3")

    def test_delete_removes_komponenta_nalez_objekt(self):
        """Ověřuje, že DELETE import smaže záznam komponenta nalez objekt."""
        nalez = self._create_existing()
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"id": f"nalo-{nalez.pk}"},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(NalezObjekt.objects.filter(pk=nalez.pk).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu komponenta nalez objekt označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB.")

        with patch.object(NalezObjekt, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu komponenta nalez objekt označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu komponenta nalez objekt nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu komponenta nalez objekt označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"id": "nalo-999999", "pocet": "5"},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)

    def test_delete_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že DELETE neexistujícího záznamu komponenta nalez objekt označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"id": "nalo-999999"},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu komponenta nalez objekt nastaví stav failed_lock_lost."""
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
        """Ověřuje, že úspěšný import záznamu komponenta nalez objekt zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
