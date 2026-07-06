"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``DokumentMapper``."""

from unittest.mock import patch

from core.constants import D_STAV_ZAPSANY
from core.forms import ImportDataAdminForm
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from dokument.models import Dokument, DokumentExtraData
from historie.models import Historie

FILE_KEY = "dokumenty"


class RunDataImportDokumentTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``DokumentMapper``."""

    def _base_payload(self, ident_cely="C-FD-991000002") -> dict:
        return {
            "ident_cely": ident_cely,
            "doi": None,
            "let": self.let.ident_cely,
            "typ_dokumentu": self.extra_heslars["doc_typ"].ident_cely,
            "material_originalu": self.extra_heslars["doc_material"].ident_cely,
            "rada": self.extra_heslars["doc_rada"].ident_cely,
            "organizace": self.organizace.ident_cely,
            "pristupnost": self.base_heslars["pristupnost"].ident_cely,
            "ulozeni_originalu": self.extra_heslars["doc_ulozeni"].ident_cely,
            "licence": self.base_heslars["licence"].ident_cely,
            "stav": D_STAV_ZAPSANY,
            "rok_vzniku": 2024,
            "datum_zverejneni": None,
            "oznaceni_originalu": "ORIG-1",
            "popis": "Popis",
            "poznamka": "Poznámka",
            "cislo_objektu": "1",
            "meritko": "1:100",
            "vyska": 10,
            "sirka": 20,
            "pocet_variant_originalu": 1,
            "odkaz": None,
            "datum_vzniku": "2024-01-02",
            "udalost": "Událost",
            "region": "Region",
            "rok_od": 2020,
            "rok_do": 2024,
            "duveryhodnost": 90,
            "geom_system": "4326",
            "geom": "SRID=4326;POINT(14.5 50.0)",
            "geom_sjtsk": None,
            "format": self.extra_heslars["doc_format"].ident_cely,
            "zachovalost": self.extra_heslars["doc_zachovalost"].ident_cely,
            "nahrada": self.extra_heslars["doc_nahrada"].ident_cely,
            "udalost_typ": self.extra_heslars["udalost_typ"].ident_cely,
            "zeme": self.extra_heslars["zeme"].ident_cely,
        }

    def test_import_dokument(self):
        """Ověřuje, že INSERT import vytvoří záznam dokument."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(Dokument.objects.filter(ident_cely="C-FD-991000002").exists())
        self.assertTrue(DokumentExtraData.objects.filter(dokument__ident_cely="C-FD-991000002").exists())

    def test_delete_removes_dokument(self):
        """Ověřuje, že DELETE import smaže záznam dokument."""
        dokument = self._create_dokument("C-FD-991000003")
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"ident_cely": dokument.ident_cely},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(Dokument.objects.filter(pk=dokument.pk).exists())

    def test_duplicate_insert_fails(self):
        """Ověřuje, že duplicitní INSERT import záznamu dokument skončí selháním."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload(self.dokument.ident_cely))

        self.assert_import_failed(fake_redis)

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu dokument označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB.")

        with patch.object(Dokument, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu dokument označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení metadat Fedory pro záznam dokument označí import jako selhaný."""

        def failing_save_metadata(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Fedora.")

        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            save_metadata_side_effect=failing_save_metadata,
        )

        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu dokument nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu dokument označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload("C-NOEXIST-DOC"),
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)

    def test_partial_update_only_ident_cely_and_poznamka(self):
        """Ověřuje, že partial UPDATE s pouze ident_cely a poznamka neselže na KeyError a aktualizuje pole."""
        original_poznamka = self.dokument.poznamka
        new_poznamka = "Nová poznámka z partial UPDATE"
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"ident_cely": self.dokument.ident_cely, "poznamka": new_poznamka},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_success(fake_redis)
        self.dokument.refresh_from_db()
        self.assertEqual(self.dokument.poznamka, new_poznamka)
        self.assertNotEqual(self.dokument.poznamka, original_poznamka)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu dokument nastaví stav failed_lock_lost."""
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
        """Ověřuje, že úspěšný import záznamu dokument zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
