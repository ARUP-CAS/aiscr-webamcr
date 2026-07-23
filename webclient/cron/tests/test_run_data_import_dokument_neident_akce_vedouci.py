"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``NeidentAkceVedouciMapper``."""

from unittest.mock import patch

from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from historie.models import Historie
from neidentakce.models import NeidentAkce, NeidentAkceVedouci

FILE_KEY = "dokumenty_neident_akce_vedouci"


class RunDataImportDokumentNeidentAkceVedouciTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``NeidentAkceVedouciMapper``.

    Mapper má ``allow_update = False`` — testovací matice tedy UPDATE neoveruje
    (kromě negativního testu, kde UPDATE musí být odmítnut).
    """

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená fixture data pro importní testy."""
        super().setUpTestData()
        cls.neident = NeidentAkce.objects.create(dokument_cast=cls.dokument_cast)

    def _base_payload(self) -> dict:
        return {
            "neident_akce": self.dokument_cast.ident_cely,
            "vedouci": self.osoba.ident_cely,
        }

    def _create_existing_vedouci(self) -> NeidentAkceVedouci:
        return NeidentAkceVedouci.objects.create(neident_akce=self.neident, vedouci=self.osoba)

    def test_insert_writes_neident_akce_vedouci_to_database(self):
        """Ověřuje, že INSERT import zapíše záznam neident akce vedouci do databáze."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(NeidentAkceVedouci.objects.filter(neident_akce=self.neident, vedouci=self.osoba).exists())

    def test_update_is_rejected_when_allow_update_is_false(self):
        """``NeidentAkceVedouciMapper.allow_update`` je False — UPDATE musí být odmítnut."""
        self._create_existing_vedouci()
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)

    def test_delete_removes_neident_akce_vedouci_from_database(self):
        """Ověřuje, že DELETE import smaže záznam neident akce vedouci z databáze."""
        existing = self._create_existing_vedouci()
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(NeidentAkceVedouci.objects.filter(pk=existing.pk).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu dokument neident akce vedouci označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB při ukládání NeidentAkceVedouci.")

        with patch.object(NeidentAkceVedouci, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu dokument neident akce vedouci označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu dokument neident akce vedouci nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_delete_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že DELETE neexistujícího záznamu dokument neident akce vedouci označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_failed(fake_redis)

    def test_insert_of_duplicate_record_marks_import_as_failed(self):
        """Ověřuje, že INSERT duplicitního record pro záznam dokument neident akce vedouci označí import jako selhaný."""
        self._create_existing_vedouci()
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu dokument neident akce vedouci nastaví stav failed_lock_lost."""
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
        """Ověřuje, že úspěšný import záznamu dokument neident akce vedouci zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
