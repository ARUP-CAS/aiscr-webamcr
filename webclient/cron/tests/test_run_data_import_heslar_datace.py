"""Jednotkové testy pro ``cron.tasks.run_data_import`` — import jednoho záznamu HeslarDatace."""

import json
from unittest.mock import MagicMock, patch

from core.constants import ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.tests.fake_redis import FakeRedis
from cron import tasks as cron_tasks
from django.contrib.auth.models import Group
from django.test import TestCase
from heslar.hesla import HESLAR_LICENCE, HESLAR_OBDOBI, HESLAR_ORGANIZACE_TYP, HESLAR_PRISTUPNOST
from heslar.models import Heslar, HeslarDatace, HeslarNazev
from uzivatel.models import Organizace, User

FILE_KEY = "heslar_datace"
JOB_ID = "test-job-heslar-datace"
LOCK_TOKEN = "test-lock-token"

OBDOBI_IDENT = "HES-100001"


class RunDataImportHeslarDataceTest(TestCase):
    """Testy ``run_data_import`` pro ``HeslarDataceMapper``."""

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená fixture data pro importní testy."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            obdobi_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_OBDOBI, defaults={"nazev": "obdobi"})
            cls.obdobi, _ = Heslar.objects.get_or_create(
                ident_cely=OBDOBI_IDENT,
                defaults={
                    "nazev_heslare": obdobi_nazev,
                    "heslo": "Doba železná",
                    "heslo_en": "Iron Age",
                    "zkratka": "DZ",
                    "razeni": 1,
                },
            )

            typ_org_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_ORGANIZACE_TYP, defaults={"nazev": "typ_organizace"}
            )
            typ_org, _ = Heslar.objects.get_or_create(
                nazev_heslare=typ_org_nazev,
                zkratka="T",
                defaults={"ident_cely": "HES-IMP-TYPORG-001", "heslo": "Test", "heslo_en": "Test"},
            )
            pristupnost_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_PRISTUPNOST, defaults={"nazev": "pristupnost"}
            )
            pristupnost, _ = Heslar.objects.get_or_create(
                nazev_heslare=pristupnost_nazev,
                zkratka="A",
                defaults={"ident_cely": "HES-IMP-PRST-001", "heslo": "Veřejný", "heslo_en": "Public"},
            )
            licence_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_LICENCE, defaults={"nazev": "licence"})
            licence, _ = Heslar.objects.get_or_create(
                nazev_heslare=licence_nazev,
                zkratka="L",
                defaults={"ident_cely": "HES-IMP-LIC-001", "heslo": "Lic", "heslo_en": "Lic"},
            )
            cls.organizace, _ = Organizace.objects.get_or_create(
                ident_cely="ORG-IMP-HD-001",
                defaults={
                    "nazev": "Org pro import datace",
                    "nazev_zkraceny": "ORGHDIMP",
                    "typ_organizace": typ_org,
                    "zverejneni_pristupnost": pristupnost,
                    "licence": licence,
                },
            )
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner-hd@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-IMP-HD-001",
                first_name="Import",
                last_name="Runner",
            )

    @staticmethod
    def _build_insert_payload(obdobi_ident: str) -> dict:
        return {
            "__file_name": FILE_KEY,
            "obdobi": obdobi_ident,
            "rok_od_min": 800,
            "rok_od_max": 750,
            "rok_do_min": 100,
            "rok_do_max": 50,
            "poznamka": "Importovaná datace",
        }

    def _build_redis(self, performed_action: str) -> FakeRedis:
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
            serialized_record = {"__file_name": FILE_KEY, "obdobi": OBDOBI_IDENT}
        else:
            serialized_record = self._build_insert_payload(OBDOBI_IDENT)
        return FakeRedis(
            {
                f"import_data_count_{JOB_ID}": "1",
                f"import_performed_action_{JOB_ID}": performed_action,
                f"import_data_{JOB_ID}_record_0": json.dumps(serialized_record),
            }
        )

    def _run_import(
        self,
        fake_redis: FakeRedis,
        save_metadata_side_effect=None,
        refresh_lock_side_effect=None,
    ):
        save_metadata_calls: list = []

        def default_side_effect(self, *args, **kwargs):
            save_metadata_calls.append(self)

        side_effect = save_metadata_side_effect or default_side_effect
        refresh_lock_kwargs = (
            {"side_effect": refresh_lock_side_effect}
            if refresh_lock_side_effect is not None
            else {"return_value": True}
        )
        with patch("core.connectors.RedisConnector.get_connection", return_value=fake_redis), patch(
            "core.connectors.RedisConnector.refresh_import_lock", **refresh_lock_kwargs
        ), patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch(
            "xml_generator.models.ModelWithMetadata.save_metadata",
            autospec=True,
            side_effect=side_effect,
        ), patch(
            "xml_generator.models.ModelWithMetadata.record_deletion",
            autospec=True,
            return_value=None,
        ), patch(
            "cron.tasks.FedoraTransaction"
        ) as fedora_transaction_mock, patch(
            "cron.tasks.FedoraDeletionOnlyTransaction"
        ) as fedora_deletion_mock, patch(
            "heslar.signals.FedoraTransaction"
        ) as signals_fedora_transaction_mock:
            fedora_transaction_mock.return_value = MagicMock(uid="test-fedora-uid", updated_ident_cely=set())
            fedora_deletion_mock.return_value = MagicMock(uid="test-fedora-deletion-uid", updated_ident_cely=set())
            signals_fedora_transaction_mock.return_value = MagicMock(uid="test-signals-fedora-uid")
            cron_tasks.run_data_import(JOB_ID, self.user.id, LOCK_TOKEN)
        return save_metadata_calls

    def _create_existing_datace(self) -> HeslarDatace:
        return HeslarDatace.objects.create(
            obdobi=self.obdobi,
            rok_od_min=1000,
            rok_od_max=900,
            rok_do_min=200,
            rok_do_max=150,
            poznamka="Původní",
        )

    def _assert_import_failed(self, fake_redis: FakeRedis):
        progress_raw = fake_redis.get(f"import_data_progress_{JOB_ID}")
        self.assertIsNotNone(progress_raw)
        self.assertEqual(int(progress_raw.decode("utf-8")), cron_tasks.IMPORT_PROGRESS_PHASE_FAILED)
        self.assertIsNotNone(fake_redis.get(f"import_data_stop_{JOB_ID}"))

    def test_insert_writes_datace_to_database(self):
        """Ověřuje, že INSERT import zapíše záznam datace do databáze."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self.assertTrue(HeslarDatace.objects.filter(obdobi=self.obdobi).exists())
        created = HeslarDatace.objects.get(obdobi=self.obdobi)
        self.assertEqual(created.rok_od_min, 800)
        self.assertEqual(created.poznamka, "Importovaná datace")

        primary_keys_raw = fake_redis.get(f"import_data_primary_keys_{JOB_ID}")
        self.assertIsNotNone(primary_keys_raw)

    def test_update_modifies_existing_datace(self):
        """Ověřuje, že UPDATE import upraví existující záznam datace."""
        self._create_existing_datace()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        updated = HeslarDatace.objects.get(obdobi=self.obdobi)
        self.assertEqual(updated.rok_od_min, 800)
        self.assertEqual(updated.poznamka, "Importovaná datace")

    def test_delete_removes_datace(self):
        """Ověřuje, že DELETE import smaže záznam datace."""
        self._create_existing_datace()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        self.assertFalse(HeslarDatace.objects.filter(obdobi=self.obdobi).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu heslar datace označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání DB.")

        with patch.object(HeslarDatace, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu heslar datace označí import jako selhaný."""
        from core.import_data_mappers import HeslarDataceMapper
        from historie.models import Historie

        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání Historie.")

        with patch.object(HeslarDataceMapper, "get_record_history", staticmethod(lambda record: record)), patch.object(
            Historie, "save", failing_save
        ):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení metadat Fedory pro záznam heslar datace označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save_metadata(self, *args, **kwargs):
            raise RuntimeError("Selhání Fedory.")

        self._run_import(fake_redis, save_metadata_side_effect=failing_save_metadata)

        self._assert_import_failed(fake_redis)

    def _build_multi_record_redis(self, records: list[dict]) -> FakeRedis:
        initial = {
            f"import_data_count_{JOB_ID}": str(len(records)),
            f"import_performed_action_{JOB_ID}": ImportDataAdminForm.PERFORMED_ACTION_INSERT,
        }
        for index, record in enumerate(records):
            initial[f"import_data_{JOB_ID}_record_{index}"] = json.dumps(record)
        return FakeRedis(initial)

    def test_failure_mid_batch_rolls_back_all_inserted_records(self):
        # PK je OneToOne FK na obdobi — nelze tedy duplikovat PK pro běžnou IntegrityError
        # (Django by INSERT s existujícím PK přetížil na UPDATE). Druhý záznam místo toho
        # odkazuje na neexistující obdobi → ``ImportDataMissingReferencedValueError`` ve fázi
        # ``map()`` → vnitřní except zavolá ``set_rollback(True)`` a první (uložený) záznam
        # je odvolán spolu se zbytkem dávky.
        """Ověřuje, že selhání uprostřed dávky vrátí vložené záznamy heslar datace zpět."""
        first = self._build_insert_payload(OBDOBI_IDENT)
        bad = self._build_insert_payload("HES-999999")
        fake_redis = self._build_multi_record_redis([first, bad])

        self._run_import(fake_redis)

        self.assertFalse(HeslarDatace.objects.filter(obdobi=self.obdobi).exists())
        self._assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu heslar datace nastaví stav zastaveno."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)
        fake_redis.set(f"import_data_stop_{JOB_ID}", "1")

        self._run_import(fake_redis)

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu heslar datace označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)
        self.assertFalse(HeslarDatace.objects.filter(obdobi=self.obdobi).exists())

    # Pozn.: ``test_insert_of_duplicate_pk_marks_import_as_failed`` nemá pro HeslarDatace
    # smysl — PK je ``OneToOneField`` na ``obdobi``; Django pro INSERT s existujícím PK
    # mlčky provede UPDATE (a ``import_validation`` v tasku ``run_data_import`` se nevolá),
    # takže k IntegrityError nedojde.

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu heslar datace nastaví stav failed_lock_lost."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis, refresh_lock_side_effect=[True, False, False, False, False])

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self._assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Ověřuje, že úspěšný import záznamu heslar datace zapíše success marker do detailu průběhu."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
