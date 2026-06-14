"""Jednotkové testy pro ``cron.tasks.run_data_import`` — import VyskovyBod (ADB výškové body)."""

import json
from unittest.mock import MagicMock, patch

from adb.models import Adb, Kladysm5, VyskovyBod
from core.constants import ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.tests.fake_redis import FakeRedis
from cron import tasks as cron_tasks
from cron.tests._import_test_fixtures import (
    create_archeologicky_zaznam,
    create_dokumentacni_jednotka,
    create_heslar_fixtures,
    create_organizace,
    create_ruian_with_pian,
)
from django.contrib.auth.models import Group
from django.test import TestCase
from heslar.hesla import HESLAR_ADB_PODNET, HESLAR_ADB_TYP, HESLAR_VYSKOVY_BOD_TYP
from heslar.models import Heslar, HeslarNazev
from uzivatel.models import Osoba, User

FILE_KEY = "az_adb_vyskove_body"
JOB_ID = "test-job-vb"
LOCK_TOKEN = "test-lock-token"

AZ_IDENT = "C-202300003A"
DJ_IDENT = "C-202300003A-D01"
ADB_IDENT = "ADB-EFGH34-000001"
VB_IDENT = "ADB-EFGH34-000001-V0001"
VB_TYP_IDENT = "HES-VBTYP-001"


