"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``UzivatelSpolupraceMapper``."""

from unittest.mock import patch

from core.constants import SPOLUPRACE_AKTIVNI
from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from historie.models import Historie
from pas.models import UzivatelSpoluprace

FILE_KEY = "uzivatele_spoluprace"


class RunDataImportUzivatelSpolupraceTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``UzivatelSpolupraceMapper``."""

    def _base_payload(self) -> dict:
        return {
            "vedouci": self.user.ident_cely,
            "spolupracovnik": self.other_user.ident_cely,
            "stav": SPOLUPRACE_AKTIVNI,
        }

    def _create_existing(self) -> UzivatelSpoluprace:
        spoluprace = UzivatelSpoluprace(vedouci=self.user, spolupracovnik=self.other_user, stav=SPOLUPRACE_AKTIVNI)
        spoluprace.suppress_signal = True
        spoluprace.save()
        return spoluprace

    def test_import_uzivatel_spoluprace(self):
        """Ověřuje, že INSERT import vytvoří záznam uzivatel spoluprace."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(UzivatelSpoluprace.objects.filter(vedouci=self.user, spolupracovnik=self.other_user).exists())

    def test_update_modifies_uzivatel_spoluprace(self):
        """Ověřuje, že UPDATE import upraví záznam uzivatel spoluprace."""
        spoluprace = self._create_existing()
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"id": f"spol-{spoluprace.pk}", "stav": "0"},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_success(fake_redis)
        spoluprace.refresh_from_db()
        self.assertEqual(spoluprace.stav, 0)

    def test_delete_removes_uzivatel_spoluprace(self):
        """Ověřuje, že DELETE import smaže záznam uzivatel spoluprace."""
        spoluprace = self._create_existing()
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"id": f"spol-{spoluprace.pk}"},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(UzivatelSpoluprace.objects.filter(pk=spoluprace.pk).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu uzivatel spoluprace označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB.")

        with patch.object(UzivatelSpoluprace, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu uzivatel spoluprace označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu uzivatel spoluprace nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu uzivatel spoluprace označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"id": "spol-999999", "stav": "0"},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)

    def test_delete_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že DELETE neexistujícího záznamu uzivatel spoluprace označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"id": "spol-999999"},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu uzivatel spoluprace nastaví stav failed_lock_lost."""
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
        """Ověřuje, že úspěšný import záznamu uzivatel spoluprace zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
