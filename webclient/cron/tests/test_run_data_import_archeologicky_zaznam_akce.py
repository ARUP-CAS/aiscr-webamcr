"""Jednotkové testy pro ``cron.tasks.run_data_import`` — import Akce (MultipleClassImportModelMapper).

ArcheologickyZaznamAkceMapper ukládá dvě instance (ArcheologickyZaznam + Akce) v rámci
jednoho záznamu. DELETE pro tento mapper není podporován (``create_records`` vrací pro
DELETE prázdný seznam), proto je vynechán z testovací matice.
"""

import json
from unittest.mock import MagicMock, patch

from arch_z.models import Akce, ArcheologickyZaznam
from core.constants import ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.tests.fake_redis import FakeRedis
from cron import tasks as cron_tasks
from cron.tests._import_test_fixtures import (
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

FILE_KEY = "az_akce"
JOB_ID = "test-job-aza"
LOCK_TOKEN = "test-lock-token"

AZ_IDENT = "C-202300601A"
VEDOUCI_IDENT = "OS-500001"


class RunDataImportArcheologickyZaznamAkceTest(TestCase):
    """Testy ``run_data_import`` pro ``ArcheologickyZaznamAkceMapper``."""

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená fixture data pro importní testy."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            heslars = create_heslar_fixtures("aza")
            cls.katastr, _ = create_ruian_with_pian("aza", "P-0001-900001", heslars)
            cls.organizace = create_organizace("aza", heslars)
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner-aza@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-IMP-AZA-001",
                first_name="Import",
                last_name="Runner",
            )
            cls.pristupnost = heslars["pristupnost"]
            cls.specifikace = create_specifikace_data("aza")
            cls.akce_typ = create_akce_typ("aza")
            cls.vedouci = Osoba.objects.create(
                ident_cely=VEDOUCI_IDENT,
                jmeno="Petr",
                prijmeni="Vedouci",
                vypis="Vedouci P.",
                vypis_cely="Vedouci, Petr",
                rok_narozeni=1980,
            )

    def _build_insert_payload(self, ident_cely: str = AZ_IDENT) -> dict:
        return {
            "__file_name": FILE_KEY,
            "ident_cely": ident_cely,
            "stav": 1,
            "typ": Akce.TYP_AKCE_SAMOSTATNA,
            "projekt": None,
            "pristupnost": self.pristupnost.ident_cely,
            "hlavni_katastr": f"ruian-{self.katastr.kod}",
            "uzivatelske_oznaceni": "AZ-IMP-01",
            "lokalizace_okolnosti": "U lesa",
            "je_nz": False,
            "odlozena_nz": False,
            "hlavni_vedouci": VEDOUCI_IDENT,
            "organizace": self.organizace.ident_cely,
            "specifikace_data": self.specifikace.ident_cely,
            "datum_zahajeni": None,
            "datum_ukonceni": None,
            "hlavni_typ": self.akce_typ.ident_cely,
            "vedlejsi_typ": None,
            "ulozeni_nalezu": None,
            "ulozeni_dokumentace": None,
            "souhrn_upresneni": None,
        }

    def _build_redis(self, performed_action: str) -> FakeRedis:
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

    def _create_existing_az_with_akce(self):
        az = create_archeologicky_zaznam(AZ_IDENT, self.katastr, self.pristupnost)
        akce = Akce(
            archeologicky_zaznam=az,
            typ=Akce.TYP_AKCE_SAMOSTATNA,
            projekt=None,
            specifikace_data=self.specifikace,
            hlavni_typ=self.akce_typ,
        )
        akce.suppress_signal = True
        akce.save()
        return az, akce

    def _assert_import_failed(self, fake_redis: FakeRedis):
        progress_raw = fake_redis.get(f"import_data_progress_{JOB_ID}")
        self.assertIsNotNone(progress_raw)
        self.assertEqual(int(progress_raw.decode("utf-8")), cron_tasks.IMPORT_PROGRESS_PHASE_FAILED)
        self.assertIsNotNone(fake_redis.get(f"import_data_stop_{JOB_ID}"))

    def test_insert_writes_az_and_akce_to_database(self):
        """Ověřuje, že INSERT import zapíše záznam az and akce do databáze."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self.assertTrue(ArcheologickyZaznam.objects.filter(ident_cely=AZ_IDENT).exists())
        az = ArcheologickyZaznam.objects.get(ident_cely=AZ_IDENT)
        self.assertEqual(az.typ_zaznamu, ArcheologickyZaznam.TYP_ZAZNAMU_AKCE)
        self.assertTrue(Akce.objects.filter(archeologicky_zaznam=az).exists())

    def test_update_modifies_existing_az_and_akce(self):
        """Ověřuje, že UPDATE import upraví existující záznam az and akce."""
        az, _ = self._create_existing_az_with_akce()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        updated = ArcheologickyZaznam.objects.get(ident_cely=AZ_IDENT)
        self.assertEqual(updated.uzivatelske_oznaceni, "AZ-IMP-01")

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu archeologicky zaznam akce označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání DB.")

        with patch.object(ArcheologickyZaznam, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu archeologicky zaznam akce označí import jako selhaný."""
        from historie.models import Historie

        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení metadat Fedory pro záznam archeologicky zaznam akce označí import jako selhaný."""
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
        """Ověřuje, že selhání uprostřed dávky vrátí vložené záznamy archeologicky zaznam akce zpět."""
        first = self._build_insert_payload("C-202300611A")
        duplicate = self._build_insert_payload("C-202300611A")
        third = self._build_insert_payload("C-202300613A")
        fake_redis = self._build_multi_record_redis([first, duplicate, third])

        self._run_import(fake_redis)

        self.assertFalse(ArcheologickyZaznam.objects.filter(ident_cely__in=["C-202300611A", "C-202300613A"]).exists())
        self._assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu archeologicky zaznam akce nastaví stav zastaveno."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)
        fake_redis.set(f"import_data_stop_{JOB_ID}", "1")

        self._run_import(fake_redis)

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu archeologicky zaznam akce označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_insert_of_duplicate_ident_marks_import_as_failed(self):
        """Ověřuje, že INSERT duplicitního ident pro záznam archeologicky zaznam akce označí import jako selhaný."""
        self._create_existing_az_with_akce()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu archeologicky zaznam akce nastaví stav failed_lock_lost."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis, refresh_lock_side_effect=[True, False, False, False, False])

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self._assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Ověřuje, že úspěšný import záznamu archeologicky zaznam akce zapíše success marker do detailu průběhu."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)

    def test_delete_action_is_noop_for_multiple_class_mapper(self):
        """DELETE pro ``ArcheologickyZaznamAkceMapper`` je no-op.

        ``MultipleClassImportModelMapper.create_records`` vrací pro DELETE prázdný seznam,
        takže žádný záznam se neoznačí ke smazání. Test fixuje toto chování — pokud
        by se v budoucnu DELETE skutečně implementoval, je třeba sem doplnit kontrolu
        smazaných řádků.
        """
        az, akce = self._create_existing_az_with_akce()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        self.assertTrue(
            ArcheologickyZaznam.objects.filter(pk=az.pk).exists(),
            "DELETE akce pro ArcheologickyZaznamAkceMapper je no-op — řádek musí v DB zůstat.",
        )
        self.assertTrue(
            Akce.objects.filter(pk=akce.pk).exists(),
            "DELETE akce pro ArcheologickyZaznamAkceMapper je no-op — Akce musí v DB zůstat.",
        )
