"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``HeslarDokumentTypMaterialMapper``."""

from unittest.mock import patch

from core.forms import ImportDataAdminForm
from core.import_data_mappers import HeslarDokumentTypMaterialMapper
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from heslar.models import Heslar, HeslarDokumentTypMaterial
from historie.models import Historie

FILE_KEY = "heslar_dokument_typ_material"


class RunDataImportHeslarDokumentTypMaterialTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``HeslarDokumentTypMaterialMapper``."""

    def _base_payload(self) -> dict:
        return {
            "dokument_typ": self.extra_heslars["doc_typ"].ident_cely,
            "dokument_material": self.extra_heslars["doc_material"].ident_cely,
        }

    def _create_existing_record(self) -> HeslarDokumentTypMaterial:
        return HeslarDokumentTypMaterial.objects.create(
            dokument_typ=self.extra_heslars["doc_typ"],
            dokument_material=self.extra_heslars["doc_material"],
        )

    def test_insert_writes_record_to_database(self):
        """Ověřuje, že INSERT import vytvoří záznam heslar dokument typ material."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(
            HeslarDokumentTypMaterial.objects.filter(
                dokument_typ=self.extra_heslars["doc_typ"],
                dokument_material=self.extra_heslars["doc_material"],
            ).exists()
        )

    def test_update_modifies_existing_record(self):
        """Ověřuje, že UPDATE import přijme existující záznam heslar dokument typ material."""
        existing = self._create_existing_record()
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"id": f"hdtm-{existing.pk}", **self._base_payload()},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_success(fake_redis)
        self.assertTrue(HeslarDokumentTypMaterial.objects.filter(pk=existing.pk).exists())

    def test_delete_removes_record(self):
        """Ověřuje, že DELETE import odstraní záznam heslar dokument typ material."""
        existing = self._create_existing_record()
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"id": f"hdtm-{existing.pk}"},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(HeslarDokumentTypMaterial.objects.filter(pk=existing.pk).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání DB.")

        with patch.object(HeslarDokumentTypMaterial, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání Historie.")

        with patch.object(
            HeslarDokumentTypMaterialMapper,
            "get_record_history",
            staticmethod(lambda record: record),
        ), patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení metadat Fedory označí import jako selhaný."""

        def failing_save_metadata(self, *args, **kwargs):
            raise RuntimeError("Selhání Fedory.")

        # Tento mapper sám nevyžaduje aktualizaci Fedora metadat. Vynucený cíl ověří,
        # že jeho průchod společnou Fedora fází správně propaguje selhání.
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            save_metadata_side_effect=failing_save_metadata,
            extra_patches=[
                patch.object(
                    HeslarDokumentTypMaterialMapper,
                    "fedora_update_targets",
                    return_value={(Heslar, self.extra_heslars["doc_typ"].pk)},
                )
            ],
        )

        self.assert_import_failed(fake_redis)

    def test_failure_mid_batch_rolls_back_all_inserted_records(self):
        """Ověřuje, že selhání uprostřed dávky vrátí všechny vložené záznamy zpět."""
        fake_redis, _ = self.run_import_records(FILE_KEY, [self._base_payload(), self._base_payload()])

        self.assertFalse(
            HeslarDokumentTypMaterial.objects.filter(
                dokument_typ=self.extra_heslars["doc_typ"],
                dokument_material=self.extra_heslars["doc_material"],
            ).exists()
        )
        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu nastaví stav stopped_by_user."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"id": "hdtm-9999999", **self._base_payload()},
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)

    def test_insert_of_duplicate_combination_marks_import_as_failed(self):
        """Ověřuje, že duplicitní INSERT kombinace označí import jako selhaný."""
        self._create_existing_record()
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku nastaví stav failed_lock_lost."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            refresh_lock_side_effect=[True, False, False, False, False],
        )

        status_raw = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self.assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Ověřuje, že úspěšný import zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_tr_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
