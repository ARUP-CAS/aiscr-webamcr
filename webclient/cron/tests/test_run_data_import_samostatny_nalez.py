"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``SamostatnyNalezMapper``."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, mock_open, patch

from core.constants import SN_ZAPSANY
from core.forms import ImportDataAdminForm
from core.models import Soubor
from cron import tasks as cron_tasks
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from historie.models import Historie
from pas.models import SamostatnyNalez

FILE_KEY = "samostatne_nalezy"
SOUBOR_FILE_KEY = "soubory"


class RunDataImportSamostatnyNalezTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``SamostatnyNalezMapper``."""

    def _base_payload(self, ident_cely="C-202399001-N00001") -> dict:
        return {
            "ident_cely": ident_cely,
            "igsn": None,
            "stav": SN_ZAPSANY,
            "evidencni_cislo": "SN-1",
            "projekt": self.projekt.ident_cely,
            "pristupnost": self.base_heslars["pristupnost"].ident_cely,
            "katastr": f"ruian-{self.katastr.kod}",
            "lokalizace": "Lokalizace",
            "geom_system": "4326",
            "geom": "SRID=4326;POINT(14.5 50.0)",
            "geom_sjtsk": None,
            "hloubka": 10,
            "okolnosti": self.extra_heslars["okolnosti"].ident_cely,
            "nalezce": self.osoba.ident_cely,
            "datum_nalezu": "2024-01-02",
            "predano": False,
            "predano_organizace": self.organizace.ident_cely,
            "obdobi": self.extra_heslars["obdobi"].ident_cely,
            "presna_datace": "středověk",
            "druh_nalezu": self.extra_heslars["predmet_druh"].ident_cely,
            "specifikace": self.extra_heslars["predmet_specifikace"].ident_cely,
            "pocet": "1",
            "poznamka": "Poznámka",
        }

    def _create_existing_nalez(self, ident_cely="C-202399001-N99999") -> SamostatnyNalez:
        nalez = SamostatnyNalez(
            ident_cely=ident_cely,
            stav=SN_ZAPSANY,
            projekt=self.projekt,
            pristupnost=self.base_heslars["pristupnost"],
            katastr=self.katastr,
            nalezce=self.osoba,
            obdobi=self.extra_heslars["obdobi"],
            druh_nalezu=self.extra_heslars["predmet_druh"],
        )
        nalez.suppress_signal = True
        nalez.save()
        return nalez

    def _soubor_phase_patches(self):
        """Patche potřebné pro import binárního souboru navázaného na samostatný nález."""
        binary_result = SimpleNamespace(
            size_mb=0.001,
            sha_512="sha",
            url_without_domain="/fedora/import-test.txt",
        )
        connector = MagicMock()
        connector.save_binary_file.return_value = binary_result
        return [
            patch("cron.tasks.os.path.isfile", return_value=True),
            patch("builtins.open", mock_open(read_data=b"plain text")),
            # SamostatnyNalez povoluje pouze obrazové MIME typy (PAS_ACCEPTED_MIMES).
            patch("core.models.Soubor.get_mime_types", return_value="image/png"),
            patch("cron.tasks.FedoraRepositoryConnector", return_value=connector),
        ]

    def test_import_samostatny_nalez(self):
        """Ověřuje, že INSERT import vytvoří záznam samostatny nalez."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_success(fake_redis)
        self.assertTrue(SamostatnyNalez.objects.filter(ident_cely="C-202399001-N00001").exists())

    def test_import_soubor_for_samostatny_nalez_sets_rozsah(self):
        """Ověřuje, že INSERT import vytvoří záznam soubor for samostatny nalez sets rozsah."""
        ident_cely = "C-202399001-N00010"
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload(ident_cely))
        self.assert_import_success(fake_redis)

        fake_redis, _ = self.run_import_records(
            SOUBOR_FILE_KEY,
            [{"vazba": ident_cely, "nazev": "nalez.png"}],
            extra_patches=self._soubor_phase_patches(),
        )

        self.assert_import_success(fake_redis)
        soubor = Soubor.objects.get(vazba__samostatny_nalez_souboru__ident_cely=ident_cely, nazev="nalez.png")
        self.assertIsNotNone(soubor.rozsah)
        self.assertEqual(soubor.rozsah, 1)

    def test_duplicate_insert_fails(self):
        """Ověřuje, že duplicitní INSERT import záznamu samostatny nalez skončí selháním."""
        existing = self._create_existing_nalez("C-202399001-N00002")
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload(existing.ident_cely))

        self.assert_import_failed(fake_redis)

    def test_delete_removes_samostatny_nalez(self):
        """Ověřuje, že DELETE import smaže záznam samostatny nalez."""
        nalez = self._create_existing_nalez("C-202399001-N00003")
        fake_redis, _ = self.run_import(
            FILE_KEY,
            {"ident_cely": nalez.ident_cely},
            ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(SamostatnyNalez.objects.filter(pk=nalez.pk).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu samostatny nalez označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB.")

        with patch.object(SamostatnyNalez, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu samostatny nalez označí import jako selhaný."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        self.assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení metadat Fedory pro záznam samostatny nalez označí import jako selhaný."""

        def failing_save_metadata(_record, fedora_transaction, *args, **kwargs):
            if self.fedora_metadata_transactions:
                raise RuntimeError("Simulované selhání Fedora.")

        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            save_metadata_side_effect=failing_save_metadata,
        )

        self.assert_import_failed(fake_redis)
        self.assertEqual(len(self.fedora_metadata_transactions), 1)
        self.fedora_metadata_transactions[0].rollback_transaction.assert_called_once_with()

    def test_fedora_close_failure_rolls_back_active_transaction(self):
        """Selhání uzavření Fedora transakce ji vrátí zpět a import označí jako neúspěšný."""

        def failing_close():
            raise RuntimeError("Simulované selhání uzavření Fedora transakce.")

        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            close_fedora_transaction_side_effect=failing_close,
        )

        self.assert_import_failed(fake_redis)
        self.assertEqual(len(self.fedora_metadata_transactions), 1)
        transaction_mock = self.fedora_metadata_transactions[0]
        transaction_mock.mark_transaction_as_closed.assert_called_once_with()
        transaction_mock.rollback_transaction.assert_called_once_with()

    def _three_fedora_payloads(self):
        payloads = []
        for index in range(3):
            payload = self._base_payload(f"C-202399001-N0010{index}")
            payload["evidencni_cislo"] = f"SN-FEDORA-{index}"
            payloads.append(payload)
        return payloads

    def test_fedora_failure_preserves_success_failed_and_unattempted_targets(self):
        """Selhání druhého cíle ponechá v reportu i úspěšný první a neprovedený třetí cíl."""
        closed_count = 0

        def fail_second_close():
            nonlocal closed_count
            closed_count += 1
            if closed_count == 2:
                raise RuntimeError("Simulované selhání druhé Fedora transakce.")

        fake_redis, _ = self.run_import_records(
            FILE_KEY,
            self._three_fedora_payloads(),
            close_fedora_transaction_side_effect=fail_second_close,
        )

        self.assert_import_failed(fake_redis)
        targets = json.loads(fake_redis.get(f"import_fedora_target_results_tr_{JOB_ID}"))
        self.assertCountEqual(
            [target["result"] for target in targets],
            [
                "cron.tasks.run_data_import.fedora_target_success",
                "cron.tasks.run_data_import.fedora_target_error",
                "cron.tasks.run_data_import.fedora_target_unattempted",
                "cron.tasks.run_data_import.fedora_target_unattempted",
            ],
        )
        self.assertCountEqual(
            [tuple(target["record_ids"]) for target in targets],
            [(0,), (1,), (2,), (0, 1, 2)],
        )
        attempted_targets = [
            target for target in targets if target["result"] != "cron.tasks.run_data_import.fedora_target_unattempted"
        ]
        self.assertEqual([target["transaction_uid"] for target in attempted_targets], ["test-fedora-uid"] * 2)
        dataframe = cron_tasks.build_import_fedora_target_dataframe(JOB_ID, fake_redis)
        self.assertEqual(len(dataframe.index), 4)

    def test_fedora_stop_preserves_success_and_all_unattempted_targets(self):
        """Stop po prvním cíli ponechá zbývající plánované cíle obnovitelné v reportu."""
        fake_redis, _ = self.run_import_records(
            FILE_KEY,
            self._three_fedora_payloads(),
            stop_after_fedora_close_count=1,
        )

        targets = json.loads(fake_redis.get(f"import_fedora_target_results_tr_{JOB_ID}"))
        self.assertCountEqual(
            [target["result"] for target in targets],
            [
                "cron.tasks.run_data_import.fedora_target_success",
                "cron.tasks.run_data_import.fedora_target_unattempted",
                "cron.tasks.run_data_import.fedora_target_unattempted",
                "cron.tasks.run_data_import.fedora_target_unattempted",
            ],
        )
        self.assertCountEqual(
            [tuple(target["record_ids"]) for target in targets],
            [(0,), (1,), (2,), (0, 1, 2)],
        )
        dataframe = cron_tasks.build_import_fedora_target_dataframe(JOB_ID, fake_redis)
        self.assertEqual(len(dataframe.index), 4)

    def test_fedora_plan_report_failure_prevents_first_fedora_mutation(self):
        """Selhání durabilního snapshotu úplného plánu ukončí fázi před první Fedora transakcí."""
        report_call_count = 0
        checkpoint_targets = []

        def fail_fedora_plan_checkpoint(_job_id, redis_connector, _reports_directory_path):
            nonlocal report_call_count
            report_call_count += 1
            targets_raw = redis_connector.get(f"import_fedora_target_results_tr_{JOB_ID}")
            targets = json.loads(targets_raw or "[]")
            if targets:
                checkpoint_targets.extend(targets)
                return None
            return "/tmp/fake-import-dir/reports/report.xlsx"

        fake_redis, _ = self.run_import_records(
            FILE_KEY,
            self._three_fedora_payloads(),
            extra_patches=[patch("cron.tasks.save_import_report_to_disk", side_effect=fail_fedora_plan_checkpoint)],
        )

        self.assert_import_failed(fake_redis)
        self.assertGreaterEqual(report_call_count, 3)
        self.assertTrue(checkpoint_targets)
        self.assertTrue(
            all(
                target["result"] == "cron.tasks.run_data_import.fedora_target_unattempted"
                for target in checkpoint_targets
            )
        )
        self.assertEqual(self.fedora_metadata_transactions, [])
        status_raw = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}")
        self.assertIn("failed_during_data_import", status_raw.decode("utf-8"))
        self.assertFalse(
            SamostatnyNalez.objects.filter(
                ident_cely__in=[payload["ident_cely"] for payload in self._three_fedora_payloads()]
            ).exists()
        )

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu samostatny nalez nastaví stav zastaveno."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu samostatny nalez označí import jako selhaný."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload("C-NOEXIST-N99999"),
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu samostatny nalez nastaví stav failed_lock_lost."""
        fake_redis, _ = self.run_import(
            FILE_KEY,
            self._base_payload(),
            refresh_lock_side_effect=[True, False, False, False, False, False],
        )

        status_raw = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self.assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Ověřuje, že úspěšný import záznamu samostatny nalez zapíše success marker do detailu průběhu."""
        fake_redis, _ = self.run_import(FILE_KEY, self._base_payload())

        details = fake_redis.lrange(f"import_data_progress_details_tr_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
