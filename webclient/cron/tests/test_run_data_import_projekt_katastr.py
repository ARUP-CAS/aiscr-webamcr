"""Jednotkové testy pro ``cron.tasks.run_data_import`` — import ProjektKatastr."""

import json
from unittest.mock import MagicMock, patch

from core.constants import ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.tests.fake_redis import FakeRedis
from cron import tasks as cron_tasks
from cron.tests._import_test_fixtures import (
    create_heslar_fixtures,
    create_organizace,
    create_projekt,
    create_projekt_typ,
    create_ruian_with_pian,
)
from django.contrib.auth.models import Group
from django.test import TestCase
from heslar.models import RuianKatastr, RuianOkres
from projekt.models import ProjektKatastr
from uzivatel.models import User

FILE_KEY = "projekty_katastry"
JOB_ID = "test-job-pk"
LOCK_TOKEN = "test-lock-token"

PROJEKT_IDENT = "C-202300201"


class RunDataImportProjektKatastrTest(TestCase):
    """Testy ``run_data_import`` pro ``ProjektKatastrMapper``."""

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená fixture data pro importní testy."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None), patch(
            "projekt.models.Projekt.set_pristupnost", return_value=None
        ):
            heslars = create_heslar_fixtures("pk")
            cls.katastr_main, _ = create_ruian_with_pian("pk", "P-0001-500001", heslars)
            cls.organizace = create_organizace("pk", heslars)
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner-pk@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-IMP-PK-001",
                first_name="Import",
                last_name="Runner",
            )
            cls.typ_projektu = create_projekt_typ("pk")
            cls.projekt = create_projekt(PROJEKT_IDENT, cls.katastr_main, cls.typ_projektu)
            # Druhý katastr, na který se naváže via ProjektKatastr.
            point_wkt = "SRID=4326;POINT(15.0 50.0)"
            multipoly_wkt = "SRID=4326;MULTIPOLYGON(((14.9 49.9, 15.1 49.9, 15.1 50.1, 14.9 50.1, 14.9 49.9)))"
            other_okres = RuianOkres.objects.get(nazev="Okres-pk")
            cls.katastr_other = RuianKatastr(
                nazev="Katastr-pk-2",
                kod=899999,
                okres=other_okres,
                definicni_bod=point_wkt,
                hranice=multipoly_wkt,
            )
            cls.katastr_other.suppress_signal = True
            cls.katastr_other.save()

    def _build_pk_payload(self, projekt_ident: str = PROJEKT_IDENT, katastr_kod: int = None) -> dict:
        if katastr_kod is None:
            katastr_kod = self.katastr_other.kod
        return {
            "__file_name": FILE_KEY,
            "projekt": projekt_ident,
            "katastr": f"ruian-{katastr_kod}",
        }

    def _build_redis(self, performed_action: str, katastr_kod: int = None) -> FakeRedis:
        payload = self._build_pk_payload(katastr_kod=katastr_kod)
        return FakeRedis(
            {
                f"import_data_count_{JOB_ID}": "1",
                f"import_performed_action_{JOB_ID}": performed_action,
                f"import_data_{JOB_ID}_record_0": json.dumps(payload),
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
            "projekt.signals.check_hlidaci_pes"
        ), patch(
            "projekt.signals.update_single_redis_snapshot"
        ), patch(
            "projekt.signals.check_if_task_queued", return_value=True
        ), patch(
            "projekt.signals.invalidate_model"
        ), patch(
            "projekt.models.Projekt.set_pristupnost", return_value=None
        ), patch(
            "cron.tasks.FedoraTransaction"
        ) as fedora_transaction_mock, patch(
            "cron.tasks.FedoraDeletionOnlyTransaction"
        ) as fedora_deletion_mock:
            fedora_transaction_mock.return_value = MagicMock(uid="test-fedora-uid", updated_ident_cely=set())
            fedora_deletion_mock.return_value = MagicMock(uid="test-fedora-deletion-uid", updated_ident_cely=set())
            cron_tasks.run_data_import(JOB_ID, self.user.id, LOCK_TOKEN)
        return save_metadata_calls

    def _create_existing_pk(self) -> ProjektKatastr:
        return ProjektKatastr.objects.create(projekt=self.projekt, katastr=self.katastr_other)

    def _assert_import_failed(self, fake_redis: FakeRedis):
        progress_raw = fake_redis.get(f"import_data_progress_{JOB_ID}")
        self.assertIsNotNone(progress_raw)
        self.assertEqual(int(progress_raw.decode("utf-8")), cron_tasks.IMPORT_PROGRESS_PHASE_FAILED)
        self.assertIsNotNone(fake_redis.get(f"import_data_stop_{JOB_ID}"))

    def test_insert_writes_pk_to_database(self):
        """Ověřuje, že INSERT import zapíše záznam projekt katastr do databáze."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self.assertTrue(ProjektKatastr.objects.filter(projekt=self.projekt, katastr=self.katastr_other).exists())

    def test_update_marks_import_as_failed(self):
        # ProjektKatastrMapper.allow_update = False → každý UPDATE skončí jako selhalý import.
        """Ověřuje, že UPDATE import záznamu projekt katastr skončí selháním."""
        self._create_existing_pk()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_delete_removes_pk_from_database(self):
        """Ověřuje, že DELETE import smaže záznam projekt katastr z databáze."""
        self._create_existing_pk()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        self.assertFalse(ProjektKatastr.objects.filter(projekt=self.projekt, katastr=self.katastr_other).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu projekt katastr označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání DB.")

        with patch.object(ProjektKatastr, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu projekt katastr označí import jako selhaný."""
        from core.import_data_mappers import ProjektKatastrMapper
        from historie.models import Historie

        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání Historie.")

        with patch.object(
            ProjektKatastrMapper, "get_record_history", staticmethod(lambda record: record)
        ), patch.object(Historie, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení metadat Fedory pro záznam projekt katastr označí import jako selhaný."""
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
        """Ověřuje, že selhání uprostřed dávky vrátí vložené záznamy projekt katastr zpět."""
        first = self._build_pk_payload()
        duplicate = self._build_pk_payload()  # stejná (projekt, katastr) → IntegrityError unique_together
        fake_redis = self._build_multi_record_redis([first, duplicate])

        self._run_import(fake_redis)

        self.assertFalse(ProjektKatastr.objects.filter(projekt=self.projekt, katastr=self.katastr_other).exists())
        self._assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu projekt katastr nastaví stav zastaveno."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)
        fake_redis.set(f"import_data_stop_{JOB_ID}", "1")

        self._run_import(fake_redis)

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_delete_of_nonexistent_record_marks_import_as_failed(self):
        # Bez pre-create: DELETE má padnout na DoesNotExist v ``create_records``.
        """Ověřuje, že DELETE neexistujícího záznamu projekt katastr označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_insert_of_duplicate_pk_marks_import_as_failed(self):
        """Ověřuje, že INSERT duplicitního projekt katastr pro záznam projekt katastr označí import jako selhaný."""
        self._create_existing_pk()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu projekt katastr nastaví stav failed_lock_lost."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis, refresh_lock_side_effect=[True, False, False, False, False])

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self._assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Ověřuje, že úspěšný import záznamu projekt katastr zapíše success marker do detailu průběhu."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