class RunDataImportVyskovyBodTest(TestCase):
    """Testy ``run_data_import`` pro ``AdbVyskovyBod`` mapper."""

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená fixture data pro importní testy."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            heslars = create_heslar_fixtures("vb")
            katastr, pian = create_ruian_with_pian("vb", "P-0001-300001", heslars)
            organizace = create_organizace("vb", heslars)
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner-vb@example.cz",
                password="pass",
                is_active=True,
                organizace=organizace,
                ident_cely="U-IMP-VB-001",
                first_name="Import",
                last_name="Runner",
            )
            az = create_archeologicky_zaznam(AZ_IDENT, katastr, heslars["pristupnost"])
            dj = create_dokumentacni_jednotka(DJ_IDENT, az, pian, heslars["dj_typ"])

            adb_typ_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_ADB_TYP, defaults={"nazev": "adb_typ"})
            typ_sondy, _ = Heslar.objects.get_or_create(
                ident_cely="HES-ADBTYP-VB-001",
                defaults={
                    "nazev_heslare": adb_typ_nazev,
                    "heslo": "Sonda",
                    "heslo_en": "Trench",
                    "zkratka": "TS",
                    "razeni": 1,
                },
            )
            podnet_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_ADB_PODNET, defaults={"nazev": "adb_podnet"})
            podnet, _ = Heslar.objects.get_or_create(
                ident_cely="HES-ADBPOD-VB-001",
                defaults={
                    "nazev_heslare": podnet_nazev,
                    "heslo": "Záchrana",
                    "heslo_en": "Rescue",
                    "zkratka": "ZR",
                    "razeni": 1,
                },
            )
            autor = Osoba.objects.create(
                ident_cely="OS-200001",
                jmeno="Petr",
                prijmeni="Autor",
                vypis="Autor P.",
                vypis_cely="Autor, Petr",
                rok_narozeni=1970,
            )
            polygon_5514_wkt = (
                "SRID=5514;POLYGON((-700000 -1000000, -700000 -1100000, -800000 -1100000,"
                " -800000 -1000000, -700000 -1000000))"
            )
            sm5 = Kladysm5.objects.create(gid=99200001, mapname="VB-SM5-name", mapno="VBSM5", geom=polygon_5514_wkt)
            cls.adb = Adb(
                ident_cely=ADB_IDENT,
                dokumentacni_jednotka=dj,
                uzivatelske_oznaceni_sondy="VB-S-01",
                trat="Trať VB",
                cislo_popisne="1",
                parcelni_cislo="1",
                stratigraficke_jednotky="SJ",
                rok_popisu=2023,
                rok_revize=None,
                poznamka="",
                typ_sondy=typ_sondy,
                podnet=podnet,
                autor_popisu=autor,
                autor_revize=None,
                sm5=sm5,
            )
            cls.adb.suppress_signal = True
            cls.adb.save()

            vb_typ_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_VYSKOVY_BOD_TYP, defaults={"nazev": "vyskovy_bod_typ"}
            )
            cls.vb_typ, _ = Heslar.objects.get_or_create(
                ident_cely=VB_TYP_IDENT,
                defaults={
                    "nazev_heslare": vb_typ_nazev,
                    "heslo": "Bod",
                    "heslo_en": "Point",
                    "zkratka": "VB",
                    "razeni": 1,
                },
            )

    @staticmethod
    def _build_insert_payload(ident_cely: str = VB_IDENT) -> dict:
        return {
            "__file_name": FILE_KEY,
            "ident_cely": ident_cely,
            "geom": "SRID=5514;POINT Z(-700000 -1050000 250.5)",
            "adb": ADB_IDENT,
            "typ": VB_TYP_IDENT,
        }

    def _build_redis(self, performed_action: str) -> FakeRedis:
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
            serialized_record = {"__file_name": FILE_KEY, "ident_cely": VB_IDENT}
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

    def _create_existing_vb(self) -> VyskovyBod:
        vb = VyskovyBod(
            ident_cely=VB_IDENT,
            adb=self.adb,
            typ=self.vb_typ,
            geom="SRID=5514;POINT Z(-700000 -1050000 100.0)",
        )
        vb.suppress_signal = True
        vb.save()
        return vb

    def _assert_import_failed(self, fake_redis: FakeRedis):
        progress_raw = fake_redis.get(f"import_data_progress_{JOB_ID}")
        self.assertIsNotNone(progress_raw)
        self.assertEqual(int(progress_raw.decode("utf-8")), cron_tasks.IMPORT_PROGRESS_PHASE_FAILED)
        self.assertIsNotNone(fake_redis.get(f"import_data_stop_{JOB_ID}"))

    def test_insert_writes_vb_to_database(self):
        """Ověřuje, že INSERT import zapíše záznam vyskovy bod do databáze."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self.assertTrue(VyskovyBod.objects.filter(ident_cely=VB_IDENT).exists())

    def test_update_modifies_existing_vb(self):
        """Ověřuje, že UPDATE import upraví existující záznam vyskovy bod."""
        self._create_existing_vb()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        updated = VyskovyBod.objects.get(ident_cely=VB_IDENT)
        self.assertAlmostEqual(updated.geom.z, 250.5, places=2)

    def test_delete_removes_vb_from_database(self):
        """Ověřuje, že DELETE import smaže záznam vyskovy bod z databáze."""
        self._create_existing_vb()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        self.assertFalse(VyskovyBod.objects.filter(ident_cely=VB_IDENT).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu adb vyskovy bod označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání DB.")

        with patch.object(VyskovyBod, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu adb vyskovy bod označí import jako selhaný."""
        from historie.models import Historie

        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení metadat Fedory pro záznam adb vyskovy bod označí import jako selhaný."""
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
        """Ověřuje, že selhání uprostřed dávky vrátí vložené záznamy adb vyskovy bod zpět."""
        first = self._build_insert_payload("ADB-EFGH34-000001-V0011")
        duplicate = self._build_insert_payload("ADB-EFGH34-000001-V0011")
        third = self._build_insert_payload("ADB-EFGH34-000001-V0013")
        fake_redis = self._build_multi_record_redis([first, duplicate, third])

        self._run_import(fake_redis)

        self.assertFalse(
            VyskovyBod.objects.filter(ident_cely__in=["ADB-EFGH34-000001-V0011", "ADB-EFGH34-000001-V0013"]).exists()
        )
        self._assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu adb vyskovy bod nastaví stav zastaveno."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)
        fake_redis.set(f"import_data_stop_{JOB_ID}", "1")

        self._run_import(fake_redis)

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu adb vyskovy bod označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_insert_of_duplicate_ident_marks_import_as_failed(self):
        """Ověřuje, že INSERT duplicitního ident pro záznam adb vyskovy bod označí import jako selhaný."""
        self._create_existing_vb()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu adb vyskovy bod nastaví stav failed_lock_lost."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis, refresh_lock_side_effect=[True, False, False, False, False])

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self._assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Ověřuje, že úspěšný import záznamu adb vyskovy bod zapíše success marker do detailu průběhu."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
