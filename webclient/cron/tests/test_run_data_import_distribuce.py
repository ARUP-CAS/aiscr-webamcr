"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``DistribuceMapper``."""

import uuid
from unittest.mock import patch

from core.constants import NAHRANI_DISTRIBUCE, SMAZANI_DISTRIBUCE, UPDATE_DISTRIBUCE
from core.forms import ImportDataAdminForm
from core.models import Soubor
from cron.tests._run_data_import_distribution_base import RunDataImportDistributionTestBase
from cron.tests._run_data_import_mapper_base import JOB_ID
from historie.models import Historie

DISTRIBUTION_FILE_KEY = "distribution"


class RunDataImportDistribuceTest(RunDataImportDistributionTestBase):
    """Testy ``run_data_import`` pro mapper ``DistribuceMapper``."""

    def _run_distribution_import(
        self,
        payloads,
        performed_action=ImportDataAdminForm.PERFORMED_ACTION_INSERT,
        **kwargs,
    ):
        """Spustí import distribucí se všemi patchi binární fáze.

        :param payloads: Seznam řádků importu (bez klíče ``__file_name``).
        :param performed_action: Prováděná importní akce.
        :param kwargs: Další argumenty pro ``run_import_records``; ``extra_patches``
            se připojí za patche binární fáze, ``connector_overrides`` upraví mock connectoru.
        :return: Dvojice ``(fake_redis, seznam objektů s uloženými metadaty)``.
        """
        extra = kwargs.pop("extra_patches", None) or []
        connector_overrides = kwargs.pop("connector_overrides", None)
        return self.run_import_records(
            DISTRIBUTION_FILE_KEY,
            payloads,
            performed_action,
            extra_patches=self._distribution_phase_patches(connector_overrides) + list(extra),
            **kwargs,
        )

    @staticmethod
    def _insert_payload(soubor, distribution="ocr", nazev="ocr-vystup.txt", mimetype="text/plain"):
        """Sestaví řádek importu distribuce pro akci INSERT nebo UPDATE.

        :param soubor: Dotčený ``Soubor``.
        :param distribution: Název distribuce.
        :param nazev: Název binárního souboru v importním adresáři.
        :param mimetype: MIME typ ukládaného obsahu.
        :return: Slovník odpovídající řádku ``distribution.csv``.
        """
        return {
            "id": "soub-{}".format(soubor.id),
            "distribution": distribution,
            "nazev": nazev,
            "mimetype": mimetype,
        }

    @staticmethod
    def _delete_payload(soubor, distribution="ocr"):
        """Sestaví řádek importu distribuce pro akci DELETE.

        :param soubor: Dotčený ``Soubor``.
        :param distribution: Název mazané distribuce.
        :return: Slovník odpovídající řádku ``distribution.csv`` s akcí DELETE.
        """
        return {"id": "soub-{}".format(soubor.id), "distribution": distribution}

    def assert_history_created(self, soubor, typ_zmeny, distribution):
        """Ověří, že v historii souboru vznikl záznam o změně distribuce.

        :param soubor: Dotčený ``Soubor``.
        :param typ_zmeny: Očekávaný typ změny (``DIST01``/``DIST11``/``DIST10``).
        :param distribution: Očekávaný název distribuce v poznámce.
        """
        self.assertTrue(
            Historie.objects.filter(vazba=soubor.historie, typ_zmeny=typ_zmeny, poznamka=distribution).exists(),
            "Import distribuce musí zapsat do historie souboru záznam {} s poznámkou {!r}.".format(
                typ_zmeny, distribution
            ),
        )

    def test_insert_writes_distribution_to_fedora_and_history(self):
        """INSERT zapíše distribuci do Fedory, vytvoří historii DIST01 a nahlásí ji v reportu."""
        soubor = self._create_existing_soubor()

        fake_redis, save_metadata_calls = self._run_distribution_import(
            [self._insert_payload(soubor, distribution="ocr", nazev="ocr-vystup.txt")],
        )

        self.assert_import_success(fake_redis)
        calls = self.connector_calls("save_distribution")
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            calls[0].args[:4],
            (soubor.repository_uuid, "ocr", "ocr-vystup.txt", "text/plain"),
        )
        self.assert_history_created(soubor, NAHRANI_DISTRIBUCE, "ocr")
        self.assertIn("history_record_created", self.history_record_result(fake_redis)["0"])
        ident_celies = [getattr(item, "ident_cely", None) for item in save_metadata_calls]
        self.assertIn(
            self.dokument.ident_cely,
            ident_celies,
            "Po zápisu distribuce se musí přegenerovat metadata navázaného záznamu. Volání pro: {}".format(
                ident_celies
            ),
        )

    def test_update_calls_update_distribution_and_writes_dist11_history(self):
        """UPDATE volá ``update_distribution`` a zapisuje historii DIST11."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_distribution_import(
            [self._insert_payload(soubor, distribution="ocr", nazev="ocr-novy.txt")],
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_success(fake_redis)
        calls = self.connector_calls("update_distribution")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].args[:4], (soubor.repository_uuid, "ocr", "ocr-novy.txt", "text/plain"))
        self.assert_no_connector_method_called("save_distribution", "delete_distribution")
        self.assert_history_created(soubor, UPDATE_DISTRIBUCE, "ocr")

    def test_delete_calls_delete_distribution_and_writes_dist10_history(self):
        """DELETE volá ``delete_distribution``, nečte binární obsah a zapisuje historii DIST10."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_distribution_import(
            [self._delete_payload(soubor, distribution="ocr")],
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_success(fake_redis)
        calls = self.connector_calls("delete_distribution")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].args[:2], (soubor.repository_uuid, "ocr"))
        self.assert_no_connector_method_called("save_distribution", "update_distribution")
        self.assert_history_created(soubor, SMAZANI_DISTRIBUCE, "ocr")

    def test_import_does_not_change_the_soubor_database_row(self):
        """Import distribuce nesmí měnit databázi — mění se pouze Fedora a historie.

        Distribuce nemá vlastní model; mapper vrací existující ``Soubor`` jen jako nosič
        hodnot pro binární fázi, takže řádek nesmí být uložen, smazán ani přejmenován.
        """
        soubor = self._create_existing_soubor(nazev="beze-zmeny.txt")
        original_path = soubor.path
        soubor_count = Soubor.objects.count()

        fake_redis, _ = self._run_distribution_import(
            [self._insert_payload(soubor, distribution="ocr")],
        )

        self.assert_import_success(fake_redis)
        self.assertEqual(Soubor.objects.count(), soubor_count)
        soubor.refresh_from_db()
        self.assertEqual(soubor.nazev, "beze-zmeny.txt")
        self.assertEqual(soubor.path, original_path)

    def test_nested_distribution_name_is_passed_through_unchanged(self):
        """Víceúrovňový název distribuce se do Fedory i historie propíše beze změny."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_distribution_import(
            [self._insert_payload(soubor, distribution="ocr/alto-xml", nazev="alto.xml", mimetype="text/xml")],
        )

        self.assert_import_success(fake_redis)
        calls = self.connector_calls("save_distribution")
        self.assertEqual(calls[0].args[1], "ocr/alto-xml")
        self.assert_history_created(soubor, NAHRANI_DISTRIBUCE, "ocr/alto-xml")

    def test_multiple_distributions_of_one_record_refresh_metadata_once(self):
        """Několik distribucí téhož navázaného záznamu spustí přegenerování metadat jen jednou.

        Metadata se obnovují až po zápisu všech distribucí, aby se stejný záznam nezapisoval
        do Fedory opakovaně.
        """
        soubor = self._create_existing_soubor()

        fake_redis, save_metadata_calls = self._run_distribution_import(
            [
                self._insert_payload(soubor, distribution="ocr", nazev="ocr.txt"),
                self._insert_payload(soubor, distribution="preview", nazev="preview.txt"),
            ],
        )

        self.assert_import_success(fake_redis)
        self.assertEqual(len(self.connector_calls("save_distribution")), 2)
        matching = [
            item for item in save_metadata_calls if getattr(item, "ident_cely", None) == self.dokument.ident_cely
        ]
        self.assertEqual(
            len(matching),
            1,
            "Metadata navázaného záznamu se smí uložit právě jednou pro celou dávku distribucí.",
        )

    def test_missing_binary_file_marks_import_as_failed(self):
        """Chybějící binární soubor v importním adresáři musí import označit jako selhalý."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_distribution_import(
            [self._insert_payload(soubor, nazev="chybi.txt")],
            extra_patches=[patch("cron.tasks.os.path.isfile", return_value=False)],
        )

        self.assert_import_failed(fake_redis)
        file_results = self.file_import_results(fake_redis)
        self.assertEqual(file_results[0]["file_name"], "chybi.txt")
        self.assertIn("file_not_found_in_directory", file_results[0]["additional_info_tr"])
        self.assert_no_connector_method_called("save_distribution")

    def test_fedora_write_failure_marks_import_as_failed(self):
        """Selhání ``save_distribution`` ve Fedoře musí import označit jako selhalý."""
        soubor = self._create_existing_soubor()

        def failing_connector(instance):
            instance.save_distribution.side_effect = RuntimeError("Simulované selhání zápisu distribuce.")

        fake_redis, _ = self._run_distribution_import(
            [self._insert_payload(soubor)],
            connector_overrides=failing_connector,
        )

        self.assert_import_failed(fake_redis)
        self.assertFalse(
            Historie.objects.filter(vazba=soubor.historie, typ_zmeny=NAHRANI_DISTRIBUCE).exists(),
            "Po selhání zápisu do Fedory nesmí v historii zůstat záznam o nahrání distribuce.",
        )

    def test_history_save_failure_marks_import_as_failed(self):
        """Selhání zápisu historie distribuce musí import označit jako selhalý."""
        soubor = self._create_existing_soubor()

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB při ukládání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self._run_distribution_import([self._insert_payload(soubor)])

        self.assert_import_failed(fake_redis)

    def test_update_of_nonexistent_soubor_marks_import_as_failed(self):
        """UPDATE odkazující na neexistující Soubor musí import označit jako selhalý."""
        fake_redis, _ = self._run_distribution_import(
            [
                {
                    "id": "soub-{}".format(uuid.uuid4()),
                    "distribution": "ocr",
                    "nazev": "ocr.txt",
                    "mimetype": "text/plain",
                }
            ],
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)
        self.assert_no_connector_method_called("update_distribution")

    def test_user_stop_during_distribution_phase_marks_status_as_stopped(self):
        """Předem nastavený stop flag musí přepnout status na ``stopped_by_user``."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_distribution_import(
            [self._insert_payload(soubor)],
            pre_redis_keys={"import_data_stop_{}".format(JOB_ID): "1"},
        )

        self.assertIn("stopped_by_user", self.status_message(fake_redis))
        self.assert_no_connector_method_called("save_distribution")

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ztráta importního zámku musí zanechat status ``failed_lock_lost`` a selhalý import."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_distribution_import(
            [self._insert_payload(soubor)],
            refresh_lock_side_effect=[True] + [False] * 20,
        )

        self.assertIn("failed_lock_lost", self.status_message(fake_redis))
        self.assert_import_failed(fake_redis)

    def test_successful_import_writes_file_marker_and_report_entry(self):
        """Úspěšný import distribuce zapíše značku ``file`` a záznam do reportu souborů."""
        soubor = self._create_existing_soubor()

        fake_redis, _ = self._run_distribution_import(
            [self._insert_payload(soubor, distribution="ocr", nazev="ocr-report.txt")],
        )

        self.assert_import_success(fake_redis)
        self.assertIn("cron.tasks.run_data_import.file", self.progress_details(fake_redis))
        file_results = self.file_import_results(fake_redis)
        self.assertEqual(file_results[0]["file_name"], "ocr-report.txt")
        self.assertEqual(file_results[0]["ident_cely"], self.dokument.ident_cely)
        self.assertIn("ocr", file_results[0]["additional_info_tr"])
