"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``LetMapper``."""

from unittest.mock import patch

from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from dokument.models import Let
from historie.models import Historie

FILE_KEY = "dokumenty_lety"


class RunDataImportDokumentLetTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``LetMapper``."""

    def _base_payload(self, ident_cely="C-LET-991002") -> dict:
        return {
            "ident_cely": ident_cely,
            "uzivatelske_oznaceni": "LET-1",
            "datum": "2024-01-02",
            "hodina_zacatek": "10:00",
            "hodina_konec": "11:00",
            "fotoaparat": "Canon",
            "pilot": "Pilot",
            "typ_letounu": "Cessna",
            "ucel_letu": "Dokumentace",
            "letiste_start": self.extra_heslars["letiste"].ident_cely,
            "letiste_cil": self.extra_heslars["letiste"].ident_cely,
            "pozorovatel": self.osoba.ident_cely,
            "organizace": self.organizace.ident_cely,
            "pocasi": self.extra_heslars["pocasi"].ident_cely,
            "dohlednost": self.extra_heslars["dohlednost"].ident_cely,
        }

    def test_import_dokument_let(self):
        """Ověřuje, že INSERT import vytvoří záznam dokument let."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(Let.objects.filter(ident_cely="C-LET-991002").exists())

    def test_update_modifies_dokument_let(self):
        """Ověřuje, že UPDATE import upraví záznam dokument let."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"ident_cely": self.let.ident_cely, "pilot": "Nový pilot"},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_success(fake_redis)
        self.let.refresh_from_db()
        self.assertEqual(self.let.pilot, "Nový pilot")

    def test_delete_removes_dokument_let(self):
        """Ověřuje, že DELETE import smaže záznam dokument let."""
        let = self._create_let("C-LET-991003")
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"ident_cely": let.ident_cely},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(Let.objects.filter(pk=let.pk).exists())

    def test_missing_letiste_fails(self):
        """Ověřuje, že chybějící letiste při importu záznamu dokument let způsobí selhání."""
        payload = self._base_payload("C-LET-991004")
        payload["letiste_start"] = "HES-REM-NOTFOUND"
        fake_redis, _ = self.run_import(FILE_KEY, payload)

        self.assert_import_failed(fake_redis)

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu dokument let označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB.")

        with patch.object(Let, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """``DokumentLetMapper.get_record_history`` vrací default ``None`` — historie loop tedy
        nikdy neběží. Pro účely testu vrátíme samotný záznam, aby ``Historie.save`` bylo voláno.
        """
        from core.import_data_mappers import DokumentLetMapper

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(DokumentLetMapper, "get_record_history", staticmethod(lambda record: record)), patch.object(
            Historie, "save", failing_save
        ):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu dokument let nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu dokument let označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"ident_cely": "C-LET-NOEXIST", "pilot": "ghost"},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)

    def test_duplicate_insert_fails(self):
        """Ověřuje, že duplicitní INSERT import záznamu dokument let skončí selháním."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload(self.let.ident_cely))

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu dokument let nastaví stav failed_lock_lost."""
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
        """Ověřuje, že úspěšný import záznamu dokument let zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
