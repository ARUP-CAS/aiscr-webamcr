"""Jednotkové testy pro ``cron.tasks.run_data_import`` — import Oznamovatel."""

import json
from unittest.mock import MagicMock, patch

from core.constants import IMPORT, ROLE_BADATEL_ID
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
from historie.models import Historie
from oznameni.models import Oznamovatel
from uzivatel.models import User

FILE_KEY = "projekty_oznamovatele"
JOB_ID = "test-job-poz"
LOCK_TOKEN = "test-lock-token"

PROJEKT_IDENT = "C-202300301"


class RunDataImportProjektOznamovatelTest(TestCase):
    """Testy ``run_data_import`` pro ``ProjektOznamovatelMapper``."""

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
            heslars = create_heslar_fixtures("poz")
            katastr, _ = create_ruian_with_pian("poz", "P-0001-600001", heslars)
            cls.organizace = create_organizace("poz", heslars)
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner-poz@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-IMP-POZ-001",
                first_name="Import",
                last_name="Runner",
            )
            cls.typ_projektu = create_projekt_typ("poz")
            cls.projekt = create_projekt(PROJEKT_IDENT, katastr, cls.typ_projektu)
            cls.projekt2 = create_projekt("C-202300302", katastr, cls.typ_projektu)

    @staticmethod
    def _build_insert_payload(projekt_ident: str = PROJEKT_IDENT) -> dict:
        return {
            "__file_name": FILE_KEY,
            "projekt": projekt_ident,
            "oznamovatel": "Stavební s.r.o.",
            "odpovedna_osoba": "Jan Novák",
            "adresa": "Hlavní 1, Praha",
            "telefon": "+420123456789",
            "email": "stavebni@example.cz",
            "poznamka": "Poznámka",
        }

    def _build_redis(self, performed_action: str) -> FakeRedis:
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
            serialized_record = {"__file_name": FILE_KEY, "projekt": PROJEKT_IDENT}
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

    def _create_existing_oznamovatel(self) -> Oznamovatel:
        return Oznamovatel.objects.create(
            projekt=self.projekt,
            oznamovatel="Původní",
            odpovedna_osoba="Pavel Starý",
            adresa="Stará 2",
            telefon="000",
            email="puvodni@example.cz",
            poznamka=None,
        )

    def _assert_import_failed(self, fake_redis: FakeRedis):
        progress_raw = fake_redis.get(f"import_data_progress_{JOB_ID}")
        self.assertIsNotNone(progress_raw)
        self.assertEqual(int(progress_raw.decode("utf-8")), cron_tasks.IMPORT_PROGRESS_PHASE_FAILED)
        self.assertIsNotNone(fake_redis.get(f"import_data_stop_{JOB_ID}"))

    def test_insert_writes_oznamovatel_to_database(self):
        """Ověřuje, že INSERT import zapíše záznam oznamovatel do databáze."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self.assertTrue(Oznamovatel.objects.filter(projekt=self.projekt).exists())

    def test_update_modifies_existing_oznamovatel(self):
        """Ověřuje, že UPDATE import upraví existující záznam oznamovatel."""
        self._create_existing_oznamovatel()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        updated = Oznamovatel.objects.get(projekt=self.projekt)
        self.assertEqual(updated.oznamovatel, "Stavební s.r.o.")

    def test_delete_removes_oznamovatel_from_database(self):
        """Ověřuje, že DELETE import smaže záznam oznamovatel z databáze."""
        self._create_existing_oznamovatel()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        self.assertFalse(Oznamovatel.objects.filter(projekt=self.projekt).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu projekt oznamovatel označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání DB.")

        with patch.object(Oznamovatel, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu projekt oznamovatel označí import jako selhaný."""
        from historie.models import Historie

        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení metadat Fedory pro záznam projekt oznamovatel označí import jako selhaný."""
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
        # Oznamovatel.projekt je OneToOneField primary_key=True → INSERT s existujícím
        # PK by Django mlčky převedl na UPDATE. Místo toho druhý záznam odkazuje na
        # neexistující projekt → ImportDataMissingReferencedValueError ve fázi map().
        """Ověřuje, že selhání uprostřed dávky vrátí vložené záznamy projekt oznamovatel zpět."""
        first = self._build_insert_payload("C-202300302")
        bad = self._build_insert_payload("C-999999999")
        fake_redis = self._build_multi_record_redis([first, bad])

        self._run_import(fake_redis)

        self.assertFalse(Oznamovatel.objects.filter(projekt=self.projekt2).exists())
        self._assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu projekt oznamovatel nastaví stav zastaveno."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)
        fake_redis.set(f"import_data_stop_{JOB_ID}", "1")

        self._run_import(fake_redis)

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu projekt oznamovatel označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    # Pozn.: ``test_insert_of_duplicate_pk_marks_import_as_failed`` nemá pro Oznamovatel
    # smysl — PK je ``OneToOneField`` na ``projekt``; Django pro INSERT s existujícím
    # PK mlčky provede UPDATE.

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu projekt oznamovatel nastaví stav failed_lock_lost."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis, refresh_lock_side_effect=[True, False, False, False, False])

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self._assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Ověřuje, že úspěšný import záznamu projekt oznamovatel zapíše success marker do detailu průběhu."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)

    def test_delete_creates_imp_history_record_on_parent_projekt(self):
        """DELETE oznamovatele vytvoří IMP historický záznam na nadřazeném projektu."""
        self._create_existing_oznamovatel()
        history_before = Historie.objects.filter(vazba=self.projekt.historie, typ_zmeny=IMPORT).count()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        history_after = Historie.objects.filter(vazba=self.projekt.historie, typ_zmeny=IMPORT).count()
        self.assertEqual(history_after, history_before + 1)

    def test_delete_creates_exactly_one_imp_history_record_per_projekt(self):
        """DELETE oznamovatele vytvoří právě jeden IMP historický záznam na nadřazeném projektu, ne více."""
        self._create_existing_oznamovatel()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        imp_records = Historie.objects.filter(vazba=self.projekt.historie, typ_zmeny=IMPORT)
        self.assertEqual(imp_records.count(), 1)
