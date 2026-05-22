"""Jednotkové testy pro ``cron.tasks.run_data_import`` — import AkceVedouci."""

import json
from unittest.mock import MagicMock, patch

from arch_z.models import AkceVedouci
from core.constants import ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.tests.fake_redis import FakeRedis
from cron import tasks as cron_tasks
from cron.tests._import_test_fixtures import (
    create_akce,
    create_akce_typ,
    create_archeologicky_zaznam,
    create_heslar_fixtures,
    create_organizace,
    create_ruian_with_pian,
    create_specifikace_data,
)
from django.contrib.auth.models import Group
from django.test import TestCase
from uzivatel.models import Osoba, User

FILE_KEY = "az_akce_vedouci"
JOB_ID = "test-job-av"
LOCK_TOKEN = "test-lock-token"

AZ_IDENT = "C-202300501A"
VEDOUCI_IDENT = "OS-400001"


class RunDataImportAkceVedouciTest(TestCase):
    """Testy ``run_data_import`` pro ``AkceVedouciMapper``."""

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená fixture data pro importní testy."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            heslars = create_heslar_fixtures("av")
            katastr, _ = create_ruian_with_pian("av", "P-0001-800001", heslars)
            cls.organizace = create_organizace("av", heslars)
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner-av@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-IMP-AV-001",
                first_name="Import",
                last_name="Runner",
            )
            cls.az = create_archeologicky_zaznam(AZ_IDENT, katastr, heslars["pristupnost"])
            specifikace = create_specifikace_data("av")
            akce_typ = create_akce_typ("av")
            cls.akce = create_akce(cls.az, specifikace_data=specifikace, hlavni_typ=akce_typ)
            cls.vedouci = Osoba.objects.create(
                ident_cely=VEDOUCI_IDENT,
                jmeno="Petr",
                prijmeni="Vedouci",
                vypis="Vedouci P.",
                vypis_cely="Vedouci, Petr",
                rok_narozeni=1980,
            )

    def _build_insert_payload(self) -> dict:
        return {
            "__file_name": FILE_KEY,
            "akce": AZ_IDENT,
            "vedouci": VEDOUCI_IDENT,
            "organizace": self.organizace.ident_cely,
        }

    def _build_update_payload(self, pk_value: str) -> dict:
        payload = self._build_insert_payload()
        payload["id"] = pk_value
        return payload

    def _build_redis(self, performed_action: str, pk_value: str = None) -> FakeRedis:
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
            serialized_record = {"__file_name": FILE_KEY, "id": pk_value}
        elif performed_action == ImportDataAdminForm.PERFORMED_ACTION_UPDATE:
            serialized_record = self._build_update_payload(pk_value)
        else:
            serialized_record = self._build_insert_payload()
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
            "uzivatel.signals.FedoraTransaction"
        ) as signals_fedora_transaction_mock:
            fedora_transaction_mock.return_value = MagicMock(uid="test-fedora-uid", updated_ident_cely=set())
            fedora_deletion_mock.return_value = MagicMock(uid="test-fedora-deletion-uid", updated_ident_cely=set())
            signals_fedora_transaction_mock.return_value = MagicMock(uid="test-signals-fedora-uid")
            cron_tasks.run_data_import(JOB_ID, self.user.id, LOCK_TOKEN)
        return save_metadata_calls

    def _create_existing_av(self) -> AkceVedouci:
        return AkceVedouci.objects.create(akce=self.akce, vedouci=self.vedouci, organizace=self.organizace)

    def _assert_import_failed(self, fake_redis: FakeRedis):
        progress_raw = fake_redis.get(f"import_data_progress_{JOB_ID}")
        self.assertIsNotNone(progress_raw)
        self.assertEqual(int(progress_raw.decode("utf-8")), cron_tasks.IMPORT_PROGRESS_PHASE_FAILED)
        self.assertIsNotNone(fake_redis.get(f"import_data_stop_{JOB_ID}"))

    def test_insert_writes_av_to_database(self):
        """Ověřuje, že INSERT import zapíše záznam akce vedouci do databáze."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self.assertTrue(AkceVedouci.objects.filter(akce=self.akce, vedouci=self.vedouci).exists())

    def test_update_modifies_existing_av(self):
        """Ověřuje, že UPDATE import upraví existující záznam akce vedouci."""
        existing = self._create_existing_av()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE, pk_value=f"vedo-{existing.pk}")

        self._run_import(fake_redis)

        refreshed = AkceVedouci.objects.get(pk=existing.pk)
        self.assertEqual(refreshed.organizace_id, self.organizace.pk)

    def test_delete_removes_av_from_database(self):
        """Ověřuje, že DELETE import smaže záznam akce vedouci z databáze."""
        existing = self._create_existing_av()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE, pk_value=f"vedo-{existing.pk}")

        self._run_import(fake_redis)

        self.assertFalse(AkceVedouci.objects.filter(pk=existing.pk).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu akce vedouci označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání DB.")

        with patch.object(AkceVedouci, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu akce vedouci označí import jako selhaný."""
        from core.import_data_mappers import AkceVedouciMapper
        from historie.models import Historie

        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání Historie.")

        with patch.object(AkceVedouciMapper, "get_record_history", staticmethod(lambda record: record)), patch.object(
            Historie, "save", failing_save
        ):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení metadat Fedory pro záznam akce vedouci označí import jako selhaný."""
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
        # unique_together (akce, vedouci): druhý INSERT s touž kombinací → IntegrityError.
        """Ověřuje, že selhání uprostřed dávky vrátí vložené záznamy akce vedouci zpět."""
        first = self._build_insert_payload()
        duplicate = self._build_insert_payload()
        fake_redis = self._build_multi_record_redis([first, duplicate])

        self._run_import(fake_redis)

        self.assertFalse(AkceVedouci.objects.filter(akce=self.akce, vedouci=self.vedouci).exists())
        self._assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu akce vedouci nastaví stav zastaveno."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)
        fake_redis.set(f"import_data_stop_{JOB_ID}", "1")

        self._run_import(fake_redis)

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu akce vedouci označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE, pk_value="vedo-9999999")

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_insert_of_duplicate_combination_marks_import_as_failed(self):
        """Ověřuje, že INSERT duplicitního combination pro záznam akce vedouci označí import jako selhaný."""
        self._create_existing_av()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu akce vedouci nastaví stav failed_lock_lost."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis, refresh_lock_side_effect=[True, False, False, False, False])

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self._assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Ověřuje, že úspěšný import záznamu akce vedouci zapíše success marker do detailu průběhu."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
