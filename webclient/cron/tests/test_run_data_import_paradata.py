"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``ParadataMapper``."""

from unittest.mock import patch

from core.forms import ImportDataAdminForm
from core.models import Soubor
from cron.tests._run_data_import_distribution_base import (
    FEDORA_PATH_PREFIX,
    RunDataImportDistributionTestBase,
)
from cron.tests._run_data_import_mapper_base import JOB_ID
from historie.models import Historie

PARADATA_FILE_KEY = "paradata"


class RunDataImportParadataTest(RunDataImportDistributionTestBase):
    """Testy ``run_data_import`` pro mapper ``ParadataMapper``."""

    def _run_paradata_import(
        self,
        payloads,
        performed_action=ImportDataAdminForm.PERFORMED_ACTION_INSERT,
        **kwargs,
    ):
        """Spustí import paradat se všemi patchi binární fáze.

        :param payloads: Seznam řádků importu (bez klíče ``__file_name``).
        :param performed_action: Prováděná importní akce.
        :param kwargs: Další argumenty pro ``run_import_records``; ``extra_patches``
            se připojí za patche binární fáze, ``connector_overrides`` upraví mock connectoru.
        :return: Dvojice ``(fake_redis, seznam objektů s uloženými metadaty)``.
        """
        extra = kwargs.pop("extra_patches", None) or []
        connector_overrides = kwargs.pop("connector_overrides", None)
        return self.run_import_records(
            PARADATA_FILE_KEY,
            payloads,
            performed_action,
            extra_patches=self._distribution_phase_patches(connector_overrides) + list(extra),
            **kwargs,
        )

    @staticmethod
    def _insert_payload(soubor, distribution="orig", nazev="paradata.json", mimetype="application/json"):
        """Sestaví řádek importu paradat pro akci INSERT nebo UPDATE.

        Soubor se na rozdíl od distribucí dohledává podle ``path``, nikoli podle ``id``.

        :param soubor: Dotčený ``Soubor``.
        :param distribution: Distribuce, ke které paradata patří.
        :param nazev: Název binárního souboru v importním adresáři.
        :param mimetype: MIME typ ukládaného obsahu.
        :return: Slovník odpovídající řádku ``paradata.csv``.
        """
        return {
            "path": soubor.path,
            "distribution": distribution,
            "nazev": nazev,
            "mimetype": mimetype,
        }

    @staticmethod
    def _delete_payload(soubor, distribution="orig"):
        """Sestaví řádek importu paradat pro akci DELETE.

        :param soubor: Dotčený ``Soubor``.
        :param distribution: Distribuce, ke které mazaná paradata patří.
        :return: Slovník odpovídající řádku ``paradata.csv`` s akcí DELETE.
        """
        return {"path": soubor.path, "distribution": distribution}

    def test_insert_writes_paradata_to_fedora(self):
        """INSERT zapíše paradata do Fedory pod uvedenou distribuci."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_paradata_import(
            [self._insert_payload(soubor, distribution="orig", nazev="paradata.json")],
        )

        self.assert_import_success(fake_redis)
        calls = self.connector_calls("save_paradata")
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            calls[0].args[:4],
            (soubor.repository_uuid, "orig", "paradata.json", "application/json"),
        )

    def test_update_calls_update_paradata(self):
        """UPDATE volá ``update_paradata`` a nesahá na zakládací ani mazací metodu."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_paradata_import(
            [self._insert_payload(soubor, distribution="orig", nazev="paradata-nova.json")],
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_success(fake_redis)
        calls = self.connector_calls("update_paradata")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].args[2], "paradata-nova.json")
        self.assert_no_connector_method_called("save_paradata", "delete_paradata")

    def test_delete_calls_delete_paradata(self):
        """DELETE volá ``delete_paradata`` a nečte binární obsah z importního adresáře."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_paradata_import(
            [self._delete_payload(soubor, distribution="orig")],
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        calls = self.connector_calls("delete_paradata")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].args[:2], (soubor.repository_uuid, "orig"))
        self.assert_no_connector_method_called("save_paradata", "update_paradata")

    def test_paradata_import_writes_no_history_and_no_metadata(self):
        """Paradata nezanechávají stopu v databázi — žádnou historii ani obnovu metadat.

        Na rozdíl od distribucí jsou paradata čistě fedorovská operace, takže se nesmí
        zapsat historie souboru ani přegenerovat metadata navázaného záznamu.
        """
        soubor = self._create_existing_soubor()
        historie_count = Historie.objects.filter(vazba=soubor.historie).count()
        soubor_count = Soubor.objects.count()

        fake_redis, save_metadata_calls = self._run_paradata_import([self._insert_payload(soubor)])

        self.assert_import_success(fake_redis)
        self.assertEqual(Historie.objects.filter(vazba=soubor.historie).count(), historie_count)
        self.assertEqual(Soubor.objects.count(), soubor_count)
        ident_celies = [getattr(item, "ident_cely", None) for item in save_metadata_calls]
        self.assertNotIn(
            self.dokument.ident_cely,
            ident_celies,
            "Import paradat nesmí přegenerovat metadata navázaného záznamu. Volání pro: {}".format(ident_celies),
        )

    def test_paradata_result_is_reported_for_the_record(self):
        """Zapsaná paradata se musí objevit v reportu Fedora operací u svého řádku.

        Bez vlastního hlášení by řádek zůstal označený jako čekající na import dat, který
        u paradat nikdy nepřijde.
        """
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_paradata_import(
            [self._insert_payload(soubor, distribution="orig")],
        )

        self.assert_import_success(fake_redis)
        reported = self.fedora_result(fake_redis)["0"]
        self.assertTrue(
            any("paradata_written" in item for item in reported),
            "Report musí u řádku paradat obsahovat hlášení ``paradata_written``. Report: {}".format(reported),
        )

    def test_implicit_distribution_name_is_accepted(self):
        """Paradata smí odkazovat na kontejnery vzniklé při importu souboru (``thumb``)."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_paradata_import(
            [self._insert_payload(soubor, distribution="thumb-large", nazev="thumb-paradata.json")],
        )

        self.assert_import_success(fake_redis)
        self.assertEqual(self.connector_calls("save_paradata")[0].args[1], "thumb-large")

    def test_nested_distribution_name_is_passed_through_unchanged(self):
        """Víceúrovňová distribuce se do Fedory propíše beze změny."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_paradata_import(
            [self._insert_payload(soubor, distribution="ocr/alto-xml")],
        )

        self.assert_import_success(fake_redis)
        self.assertEqual(self.connector_calls("save_paradata")[0].args[1], "ocr/alto-xml")

    def test_missing_binary_file_marks_import_as_failed(self):
        """Chybějící binární soubor v importním adresáři musí import označit jako selhalý."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_paradata_import(
            [self._insert_payload(soubor, nazev="chybi.json")],
            extra_patches=[patch("cron.tasks.os.path.isfile", return_value=False)],
        )

        self.assert_import_failed(fake_redis)
        file_results = self.file_import_results(fake_redis)
        self.assertEqual(file_results[0]["file_name"], "chybi.json")
        self.assertIn("file_not_found_in_directory", file_results[0]["additional_info_tr"])
        self.assert_no_connector_method_called("save_paradata")

    def test_fedora_write_failure_marks_import_as_failed(self):
        """Selhání ``save_paradata`` ve Fedoře musí import označit jako selhalý."""
        soubor = self._create_existing_soubor()

        def failing_connector(instance):
            instance.save_paradata.side_effect = RuntimeError("Simulované selhání zápisu paradat.")

        fake_redis, _ = self._run_paradata_import(
            [self._insert_payload(soubor)],
            connector_overrides=failing_connector,
        )

        self.assert_import_failed(fake_redis)

    def test_update_of_nonexistent_soubor_marks_import_as_failed(self):
        """UPDATE odkazující na cestu, které neodpovídá žádný Soubor, musí import označit jako selhalý."""
        fake_redis, _ = self._run_paradata_import(
            [
                {
                    "path": "{}/{}".format(FEDORA_PATH_PREFIX, "00000000-0000-0000-0000-000000000000"),
                    "distribution": "orig",
                    "nazev": "paradata.json",
                    "mimetype": "application/json",
                }
            ],
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)
        self.assert_no_connector_method_called("update_paradata")

    def test_user_stop_during_paradata_phase_marks_status_as_stopped(self):
        """Předem nastavený stop flag musí přepnout status na ``stopped_by_user``."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_paradata_import(
            [self._insert_payload(soubor)],
            pre_redis_keys={"import_data_stop_{}".format(JOB_ID): "1"},
        )

        self.assertIn("stopped_by_user", self.status_message(fake_redis))
        self.assert_no_connector_method_called("save_paradata")

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ztráta importního zámku musí zanechat status ``failed_lock_lost`` a selhalý import."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_paradata_import(
            [self._insert_payload(soubor)],
            refresh_lock_side_effect=[True] + [False] * 20,
        )

        self.assertIn("failed_lock_lost", self.status_message(fake_redis))
        self.assert_import_failed(fake_redis)

    def test_successful_import_writes_file_marker_and_report_entry(self):
        """Úspěšný import paradat zapíše značku ``file`` a záznam do reportu souborů."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_paradata_import(
            [self._insert_payload(soubor, distribution="orig", nazev="paradata-report.json")],
        )

        self.assert_import_success(fake_redis)
        self.assertIn("cron.tasks.run_data_import.file", self.progress_details(fake_redis))
        file_results = self.file_import_results(fake_redis)
        self.assertEqual(file_results[0]["file_name"], "paradata-report.json")
        self.assertEqual(file_results[0]["ident_cely"], self.dokument.ident_cely)
