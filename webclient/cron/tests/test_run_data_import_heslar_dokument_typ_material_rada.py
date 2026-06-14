"""Jednotkové testy pro ``cron.tasks.run_data_import`` — import HeslarDokumentTypMaterialRada."""

import json
from unittest.mock import MagicMock, patch

from core.constants import ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.tests.fake_redis import FakeRedis
from cron import tasks as cron_tasks
from django.contrib.auth.models import Group
from django.test import TestCase
from heslar.hesla import (
    HESLAR_DOKUMENT_MATERIAL,
    HESLAR_DOKUMENT_RADA,
    HESLAR_DOKUMENT_TYP,
    HESLAR_LICENCE,
    HESLAR_ORGANIZACE_TYP,
    HESLAR_PRISTUPNOST,
)
from heslar.models import Heslar, HeslarDokumentTypMaterialRada, HeslarNazev
from uzivatel.models import Organizace, User

FILE_KEY = "heslar_dokument_typ_material_rada"
JOB_ID = "test-job-hdtm"
LOCK_TOKEN = "test-lock-token"

TYP_IDENT = "HES-200001"
MATERIAL_IDENT = "HES-200002"
RADA_IDENT = "HES-200003"


class RunDataImportHeslarDokumentTypMaterialRadaTest(TestCase):
    """Testy ``run_data_import`` pro ``HeslarDokumentTypMaterialRadaMapper``."""

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená fixture data pro importní testy."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            typ_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_DOKUMENT_TYP, defaults={"nazev": "dokument_typ"})
            cls.typ_heslar, _ = Heslar.objects.get_or_create(
                ident_cely=TYP_IDENT,
                defaults={
                    "nazev_heslare": typ_nazev,
                    "heslo": "Typ",
                    "heslo_en": "Type",
                    "zkratka": "TY",
                    "razeni": 1,
                },
            )
            material_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_DOKUMENT_MATERIAL, defaults={"nazev": "dokument_material"}
            )
            cls.material_heslar, _ = Heslar.objects.get_or_create(
                ident_cely=MATERIAL_IDENT,
                defaults={
                    "nazev_heslare": material_nazev,
                    "heslo": "Material",
                    "heslo_en": "Material",
                    "zkratka": "MA",
                    "razeni": 1,
                },
            )
            rada_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_DOKUMENT_RADA, defaults={"nazev": "dokument_rada"}
            )
            cls.rada_heslar, _ = Heslar.objects.get_or_create(
                ident_cely=RADA_IDENT,
                defaults={
                    "nazev_heslare": rada_nazev,
                    "heslo": "Rada",
                    "heslo_en": "Series",
                    "zkratka": "RA",
                    "razeni": 1,
                },
            )

            typ_org_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_ORGANIZACE_TYP, defaults={"nazev": "typ_organizace"}
            )
            typ_org, _ = Heslar.objects.get_or_create(
                nazev_heslare=typ_org_nazev,
                zkratka="T",
                defaults={"ident_cely": "HES-IMP-TYPORG-001", "heslo": "T", "heslo_en": "T"},
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
                defaults={"ident_cely": "HES-IMP-LIC-001", "heslo": "L", "heslo_en": "L"},
            )
            cls.organizace, _ = Organizace.objects.get_or_create(
                ident_cely="ORG-IMP-HDTM-001",
                defaults={
                    "nazev": "Org HDTM",
                    "nazev_zkraceny": "ORGHDTM",
                    "typ_organizace": typ_org,
                    "zverejneni_pristupnost": pristupnost,
                    "licence": licence,
                },
            )
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner-hdtm@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-IMP-HDTM-001",
                first_name="Import",
                last_name="Runner",
            )

    @staticmethod
    def _build_insert_payload(material_ident: str) -> dict:
        return {
            "__file_name": FILE_KEY,
            "dokument_typ": TYP_IDENT,
            "dokument_material": material_ident,
            "dokument_rada": RADA_IDENT,
        }

    def _build_redis_for_insert(self, material_ident: str = MATERIAL_IDENT) -> FakeRedis:
        return FakeRedis(
            {
                f"import_data_count_{JOB_ID}": "1",
                f"import_performed_action_{JOB_ID}": ImportDataAdminForm.PERFORMED_ACTION_INSERT,
                f"import_data_{JOB_ID}_record_0": json.dumps(self._build_insert_payload(material_ident)),
            }
        )

    def _build_redis_for_update(self, pk_value: str) -> FakeRedis:
        payload = self._build_insert_payload(MATERIAL_IDENT)
        payload["id"] = pk_value
        return FakeRedis(
            {
                f"import_data_count_{JOB_ID}": "1",
                f"import_performed_action_{JOB_ID}": ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
                f"import_data_{JOB_ID}_record_0": json.dumps(payload),
            }
        )

    def _build_redis_for_delete(self, pk_value: str) -> FakeRedis:
        return FakeRedis(
            {
                f"import_data_count_{JOB_ID}": "1",
                f"import_performed_action_{JOB_ID}": ImportDataAdminForm.PERFORMED_ACTION_DELETE,
                f"import_data_{JOB_ID}_record_0": json.dumps({"__file_name": FILE_KEY, "id": pk_value}),
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

    def _create_existing_record(self, material_heslar=None) -> HeslarDokumentTypMaterialRada:
        return HeslarDokumentTypMaterialRada.objects.create(
            dokument_typ=self.typ_heslar,
            dokument_material=material_heslar or self.material_heslar,
            dokument_rada=self.rada_heslar,
        )

    def _assert_import_failed(self, fake_redis: FakeRedis):
        progress_raw = fake_redis.get(f"import_data_progress_{JOB_ID}")
        self.assertIsNotNone(progress_raw)
        self.assertEqual(int(progress_raw.decode("utf-8")), cron_tasks.IMPORT_PROGRESS_PHASE_FAILED)
        self.assertIsNotNone(fake_redis.get(f"import_data_stop_{JOB_ID}"))

    def test_insert_writes_record_to_database(self):
        """Ověřuje, že INSERT import zapíše záznam record do databáze."""
        fake_redis = self._build_redis_for_insert()

        self._run_import(fake_redis)

        self.assertTrue(
            HeslarDokumentTypMaterialRada.objects.filter(
                dokument_typ=self.typ_heslar, dokument_material=self.material_heslar
            ).exists()
        )

    def test_update_modifies_existing_record(self):
        """Ověřuje, že UPDATE import upraví existující záznam record."""
        existing = self._create_existing_record()
        fake_redis = self._build_redis_for_update(f"hdtm-{existing.pk}")

        self._run_import(fake_redis)

        # Pole stejná, ale UPDATE prošel (save_metadata bylo voláno přes signál).
        refreshed = HeslarDokumentTypMaterialRada.objects.get(pk=existing.pk)
        self.assertEqual(refreshed.dokument_rada_id, self.rada_heslar.pk)

    def test_delete_removes_record(self):
        """Ověřuje, že DELETE import smaže záznam record."""
        existing = self._create_existing_record()
        fake_redis = self._build_redis_for_delete(f"hdtm-{existing.pk}")

        self._run_import(fake_redis)

        self.assertFalse(HeslarDokumentTypMaterialRada.objects.filter(pk=existing.pk).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu heslar dokument typ material rada označí import jako selhaný."""
        fake_redis = self._build_redis_for_insert()

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání DB.")

        with patch.object(HeslarDokumentTypMaterialRada, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu heslar dokument typ material rada označí import jako selhaný."""
        from core.import_data_mappers import HeslarDokumentTypMaterialRadaMapper
        from historie.models import Historie

        fake_redis = self._build_redis_for_insert()

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání Historie.")

        with patch.object(
            HeslarDokumentTypMaterialRadaMapper,
            "get_record_history",
            staticmethod(lambda record: record),
        ), patch.object(Historie, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení metadat Fedory pro záznam heslar dokument typ material rada označí import jako selhaný."""
        fake_redis = self._build_redis_for_insert()

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
        # 2. záznam má stejnou kombinaci (typ, material) → IntegrityError na unique_together.
        """Ověřuje, že selhání uprostřed dávky vrátí vložené záznamy heslar dokument typ material rada zpět."""
        first = self._build_insert_payload(MATERIAL_IDENT)
        duplicate = self._build_insert_payload(MATERIAL_IDENT)
        fake_redis = self._build_multi_record_redis([first, duplicate])

        self._run_import(fake_redis)

        self.assertFalse(
            HeslarDokumentTypMaterialRada.objects.filter(
                dokument_typ=self.typ_heslar, dokument_material=self.material_heslar
            ).exists()
        )
        self._assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu heslar dokument typ material rada nastaví stav zastaveno."""
        fake_redis = self._build_redis_for_insert()
        fake_redis.set(f"import_data_stop_{JOB_ID}", "1")

        self._run_import(fake_redis)

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu heslar dokument typ material rada označí import jako selhaný."""
        fake_redis = self._build_redis_for_update("hdtm-9999999")

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_insert_of_duplicate_combination_marks_import_as_failed(self):
        """Ověřuje, že INSERT duplicitního combination pro záznam heslar dokument typ material rada označí import jako selhaný."""
        self._create_existing_record()
        fake_redis = self._build_redis_for_insert()

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu heslar dokument typ material rada nastaví stav failed_lock_lost."""
        fake_redis = self._build_redis_for_insert()

        self._run_import(fake_redis, refresh_lock_side_effect=[True, False, False, False, False])

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self._assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Ověřuje, že úspěšný import záznamu heslar dokument typ material rada zapíše success marker do detailu průběhu."""
        fake_redis = self._build_redis_for_insert()

        self._run_import(fake_redis)

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
