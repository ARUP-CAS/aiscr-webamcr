"""Jednotkové testy pro ``cron.tasks.run_data_import`` — import Adb."""

import json
from unittest.mock import MagicMock, patch

from adb.models import Adb, Kladysm5, VyskovyBod
from core.constants import ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.import_data_mappers import AdbMapper, ImportDataError
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
from historie.models import Historie
from uzivatel.models import Osoba, User

FILE_KEY = "az_adb"
JOB_ID = "test-job-adb"
LOCK_TOKEN = "test-lock-token"

AZ_IDENT = "C-202300002A"
DJ_IDENT = "C-202300002A-D01"
ADB_IDENT = "ADB-ABCD12-000001"
TYP_SONDY_IDENT = "HES-ADBTYP-001"
PODNET_IDENT = "HES-ADBPOD-001"
AUTOR_IDENT = "OS-100001"
SM5_MAPNO = "ADBSM5"


class RunDataImportAdbTest(TestCase):
    """Testy ``run_data_import`` pro ``AdbMapper``."""

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená fixture data pro importní testy."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            heslars = create_heslar_fixtures("adb")
            katastr, pian = create_ruian_with_pian("adb", "P-0001-200001", heslars)
            cls.heslars, cls.katastr, cls.pian = heslars, katastr, pian
            organizace = create_organizace("adb", heslars)
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner-adb@example.cz",
                password="pass",
                is_active=True,
                organizace=organizace,
                ident_cely="U-IMP-ADB-001",
                first_name="Import",
                last_name="Runner",
            )
            cls.az = create_archeologicky_zaznam(AZ_IDENT, katastr, heslars["pristupnost"])
            cls.dj = create_dokumentacni_jednotka(DJ_IDENT, cls.az, pian, heslars["dj_typ"])

            # ADB-specific heslars
            adb_typ_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_ADB_TYP, defaults={"nazev": "adb_typ"})
            cls.typ_sondy, _ = Heslar.objects.get_or_create(
                ident_cely=TYP_SONDY_IDENT,
                defaults={
                    "nazev_heslare": adb_typ_nazev,
                    "heslo": "Sonda",
                    "heslo_en": "Trench",
                    "zkratka": "TS",
                    "razeni": 1,
                },
            )
            podnet_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_ADB_PODNET, defaults={"nazev": "adb_podnet"})
            cls.podnet, _ = Heslar.objects.get_or_create(
                ident_cely=PODNET_IDENT,
                defaults={
                    "nazev_heslare": podnet_nazev,
                    "heslo": "Záchrana",
                    "heslo_en": "Rescue",
                    "zkratka": "ZR",
                    "razeni": 1,
                },
            )

            # Autor (Osoba) — ident regex `OS-\d{6}`
            cls.autor = Osoba.objects.create(
                ident_cely=AUTOR_IDENT,
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
            cls.sm5 = Kladysm5.objects.create(
                gid=99100001, mapname="ADB-SM5-name", mapno=SM5_MAPNO, geom=polygon_5514_wkt
            )

    @staticmethod
    def _build_insert_payload(ident_cely: str = ADB_IDENT) -> dict:
        return {
            "__file_name": FILE_KEY,
            "ident_cely": ident_cely,
            "uzivatelske_oznaceni_sondy": "S-01",
            "trat": "Trať A",
            "cislo_popisne": "12/3",
            "parcelni_cislo": "123/4",
            "stratigraficke_jednotky": "SJ 1, SJ 2",
            "rok_popisu": 2023,
            "rok_revize": 2024,
            "poznamka": "Poznámka",
            "dokumentacni_jednotka": DJ_IDENT,
            "typ_sondy": TYP_SONDY_IDENT,
            "podnet": PODNET_IDENT,
            "autor_popisu": AUTOR_IDENT,
            "autor_revize": AUTOR_IDENT,
            "sm5": SM5_MAPNO,
        }

    def _build_redis(self, performed_action: str) -> FakeRedis:
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
            serialized_record = {"__file_name": FILE_KEY, "ident_cely": ADB_IDENT}
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
        ) as signals_fedora_transaction_mock, patch(
            "cron.tasks.check_import_report_directory",
            return_value=("/tmp/fake-import-dir", "/tmp/fake-import-dir/reports", None),
        ), patch(
            "cron.tasks.save_import_report_to_disk", return_value="/tmp/fake-import-dir/reports/report.xlsx"
        ):
            fedora_transaction_mock.return_value = MagicMock(uid="test-fedora-uid", updated_ident_cely=set())
            fedora_deletion_mock.return_value = MagicMock(uid="test-fedora-deletion-uid", updated_ident_cely=set())
            signals_fedora_transaction_mock.return_value = MagicMock(uid="test-signals-fedora-uid")
            cron_tasks.run_data_import(JOB_ID, self.user.id, LOCK_TOKEN)
        return save_metadata_calls

    def _create_existing_adb(self) -> Adb:
        adb = Adb(
            ident_cely=ADB_IDENT,
            dokumentacni_jednotka=self.dj,
            uzivatelske_oznaceni_sondy="OLD-01",
            trat="Trať O",
            cislo_popisne="1/1",
            parcelni_cislo="1/1",
            stratigraficke_jednotky="SJ 0",
            rok_popisu=2020,
            rok_revize=2021,
            poznamka="Původní",
            typ_sondy=self.typ_sondy,
            podnet=self.podnet,
            autor_popisu=self.autor,
            autor_revize=self.autor,
            sm5=self.sm5,
        )
        adb.suppress_signal = True
        adb.save()
        return adb

    def _assert_import_failed(self, fake_redis: FakeRedis):
        progress_raw = fake_redis.get(f"import_data_progress_{JOB_ID}")
        self.assertIsNotNone(progress_raw)
        self.assertEqual(int(progress_raw.decode("utf-8")), cron_tasks.IMPORT_PROGRESS_PHASE_FAILED)
        self.assertIsNotNone(fake_redis.get(f"import_data_stop_{JOB_ID}"))

    def test_insert_writes_adb_to_database(self):
        """Ověřuje, že INSERT import zapíše záznam ADB do databáze."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self.assertTrue(Adb.objects.filter(ident_cely=ADB_IDENT).exists())

    def test_update_modifies_existing_adb(self):
        """Ověřuje, že UPDATE import upraví existující záznam ADB."""
        self._create_existing_adb()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        updated = Adb.objects.get(ident_cely=ADB_IDENT)
        self.assertEqual(updated.uzivatelske_oznaceni_sondy, "S-01")

    def test_delete_removes_adb_from_database(self):
        """Ověřuje, že DELETE import smaže záznam ADB z databáze."""
        self._create_existing_adb()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        self.assertFalse(Adb.objects.filter(ident_cely=ADB_IDENT).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu ADB označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání DB.")

        with patch.object(Adb, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu ADB označí import jako selhaný."""
        from historie.models import Historie

        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení metadat Fedory pro záznam ADB označí import jako selhaný."""
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
        # Adb.dokumentacni_jednotka je OneToOneField primary_key=True → INSERT s
        # existující DJ Django mlčky převede na UPDATE (žádný IntegrityError). Místo toho
        # druhý záznam odkazuje na neexistující DJ → ``ImportDataMissingReferencedValueError``
        # ve fázi ``map()`` → vnitřní except zavolá ``set_rollback(True)`` a první (uložený)
        # záznam je odvolán spolu se zbytkem dávky.
        """Ověřuje, že selhání uprostřed dávky vrátí vložené záznamy ADB zpět."""
        first = self._build_insert_payload("ADB-ABCD12-000011")
        bad = self._build_insert_payload("ADB-ABCD12-000012")
        bad["dokumentacni_jednotka"] = "C-9999999X-D99"
        fake_redis = self._build_multi_record_redis([first, bad])

        self._run_import(fake_redis)

        self.assertFalse(Adb.objects.filter(ident_cely="ADB-ABCD12-000011").exists())
        self._assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu ADB nastaví stav zastaveno."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)
        fake_redis.set(f"import_data_stop_{JOB_ID}", "1")

        self._run_import(fake_redis)

        status_raw = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu ADB označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    # Pozn.: ``test_insert_of_duplicate_pk_marks_import_as_failed`` nemá pro Adb
    # smysl — PK je ``OneToOneField`` na ``dokumentacni_jednotka``; Django pro INSERT
    # s existujícím PK mlčky provede UPDATE (``import_validation`` v ``run_data_import``
    # se nevolá), takže k IntegrityError nedojde.

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu ADB nastaví stav failed_lock_lost."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis, refresh_lock_side_effect=[True, False, False, False, False])

        status_raw = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self._assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Ověřuje, že úspěšný import záznamu ADB zapíše success marker do detailu průběhu."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        details = fake_redis.lrange(f"import_data_progress_details_tr_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)

    def _create_second_dj(self, az_ident: str = "C-202300003A", dj_ident: str = "C-202300003A-D01"):
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            az = create_archeologicky_zaznam(az_ident, self.katastr, self.heslars["pristupnost"])
            dj = create_dokumentacni_jednotka(dj_ident, az, self.pian, self.heslars["dj_typ"])
        return az, dj

    def _validate_update(self, dj_ident: str, seen_in_batch: set):
        payload = self._build_insert_payload()
        del payload["__file_name"]
        payload["dokumentacni_jednotka"] = dj_ident
        return AdbMapper(payload).import_validation(
            ImportDataAdminForm.PERFORMED_ACTION_UPDATE, self.user.id, seen_in_batch=seen_in_batch
        )

    def test_update_moves_adb_and_height_points_to_another_dj(self):
        """Ověřuje, že UPDATE se změnou DJ přesune ADB i výškové body a zapíše oba AZ do historie a Fedory (F32)."""
        adb = self._create_existing_adb()
        vb_typ_nazev, _ = HeslarNazev.objects.get_or_create(
            id=HESLAR_VYSKOVY_BOD_TYP, defaults={"nazev": "vyskovy_bod_typ"}
        )
        vb_typ = Heslar.objects.create(
            ident_cely="HES-VBTYP-ADB-001", nazev_heslare=vb_typ_nazev, heslo="Bod", heslo_en="Point", zkratka="VB"
        )
        vb = VyskovyBod(
            ident_cely=f"{ADB_IDENT}-V01", adb=adb, typ=vb_typ, geom="SRID=5514;POINT Z(-700000 -1050000 100.0)"
        )
        vb.suppress_signal = True
        vb.save()
        new_az, new_dj = self._create_second_dj()
        payload = self._build_insert_payload()
        payload["dokumentacni_jednotka"] = new_dj.ident_cely
        fake_redis = FakeRedis(
            {
                f"import_data_count_{JOB_ID}": "1",
                f"import_performed_action_{JOB_ID}": ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
                f"import_data_{JOB_ID}_record_0": json.dumps(payload),
            }
        )

        save_metadata_calls = self._run_import(fake_redis)

        progress_raw = fake_redis.get(f"import_data_progress_{JOB_ID}")
        self.assertEqual(int(progress_raw.decode("utf-8")), cron_tasks.IMPORT_PROGRESS_PHASE_FINISHED)
        moved = Adb.objects.get(ident_cely=ADB_IDENT)
        self.assertEqual(moved.dokumentacni_jednotka, new_dj)
        self.assertEqual(moved.uzivatelske_oznaceni_sondy, "S-01")
        self.assertEqual(Adb.objects.count(), 1)
        self.assertEqual(VyskovyBod.objects.get(pk=vb.pk).adb_id, new_dj.pk)
        updated_idents = {getattr(record, "ident_cely", None) for record in save_metadata_calls}
        self.assertTrue({ADB_IDENT, AZ_IDENT, new_az.ident_cely} <= updated_idents, updated_idents)
        for az in (self.az, new_az):
            az.refresh_from_db()
            self.assertTrue(Historie.objects.filter(vazba=az.historie).exists(), az.ident_cely)

    def test_validation_rejects_move_to_dj_that_has_adb(self):
        """Ověřuje, že validace odmítne přesun ADB na DJ, která už ADB má (F32)."""
        self._create_existing_adb()
        _, new_dj = self._create_second_dj()
        existing_target_adb = Adb(
            ident_cely="ADB-ABCD12-000002",
            dokumentacni_jednotka=new_dj,
            rok_popisu=2020,
            autor_popisu=self.autor,
            sm5=self.sm5,
        )
        existing_target_adb.suppress_signal = True
        existing_target_adb.save()

        with self.assertRaises(ImportDataError):
            self._validate_update(new_dj.ident_cely, set())

    def test_validation_allows_one_move_per_target_dj_in_batch(self):
        """Ověřuje, že validace povolí přesun na DJ bez ADB, ale jen jednou v rámci dávky (F32)."""
        self._create_existing_adb()
        _, new_dj = self._create_second_dj()
        seen_in_batch: set = set()

        self.assertEqual(self._validate_update(new_dj.ident_cely, seen_in_batch), {"ident_cely": ADB_IDENT})
        with self.assertRaises(ImportDataError):
            self._validate_update(new_dj.ident_cely, seen_in_batch)

    def test_validation_allows_update_without_dj_change(self):
        """Ověřuje, že UPDATE se stejnou DJ validace propustí i opakovaně v jedné dávce."""
        self._create_existing_adb()
        seen_in_batch: set = set()

        self._validate_update(DJ_IDENT, seen_in_batch)
        self._validate_update(DJ_IDENT, seen_in_batch)
        self.assertEqual(seen_in_batch, set())
