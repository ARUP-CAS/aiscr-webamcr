"""Jednotkové testy pro ``cron.tasks.run_data_import_validation``."""

import io
import json
import zipfile
from unittest.mock import patch

from core.constants import ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.import_data_mappers import SouborImportIntegrityError
from core.models import AntivirusCheckResult
from core.tests.fake_redis import FakeRedis
from cron import tasks as cron_tasks
from django.contrib.auth.models import Group
from django.db import connection
from django.test import TestCase, override_settings
from heslar.hesla import HESLAR_LICENCE, HESLAR_ORGANIZACE_TYP, HESLAR_PRISTUPNOST
from heslar.models import Heslar, HeslarNazev
from uzivatel.models import Organizace, User

JOB_ID = "test-job-validation"
LOCK_TOKEN = "test-lock-token-validation"
USER_IDENT = "U-VAL-001"
USER_EMAIL = "validation-user@example.cz"
USER_ORGANIZACE_IDENT = "ORG-VAL-001"

UZIVATEL_COLUMNS = [
    "ident_cely",
    "first_name",
    "last_name",
    "email",
    "telefon",
    "orcid",
    "jazyk",
    "is_active",
    "is_staff",
    "is_superuser",
    "date_joined",
    "last_login",
    "osoba",
    "organizace",
]


def _uzivatel_row(ident_cely=USER_IDENT, email=USER_EMAIL, organizace=USER_ORGANIZACE_IDENT):
    """Vrátí slovník jednoho platného řádku ``uzivatele.csv`` pro INSERT."""
    return {
        "ident_cely": ident_cely,
        "first_name": "Jan",
        "last_name": "Importovaný",
        "email": email,
        "telefon": "",
        "orcid": "",
        "jazyk": "cs",
        "is_active": "True",
        "is_staff": "False",
        "is_superuser": "False",
        "date_joined": "2024-01-01 00:00:00",
        "last_login": "",
        "osoba": "",
        "organizace": organizace,
    }


def _build_zip(rows: list[dict], file_name: str = "uzivatele.csv") -> bytes:
    """Postaví ZIP archiv s jedním CSV souborem s danými řádky a vrátí jeho bytes."""
    buf = io.BytesIO()
    import csv as csv_module

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        with zf.open(file_name, "w") as f, io.TextIOWrapper(f, encoding="utf-8", newline="") as text_f:
            writer = csv_module.DictWriter(text_f, fieldnames=UZIVATEL_COLUMNS)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
    return buf.getvalue()


def _stage_zip(fake_redis: FakeRedis, blob: bytes, chunk_size: int = 64 * 1024 * 1024) -> int:
    """Nastageuje ZIP blob do FakeRedis po chunkách (zrcadlí POST chování) a vrátí počet chunků."""
    chunk_count = (len(blob) + chunk_size - 1) // chunk_size or 1
    for i in range(chunk_count):
        fake_redis.set(
            f"import_data_file_{JOB_ID}_{i}",
            blob[i * chunk_size : (i + 1) * chunk_size],
        )
    fake_redis.set(f"import_data_file_chunks_{JOB_ID}", chunk_count)
    return chunk_count


