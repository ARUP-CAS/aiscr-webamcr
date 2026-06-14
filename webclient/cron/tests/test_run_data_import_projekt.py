"""Jednotkové testy pro ``cron.tasks.run_data_import`` — import jednoho záznamu Projekt."""

import json
from unittest.mock import MagicMock, patch

from core.constants import ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.tests.fake_redis import FakeRedis
from cron import tasks as cron_tasks
from cron.tests._import_test_fixtures import (
    create_heslar_fixtures,
    create_organizace,
    create_projekt_typ,
    create_ruian_with_pian,
)
from django.contrib.auth.models import Group
from django.test import TestCase
from heslar.hesla import HESLAR_PAMATKOVA_OCHRANA
from heslar.models import Heslar, HeslarNazev
from projekt.models import Projekt
from uzivatel.models import Osoba, User

FILE_KEY = "projekty"
JOB_ID = "test-job-projekt"
LOCK_TOKEN = "test-lock-token"

PROJEKT_IDENT = "C-202300101"
PAMATKA_IDENT = "HES-PAMOCH-001"
VEDOUCI_IDENT = "OS-300001"


class RunDataImportProjektTest(TestCase):
    """Testy ``run_data_import`` pro ``ProjektMapper``."""

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená fixture data pro importní testy."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            heslars = create_heslar_fixtures("proj")
            katastr, _pian = create_ruian_with_pian("proj", "P-0001-400001", heslars)
            cls.organizace = create_organizace("proj", heslars)
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner-proj@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-IMP-PROJ-001",
                first_name="Import",
                last_name="Runner",
            )
            cls.katastr = katastr
            cls.typ_projektu = create_projekt_typ("proj")
            cls.vedouci = Osoba.objects.create(
                ident_cely=VEDOUCI_IDENT,
                jmeno="Petr",
                prijmeni="Vedouci",
                vypis="Vedouci P.",
                vypis_cely="Vedouci, Petr",
                rok_narozeni=1980,
            )
            pamatka_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_PAMATKOVA_OCHRANA, defaults={"nazev": "pamatkova_ochrana"}
            )
            cls.pamatka = Heslar.objects.create(
                ident_cely=PAMATKA_IDENT,
                nazev_heslare=pamatka_nazev,
                heslo="Národní kulturní památka",
                heslo_en="National monument",
                zkratka="NKP",
                razeni=1,
            )

    @classmethod
    def _build_insert_payload(cls, ident_cely: str = PROJEKT_IDENT) -> dict:
        return {
            "__file_name": FILE_KEY,
            "ident_cely": ident_cely,
            "stav": 1,
            "lokalizace": "U lesa",
            "parcelni_cislo": "12/3",
            "geom": None,
            "geom_system": "5514",
            "geom_sjtsk": None,
            "podnet": "Výstavba",
            "planovane_zahajeni": None,
            "uzivatelske_oznaceni": "PROJ-IMP-01",
            "oznaceni_stavby": "Stavba A",
            "kulturni_pamatka_cislo": "12345",
            "kulturni_pamatka_popis": "Popis památky",
            "datum_zahajeni": None,
            "datum_ukonceni": None,
            "termin_odevzdani_nz": None,
            "typ_projektu": "HES-PROJTYP-proj",
            "hlavni_katastr": f"ruian-{cls._get_katastr_kod()}",
            "vedouci_projektu": VEDOUCI_IDENT,
            "organizace": "ORG-IMP-proj-001",
            "kulturni_pamatka": PAMATKA_IDENT,
        }

    @classmethod
    def _get_katastr_kod(cls):
        from heslar.models import RuianKatastr

        return RuianKatastr.objects.get(nazev="Katastr-proj").kod

    def _build_redis(self, performed_action: str) -> FakeRedis:
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
            serialized_record = {"__file_name": FILE_KEY, "ident_cely": PROJEKT_IDENT}
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
        ) as fedora_deletion_mock, patch(
            "uzivatel.signals.FedoraTransaction"
        ) as signals_fedora_transaction_mock:
            fedora_transaction_mock.return_value = MagicMock(uid="test-fedora-uid", updated_ident_cely=set())
            fedora_deletion_mock.return_value = MagicMock(uid="test-fedora-deletion-uid", updated_ident_cely=set())
            signals_fedora_transaction_mock.return_value = MagicMock(uid="test-signals-fedora-uid")
            cron_tasks.run_data_import(JOB_ID, self.user.id, LOCK_TOKEN)
        return save_metadata_calls

    def _create_existing_projekt(self) -> Projekt:
        with patch("projekt.models.Projekt.set_pristupnost", return_value=None):
            projekt = Projekt(
                ident_cely=PROJEKT_IDENT,
                stav=1,
                typ_projektu=self.typ_projektu,
                hlavni_katastr=self.katastr,
                lokalizace="Původní",
            )
            projekt.suppress_signal = True
            projekt.save()
        return projekt

    def _assert_import_failed(self, fake_redis: FakeRedis):
        progress_raw = fake_redis.get(f"import_data_progress_{JOB_ID}")
        self.assertIsNotNone(progress_raw)
        self.assertEqual(int(progress_raw.decode("utf-8")), cron_tasks.IMPORT_PROGRESS_PHASE_FAILED)
        self.assertIsNotNone(fake_redis.get(f"import_data_stop_{JOB_ID}"))

    def test_insert_writes_projekt_to_database(self):
        """Ověřuje, že INSERT import zapíše záznam projekt do databáze."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self.assertTrue(Projekt.objects.filter(ident_cely=PROJEKT_IDENT).exists())
        created = Projekt.objects.get(ident_cely=PROJEKT_IDENT)
        self.assertEqual(created.lokalizace, "U lesa")
        self.assertEqual(created.typ_projektu_id, self.typ_projektu.pk)

    def test_update_modifies_existing_projekt(self):
        """Ověřuje, že UPDATE import upraví existující záznam projekt."""
        self._create_existing_projekt()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        updated = Projekt.objects.get(ident_cely=PROJEKT_IDENT)
        self.assertEqual(updated.lokalizace, "U lesa")

    def test_delete_removes_projekt_from_database(self):
        """Ověřuje, že DELETE import smaže záznam projekt z databáze."""
        self._create_existing_projekt()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        self.assertFalse(Projekt.objects.filter(ident_cely=PROJEKT_IDENT).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu projekt označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání DB.")

        with patch.object(Projekt, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu projekt označí import jako selhaný."""
        from historie.models import Historie

        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení metadat Fedory pro záznam projekt označí import jako selhaný."""
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
        """Ověřuje, že selhání uprostřed dávky vrátí vložené záznamy projekt zpět."""
        first = self._build_insert_payload("C-202300111")
        duplicate = self._build_insert_payload("C-202300111")
        third = self._build_insert_payload("C-202300113")
        fake_redis = self._build_multi_record_redis([first, duplicate, third])

        self._run_import(fake_redis)

        self.assertFalse(Projekt.objects.filter(ident_cely__in=["C-202300111", "C-202300113"]).exists())
        self._assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu projekt nastaví stav zastaveno."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)
        fake_redis.set(f"import_data_stop_{JOB_ID}", "1")

        self._run_import(fake_redis)

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu projekt označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_insert_of_duplicate_ident_marks_import_as_failed(self):
        """Ověřuje, že INSERT duplicitního ident pro záznam projekt označí import jako selhaný."""
        self._create_existing_projekt()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu projekt nastaví stav failed_lock_lost."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis, refresh_lock_side_effect=[True, False, False, False, False])

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self._assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Ověřuje, že úspěšný import záznamu projekt zapíše success marker do detailu průběhu."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