class RunDataImportValidationTest(TestCase):
    """Testy ``run_data_import_validation`` s mocknutým Redis, antivirem a Fedora repozitářem."""

    @classmethod
    def setUpTestData(cls):
        """Připraví minimální fixtures — organizaci a uživatele běžícího import."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            typ_org_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_ORGANIZACE_TYP, defaults={"nazev": "typ_organizace"}
            )
            typ_org, _ = Heslar.objects.get_or_create(
                nazev_heslare=typ_org_nazev,
                zkratka="T",
                defaults={"ident_cely": "HES-VAL-TYPORG-001", "heslo": "Test", "heslo_en": "Test"},
            )
            pristupnost_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_PRISTUPNOST, defaults={"nazev": "pristupnost"}
            )
            pristupnost, _ = Heslar.objects.get_or_create(
                nazev_heslare=pristupnost_nazev,
                zkratka="A",
                defaults={"ident_cely": "HES-VAL-PRST-001", "heslo": "Veřejný", "heslo_en": "Public"},
            )
            licence_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_LICENCE, defaults={"nazev": "licence"})
            licence, _ = Heslar.objects.get_or_create(
                nazev_heslare=licence_nazev,
                zkratka="L",
                defaults={"ident_cely": "HES-VAL-LIC-001", "heslo": "Lic", "heslo_en": "Lic"},
            )
            cls.organizace, _ = Organizace.objects.get_or_create(
                ident_cely=USER_ORGANIZACE_IDENT,
                defaults={
                    "nazev": "Org pro validaci",
                    "nazev_zkraceny": "ORGVAL",
                    "typ_organizace": typ_org,
                    "zverejneni_pristupnost": pristupnost,
                    "licence": licence,
                },
            )
            cls.runner = User.objects.create_user(  # type: ignore[attr-defined]
                email="validation-runner@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-VAL-RUNNER-001",
                first_name="Validation",
                last_name="Runner",
            )

    def _build_redis(
        self, blob: bytes | None = None, performed_action: str = ImportDataAdminForm.PERFORMED_ACTION_INSERT
    ) -> FakeRedis:
        """Sestaví FakeRedis s nastageovaným ZIPem a per-job klíči tak, jak je nastavuje POST."""
        fake_redis = FakeRedis()
        fake_redis.set(f"import_performed_action_{JOB_ID}", performed_action)
        fake_redis.set(f"import_data_user_{JOB_ID}", str(self.runner.id))
        fake_redis.set(f"import_data_lock_token_{JOB_ID}", LOCK_TOKEN)
        fake_redis.set(f"import_data_phase_{JOB_ID}", cron_tasks.IMPORT_PHASE_VALIDATING)
        fake_redis.set(f"import_data_current_job_{self.runner.id}", JOB_ID)
        fake_redis.set(cron_tasks.RedisConnector.IMPORT_DATA_LOCK_KEY, LOCK_TOKEN)
        fake_redis.set(cron_tasks.RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY, JOB_ID)
        fake_redis.set(f"import_data_validation_total_{JOB_ID}", 0)
        fake_redis.set(f"import_data_validation_progress_{JOB_ID}", 0)
        fake_redis.set(f"import_data_validation_results_{JOB_ID}", json.dumps([]))
        fake_redis.set(f"import_data_valid_{JOB_ID}", "0")
        if blob is not None:
            _stage_zip(fake_redis, blob)
        return fake_redis

    def _run_validation(
        self,
        fake_redis: FakeRedis,
        antivirus_result: AntivirusCheckResult = AntivirusCheckResult.PASSES,
        refresh_lock_side_effect=None,
        finalize_validation_side_effect=None,
    ):
        """Spustí ``run_data_import_validation`` s mocknutým Redis, antivirem a Fedora."""
        refresh_lock_kwargs = (
            {"side_effect": refresh_lock_side_effect}
            if refresh_lock_side_effect is not None
            else {"return_value": True}
        )
        real_finalize_validation = cron_tasks.RedisConnector.finalize_validation
        finalize_validation_kwargs = (
            {"side_effect": finalize_validation_side_effect}
            if finalize_validation_side_effect is not None
            else {"side_effect": real_finalize_validation}
        )
        with patch("core.connectors.RedisConnector.get_connection", return_value=fake_redis), patch(
            "core.connectors.RedisConnector.refresh_import_lock", **refresh_lock_kwargs
        ), patch("core.connectors.RedisConnector.finalize_validation", **finalize_validation_kwargs), patch(
            "core.connectors.RedisConnector.release_import_lock", return_value=True
        ) as release_lock_mock, patch(
            "core.models.Soubor.check_antivirus", return_value=antivirus_result
        ), patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch(
            "xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None
        ), patch(
            "uzivatel.models.User.save_metadata", lambda *a, **kw: None
        ), patch(
            "uzivatel.signals.FedoraTransaction"
        ) as signals_fedora_transaction_mock, patch(
            "cron.tasks.check_import_report_directory",
            return_value=("/tmp/fake-import-dir", "/tmp/fake-import-dir/reports", None),
        ), patch(
            "cron.tasks.save_import_report_to_disk", return_value="/tmp/fake-import-dir/reports/report.xlsx"
        ) as report_save_mock:
            self.validation_report_save_mock = report_save_mock
            signals_fedora_transaction_mock.return_value = None
            cron_tasks.run_data_import_validation(
                JOB_ID, self.runner.id, LOCK_TOKEN, ImportDataAdminForm.PERFORMED_ACTION_INSERT
            )
        return release_lock_mock

    def _assert_phase(self, fake_redis: FakeRedis, expected_phase: str):
        """Ověří, že ``import_data_phase_{job_id}`` je nastavena na očekávanou fázi."""
        phase_raw = fake_redis.get(f"import_data_phase_{JOB_ID}")
        self.assertIsNotNone(phase_raw)
        self.assertEqual(phase_raw.decode("utf-8"), expected_phase)

    def _assert_chunks_deleted(self, fake_redis: FakeRedis, chunk_count: int):
        """Ověří, že všechny chunk klíče i count klíč jsou smazány v ``finally``."""
        self.assertIsNone(fake_redis.get(f"import_data_file_chunks_{JOB_ID}"))
        for i in range(chunk_count):
            self.assertIsNone(fake_redis.get(f"import_data_file_{JOB_ID}_{i}"))

    def test_lock_lost_at_start_sets_failed_lock_lost_and_releases_lock(self):
        """Ztráta locku před začátkem nastaví fázi ``failed`` a ``failed_lock_lost`` status; lock se uvolní."""
        fake_redis = self._build_redis(blob=_build_zip([_uzivatel_row()]))

        release_lock_mock = self._run_validation(fake_redis, refresh_lock_side_effect=[False])

        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_FAILED)
        status_raw = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        failure_reason_raw = fake_redis.get(f"import_data_failure_reason_{JOB_ID}")
        self.assertIsNotNone(failure_reason_raw)
        self.assertEqual(failure_reason_raw.decode("utf-8"), cron_tasks.IMPORT_FAILURE_REASON_ERROR)
        self.assertTrue(release_lock_mock.called)

    def test_virus_found_sets_failed_error_and_releases_lock(self):
        """Nalezení viru nastaví fázi ``failed`` s ``error`` reason a crash status zprávu; lock se uvolní."""
        fake_redis = self._build_redis(blob=_build_zip([_uzivatel_row()]))

        release_lock_mock = self._run_validation(fake_redis, antivirus_result=AntivirusCheckResult.VIRUS_FOUND)

        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_FAILED)
        failure_reason_raw = fake_redis.get(f"import_data_failure_reason_{JOB_ID}")
        self.assertIsNotNone(failure_reason_raw)
        self.assertEqual(failure_reason_raw.decode("utf-8"), cron_tasks.IMPORT_FAILURE_REASON_ERROR)
        status_raw = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertNotIn("failed_lock_lost", status_raw.decode("utf-8"))
        self.assertTrue(release_lock_mock.called)

    def test_bad_zip_sets_failed_error_and_releases_lock(self):
        """Neplatný ZIP nastaví fázi ``failed`` s ``error`` reason; chunky se smažou v ``finally``."""
        fake_redis = self._build_redis(blob=b"this is not a zip file")
        chunk_count = int(fake_redis.get(f"import_data_file_chunks_{JOB_ID}").decode("utf-8"))

        release_lock_mock = self._run_validation(fake_redis)

        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_FAILED)
        failure_reason_raw = fake_redis.get(f"import_data_failure_reason_{JOB_ID}")
        self.assertIsNotNone(failure_reason_raw)
        self.assertEqual(failure_reason_raw.decode("utf-8"), cron_tasks.IMPORT_FAILURE_REASON_ERROR)
        self.assertTrue(release_lock_mock.called)
        self._assert_chunks_deleted(fake_redis, chunk_count)

    def test_unsupported_files_sets_failed_error(self):
        """ZIP se souborem, pro který neexistuje mapper, nastaví fázi ``failed`` s ``error`` reason."""
        blob = _build_zip([_uzivatel_row()], file_name="nehospodar.csv")
        fake_redis = self._build_redis(blob=blob)

        self._run_validation(fake_redis)

        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_FAILED)
        failure_reason_raw = fake_redis.get(f"import_data_failure_reason_{JOB_ID}")
        self.assertIsNotNone(failure_reason_raw)
        self.assertEqual(failure_reason_raw.decode("utf-8"), cron_tasks.IMPORT_FAILURE_REASON_ERROR)

    def test_empty_zip_sets_failed_error(self):
        """ZIP bez CSV souborů nastaví fázi ``failed`` s ``error`` reason."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED):
            pass
        fake_redis = self._build_redis(blob=buf.getvalue())

        self._run_validation(fake_redis)

        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_FAILED)
        failure_reason_raw = fake_redis.get(f"import_data_failure_reason_{JOB_ID}")
        self.assertIsNotNone(failure_reason_raw)
        self.assertEqual(failure_reason_raw.decode("utf-8"), cron_tasks.IMPORT_FAILURE_REASON_ERROR)

    def test_empty_csv_sets_failed_error(self):
        """ZIP s prázdným CSV (pouze hlavička, žádné řádky) nastaví fázi ``failed`` s ``error`` reason."""
        blob = _build_zip(rows=[])
        fake_redis = self._build_redis(blob=blob)

        self._run_validation(fake_redis)

        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_FAILED)
        failure_reason_raw = fake_redis.get(f"import_data_failure_reason_{JOB_ID}")
        self.assertIsNotNone(failure_reason_raw)
        self.assertEqual(failure_reason_raw.decode("utf-8"), cron_tasks.IMPORT_FAILURE_REASON_ERROR)

    @override_settings()
    def test_oversized_zip_sets_failed_error(self):
        """ZIP překračující ``IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE`` nastaví fázi ``failed`` s ``error`` reason."""
        blob = _build_zip([_uzivatel_row()])
        fake_redis = self._build_redis(blob=blob)

        with patch("core.admin_sites.AmcrCustomAdminSite.IMPORT_ZIP_MAX_UNCOMPRESSED_SIZE", 0):
            self._run_validation(fake_redis)

        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_FAILED)
        failure_reason_raw = fake_redis.get(f"import_data_failure_reason_{JOB_ID}")
        self.assertIsNotNone(failure_reason_raw)
        self.assertEqual(failure_reason_raw.decode("utf-8"), cron_tasks.IMPORT_FAILURE_REASON_ERROR)

    def test_all_valid_sets_awaiting_approval_and_holds_lock(self):
        """Úspěšná validace všech řádků nastaví ``awaiting_approval``, ``valid=1`` a lock se NEuvolní."""
        blob = _build_zip([_uzivatel_row()])
        fake_redis = self._build_redis(blob=blob)

        release_lock_mock = self._run_validation(fake_redis)

        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_AWAITING_APPROVAL)
        valid_raw = fake_redis.get(f"import_data_valid_{JOB_ID}")
        self.assertIsNotNone(valid_raw)
        self.assertEqual(valid_raw.decode("utf-8"), "1")
        self.assertFalse(release_lock_mock.called, "Na úspěšné cestě se lock nesmí uvolnit.")
        count_raw = fake_redis.get(f"import_data_count_{JOB_ID}")
        self.assertIsNotNone(count_raw)
        self.assertEqual(int(count_raw.decode("utf-8")), 1)
        details = fake_redis.lrange(f"import_data_validation_details_{JOB_ID}", 0, -1)
        self.assertEqual(len(details), 1)
        result = json.loads(details[0].decode("utf-8"))
        self.assertEqual(result["validation_result"], "core.admin.import_data.record_valid")
        progress_raw = fake_redis.get(f"import_data_validation_progress_{JOB_ID}")
        self.assertIsNotNone(progress_raw)
        self.assertEqual(int(progress_raw.decode("utf-8")), 1)

    def test_reset_during_finalization_cannot_publish_awaiting_approval(self):
        """Reset těsně před finalizací zabrání přechodu validace do ``awaiting_approval``."""
        fake_redis = self._build_redis(blob=_build_zip([_uzivatel_row()]))
        real_finalize_validation = cron_tasks.RedisConnector.finalize_validation

        def reset_then_finalize(connection, job_id):
            connection.set(f"import_data_stop_{job_id}", "1")
            connection.set(f"import_data_phase_{job_id}", cron_tasks.IMPORT_PHASE_FAILED)
            connection.delete(cron_tasks.RedisConnector.IMPORT_DATA_LOCK_KEY)
            return real_finalize_validation(connection, job_id)

        release_lock_mock = self._run_validation(
            fake_redis,
            finalize_validation_side_effect=reset_then_finalize,
        )

        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_FAILED)
        status = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}").decode("utf-8")
        self.assertIn("failed_lock_lost", status)
        self.assertTrue(release_lock_mock.called)

    def test_lock_replaced_during_finalization_cannot_publish_awaiting_approval(self):
        """Cizí lock získaný před finalizací zůstane zachován a validace skončí jako ``failed``."""
        fake_redis = self._build_redis(blob=_build_zip([_uzivatel_row()]))
        real_finalize_validation = cron_tasks.RedisConnector.finalize_validation
        replacement_token = "replacement-lock-token"
        replacement_job_id = "replacement-job"

        def replace_lock_then_finalize(connection, job_id):
            connection.set(cron_tasks.RedisConnector.IMPORT_DATA_LOCK_KEY, replacement_token)
            connection.set(cron_tasks.RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY, replacement_job_id)
            connection.set(f"import_data_current_job_{self.runner.id}", replacement_job_id)
            return real_finalize_validation(connection, job_id)

        self._run_validation(
            fake_redis,
            finalize_validation_side_effect=replace_lock_then_finalize,
        )

        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_FAILED)
        self.assertEqual(
            fake_redis.get(cron_tasks.RedisConnector.IMPORT_DATA_LOCK_KEY).decode("utf-8"), replacement_token
        )
        self.assertEqual(
            fake_redis.get(cron_tasks.RedisConnector.IMPORT_DATA_ACTIVE_JOB_KEY).decode("utf-8"), replacement_job_id
        )
        self.assertEqual(
            fake_redis.get(f"import_data_current_job_{self.runner.id}").decode("utf-8"), replacement_job_id
        )

    def test_some_invalid_sets_failed_validation_rejected_and_releases_lock(self):
        """Řádek s neexistující organizací nastaví ``failed`` s ``validation_rejected`` reason a uvolní lock."""
        # Neexistující organizace → LookupImportField vyvolá ImportDataMissingReferencedValueError.
        rows = [
            _uzivatel_row(ident_cely="U-VAL-OK", email="ok@example.cz"),
            _uzivatel_row(ident_cely="U-VAL-BAD", email="bad@example.cz", organizace="ORG-DOES-NOT-EXIST"),
        ]
        blob = _build_zip(rows)
        fake_redis = self._build_redis(blob=blob)

        release_lock_mock = self._run_validation(fake_redis)

        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_FAILED)
        failure_reason_raw = fake_redis.get(f"import_data_failure_reason_{JOB_ID}")
        self.assertIsNotNone(failure_reason_raw)
        self.assertEqual(
            failure_reason_raw.decode("utf-8"),
            cron_tasks.IMPORT_FAILURE_REASON_VALIDATION_REJECTED,
        )
        valid_raw = fake_redis.get(f"import_data_valid_{JOB_ID}")
        self.assertIsNotNone(valid_raw)
        self.assertEqual(valid_raw.decode("utf-8"), "0")
        status_raw = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        status_decoded = status_raw.decode("utf-8")
        self.assertIn("validation_rejected", status_decoded)
        self.assertNotIn("failed_lock_lost", status_decoded)
        self.assertTrue(release_lock_mock.called, "Při validation_rejected se lock musí uvolnit.")
        details = fake_redis.lrange(f"import_data_validation_details_{JOB_ID}", 0, -1)
        self.assertEqual(len(details), 2)
        persisted_results = json.loads(fake_redis.get(f"import_data_validation_results_{JOB_ID}"))
        self.assertEqual(len(persisted_results), 2)
        self.assertEqual([result["item_order"] for result in persisted_results], [0, 1])
        self.assertGreaterEqual(self.validation_report_save_mock.call_count, 2)

    def test_duplicate_soubory_across_zip_paths_is_rejected(self):
        """Duplicitní soubor v různých cestách ZIPu sdílí stav dávky a validace jej odmítne."""

        class SouborMapperStub:
            """Napodobuje mapper souborů a odmítá opakovaný logický klíč v jedné dávce."""

            allow_update = True

            def __init__(self, row):
                self.row = row

            @staticmethod
            def validate_batch_ordering(rows):
                return None

            def map(self, performed_action, **kwargs):
                return {"logical_key": self.row["logical_key"]}

            def check_required_fields(self, performed_action):
                return None

            def import_validation(self, performed_action, user_id, seen_in_batch=None):
                key = self.row["logical_key"]
                if key in seen_in_batch:
                    raise SouborImportIntegrityError("X-TEST", key)
                seen_in_batch.add(key)
                return {"logical_key": key}

            def create_records(self, performed_action):
                return []

        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("a/soubory.csv", "logical_key\nduplicate.txt\n")
            zf.writestr("b/soubory.csv", "logical_key\nduplicate.txt\n")
        fake_redis = self._build_redis(blob=archive.getvalue())

        with patch.object(
            cron_tasks.ImportModelMapper,
            "get_import_data_mapper_dict",
            return_value={"soubory": SouborMapperStub},
        ), patch.object(
            cron_tasks.ImportModelMapper,
            "get_import_data_mapper",
            return_value=SouborMapperStub,
        ):
            self._run_validation(fake_redis)

        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_FAILED)
        self.assertEqual(fake_redis.get(f"import_data_valid_{JOB_ID}").decode("utf-8"), "0")
        results = json.loads(fake_redis.get(f"import_data_validation_results_{JOB_ID}"))
        self.assertEqual(len(results), 2)
        self.assertEqual([item["file_name"] for item in results], ["soubory.csv", "soubory.csv"])
        self.assertEqual(results[0]["validation_result"], "core.admin.import_data.record_valid")
        self.assertIn("duplicate.txt", results[1]["validation_result"])

    def test_failed_validation_rejected_and_error_never_share_status_string(self):
        """``validation_rejected`` a ``error`` reason nesmí sdílet stejnou status zprávu."""
        # validation_rejected cesta
        rows = [_uzivatel_row(ident_cely="U-VAL-BAD", email="bad@example.cz", organizace="ORG-DOES-NOT-EXIST")]
        fake_redis_rejected = self._build_redis(blob=_build_zip(rows))
        self._run_validation(fake_redis_rejected)
        rejected_status = fake_redis_rejected.get(f"import_data_status_message_tr_{JOB_ID}").decode("utf-8")

        # error cesta (bad zip)
        fake_redis_error = self._build_redis(blob=b"not a zip")
        self._run_validation(fake_redis_error)
        error_status = fake_redis_error.get(f"import_data_status_message_tr_{JOB_ID}").decode("utf-8")

        self.assertNotEqual(rejected_status, error_status)
        self.assertIn("validation_rejected", rejected_status)

    def test_stop_sentinel_mid_validation_sets_stopped_and_releases_lock(self):
        """Předem nastavený stop sentinel způsobí zastavení po prvním řádku a fázi ``stopped``; lock se uvolní."""
        rows = [
            _uzivatel_row(ident_cely="U-VAL-STOP-1", email="stop-1@example.cz"),
            _uzivatel_row(ident_cely="U-VAL-STOP-2", email="stop-2@example.cz"),
        ]
        blob = _build_zip(rows)
        fake_redis = self._build_redis(blob=blob)
        fake_redis.set(f"import_data_stop_{JOB_ID}", "1")

        release_lock_mock = self._run_validation(fake_redis)

        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_STOPPED)
        status_raw = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))
        self.assertTrue(release_lock_mock.called)

    def test_stop_after_non_checkpoint_rows_flushes_complete_results_before_report(self):
        """Stop po dvou řádcích zapíše oba výsledky do Redis ještě před terminálním reportem."""
        rows = [
            _uzivatel_row(ident_cely="U-VAL-STOP-1", email="stop-1@example.cz"),
            _uzivatel_row(ident_cely="U-VAL-STOP-2", email="stop-2@example.cz"),
            _uzivatel_row(ident_cely="U-VAL-STOP-3", email="stop-3@example.cz"),
        ]
        fake_redis = self._build_redis(blob=_build_zip(rows))
        refresh_count = 0

        def stop_before_third_row(*args, **kwargs):
            nonlocal refresh_count
            refresh_count += 1
            # One initial refresh precedes validation; subsequent calls precede individual rows.
            if refresh_count == 4:
                fake_redis.set(f"import_data_stop_{JOB_ID}", "1")
            return True

        self._run_validation(fake_redis, refresh_lock_side_effect=stop_before_third_row)

        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_STOPPED)
        persisted_results = json.loads(fake_redis.get(f"import_data_validation_results_{JOB_ID}"))
        self.assertEqual(len(persisted_results), 2)
        self.assertEqual([result["item_order"] for result in persisted_results], [0, 1])
        self.assertGreaterEqual(self.validation_report_save_mock.call_count, 2)

    def test_chunked_zip_is_reassembled_byte_for_byte(self):
        """ZIP rozdělený na více chunků se reassemblovat byte-for-byte a správně zvaliduje."""
        blob = _build_zip([_uzivatel_row()])
        # Vynutíme více chunků tím, že nastageujeme s malým chunk_size.
        small_chunk = 64
        fake_redis = self._build_redis(blob=blob)
        # Přepíšeme staging malými chunky.
        for i in range((len(blob) + small_chunk - 1) // small_chunk):
            fake_redis.set(
                f"import_data_file_{JOB_ID}_{i}",
                blob[i * small_chunk : (i + 1) * small_chunk],
            )
        chunk_count = (len(blob) + small_chunk - 1) // small_chunk
        fake_redis.set(f"import_data_file_chunks_{JOB_ID}", chunk_count)
        self.assertGreater(chunk_count, 1)

        self._run_validation(fake_redis)

        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_AWAITING_APPROVAL)
        valid_raw = fake_redis.get(f"import_data_valid_{JOB_ID}")
        self.assertIsNotNone(valid_raw)
        self.assertEqual(valid_raw.decode("utf-8"), "1")
        self._assert_chunks_deleted(fake_redis, chunk_count)

    def test_failure_path_expires_data_keys_not_deletes_them(self):
        """Na ``failed`` cestě se datové klíče expirují (ne mažou) — report zůstává stažitelný."""
        blob = _build_zip([_uzivatel_row()])
        fake_redis = self._build_redis(blob=blob)

        self._run_validation(fake_redis, antivirus_result=AntivirusCheckResult.VIRUS_FOUND)

        # Datové klíče musí stále existovat (expire v FakeRedis je no-op, klíč zůstává).
        self.assertIsNotNone(fake_redis.get(f"import_data_validation_results_{JOB_ID}"))
        self.assertIsNotNone(fake_redis.get(f"import_data_status_message_tr_{JOB_ID}"))
        # Chunk klíče se naopak mažou (ne expirují).
        chunks_raw = fake_redis.get(f"import_data_file_chunks_{JOB_ID}")
        self.assertIsNone(chunks_raw)

    def test_success_path_persists_per_job_data_keys(self):
        """Na úspěšné cestě se per-job datové klíče persistují (bez TTL) pro awaiting_approval okno."""
        blob = _build_zip([_uzivatel_row()])
        fake_redis = self._build_redis(blob=blob)

        self._run_validation(fake_redis)

        # Persist v FakeRedis je no-op; ověříme, že klíče zůstávají a fáze je awaiting_approval.
        self._assert_phase(fake_redis, cron_tasks.IMPORT_PHASE_AWAITING_APPROVAL)
        self.assertIsNotNone(fake_redis.get(f"import_data_validation_results_{JOB_ID}"))
        self.assertIsNotNone(fake_redis.get(f"import_data_count_{JOB_ID}"))
        self.assertIsNotNone(fake_redis.get(f"import_data_valid_{JOB_ID}"))
        # Per-user pointer se na úspěšné cestě persistuje (nesmí se smazat).
        self.assertIsNotNone(fake_redis.get(f"import_data_current_job_{self.runner.id}"))

    def test_read_only_contract_no_db_writes_during_validation(self):
        """Během validace se do DB nezapíše — žádný INSERT/UPDATE/DELETE (read-only kontrakt)."""
        from django.test.utils import CaptureQueriesContext

        blob = _build_zip([_uzivatel_row()])
        fake_redis = self._build_redis(blob=blob)

        with CaptureQueriesContext(connection) as ctx:
            self._run_validation(fake_redis)

        write_prefixes = ("insert", "update", "delete")
        writes = [
            q["sql"].lower()
            for q in ctx.captured_queries
            if q["sql"].lower().split()[0:1] and q["sql"].lower().split()[0] in write_prefixes
        ]
        self.assertEqual(writes, [], "Během validace se nesmí provést žádný DB zápis.")
        self.assertFalse(User.objects.filter(ident_cely=USER_IDENT).exists())

    def test_read_only_contract_fedora_save_metadata_not_called(self):
        """Během validace se nezavolá ``save_metadata`` ani jiné Fedora external-write entry pointy."""
        blob = _build_zip([_uzivatel_row()])
        fake_redis = self._build_redis(blob=blob)

        with patch("core.connectors.RedisConnector.get_connection", return_value=fake_redis), patch(
            "core.connectors.RedisConnector.refresh_import_lock", return_value=True
        ), patch("core.connectors.RedisConnector.persist_import_lock", return_value=True), patch(
            "core.connectors.RedisConnector.release_import_lock", return_value=True
        ), patch(
            "core.models.Soubor.check_antivirus", return_value=AntivirusCheckResult.PASSES
        ), patch(
            "xml_generator.models.ModelWithMetadata.save_metadata"
        ) as save_metadata_mock, patch(
            "uzivatel.models.User.save_metadata"
        ) as user_save_metadata_mock, patch(
            "core.repository_connector.FedoraRepositoryConnector.save_binary_file"
        ) as save_binary_file_mock, patch(
            "cron.tasks.check_import_report_directory",
            return_value=("/tmp/fake-import-dir", "/tmp/fake-import-dir/reports", None),
        ), patch(
            "cron.tasks.save_import_report_to_disk", return_value="/tmp/fake-import-dir/reports/report.xlsx"
        ):
            cron_tasks.run_data_import_validation(
                JOB_ID, self.runner.id, LOCK_TOKEN, ImportDataAdminForm.PERFORMED_ACTION_INSERT
            )

        save_metadata_mock.assert_not_called()
        user_save_metadata_mock.assert_not_called()
        save_binary_file_mock.assert_not_called()
