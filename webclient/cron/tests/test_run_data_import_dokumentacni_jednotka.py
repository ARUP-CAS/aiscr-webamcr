"""Jednotkové testy pro ``cron.tasks.run_data_import`` — import DokumentacniJednotka.

Vyžaduje rozsáhlejší fixture: ``RuianKraj`` → ``RuianOkres`` → ``RuianKatastr`` →
``Pian`` (linkovaný do katastru, aby ``DokumentacniJednotkaMapper.record_postprocessing``
nezvolala ``vytvor_pian``) → ``ArcheologickyZaznam``.
"""

import json
from unittest.mock import MagicMock, patch

from arch_z.models import ArcheologickyZaznam
from core.constants import AZ_STAV_ZAPSANY, ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.tests.fake_redis import FakeRedis
from cron import tasks as cron_tasks
from dj.models import DokumentacniJednotka
from django.contrib.auth.models import Group
from django.test import TestCase
from heslar.hesla import (
    HESLAR_DJ_TYP,
    HESLAR_LICENCE,
    HESLAR_ORGANIZACE_TYP,
    HESLAR_PIAN_PRESNOST,
    HESLAR_PIAN_TYP,
    HESLAR_PRISTUPNOST,
)
from heslar.models import Heslar, HeslarNazev, RuianKatastr, RuianKraj, RuianOkres
from pian.models import Kladyzm, Pian
from uzivatel.models import Organizace, User

FILE_KEY = "az_dokumentacni_jednotky"
JOB_ID = "test-job-dj"
LOCK_TOKEN = "test-lock-token"

AZ_IDENT = "C-202300001A"
DJ_IDENT = "C-202300001A-D01"
DJ_TYP_IDENT = "HES-DJTYP-NK01"  # ne-katastrový typ, aby DJ post_save signál neřešil pian


class RunDataImportDokumentacniJednotkaTest(TestCase):
    """Testy ``run_data_import`` pro ``DokumentacniJednotkaMapper``."""

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená fixture data pro importní testy."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            # Heslar lookups
            pristupnost_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_PRISTUPNOST, defaults={"nazev": "pristupnost"}
            )
            cls.pristupnost, _ = Heslar.objects.get_or_create(
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
            typ_org_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_ORGANIZACE_TYP, defaults={"nazev": "typ_organizace"}
            )
            typ_org, _ = Heslar.objects.get_or_create(
                nazev_heslare=typ_org_nazev,
                zkratka="T",
                defaults={"ident_cely": "HES-IMP-TYPORG-001", "heslo": "T", "heslo_en": "T"},
            )
            dj_typ_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_DJ_TYP, defaults={"nazev": "dj_typ"})
            cls.dj_typ, _ = Heslar.objects.get_or_create(
                ident_cely=DJ_TYP_IDENT,
                defaults={
                    "nazev_heslare": dj_typ_nazev,
                    "heslo": "Sonda",
                    "heslo_en": "Trench",
                    "zkratka": "S",
                    "razeni": 99,
                },
            )

            # Organizace / user (pro běžce importu)
            cls.organizace, _ = Organizace.objects.get_or_create(
                ident_cely="ORG-IMP-DJ-001",
                defaults={
                    "nazev": "Org DJ",
                    "nazev_zkraceny": "ORGDJ",
                    "typ_organizace": typ_org,
                    "zverejneni_pristupnost": cls.pristupnost,
                    "licence": licence,
                },
            )
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner-dj@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-IMP-DJ-001",
                first_name="Import",
                last_name="Runner",
            )

            # RUIAN hierarchie
            point_wkt = "SRID=4326;POINT(14.5 50.0)"
            multipoly_wkt = "SRID=4326;MULTIPOLYGON(((14.4 49.9, 14.6 49.9, 14.6 50.1, 14.4 50.1, 14.4 49.9)))"
            kraj = RuianKraj(
                nazev="DJ-Test-Kraj",
                kod=991,
                rada_id="X",
                nazev_en="DJ-Test-Kraj-EN",
                definicni_bod=point_wkt,
                hranice=multipoly_wkt,
            )
            kraj.suppress_signal = True
            kraj.save()
            okres = RuianOkres(
                nazev="DJ-Test-Okres",
                kraj=kraj,
                spz="DJX",
                kod=99100,
                nazev_en="DJ-Test-Okres-EN",
                definicni_bod=point_wkt,
                hranice=multipoly_wkt,
            )
            okres.suppress_signal = True
            okres.save()
            cls.katastr = RuianKatastr(
                nazev="DJ-Test-Katastr",
                kod=991001,
                okres=okres,
                definicni_bod=point_wkt,
                hranice=multipoly_wkt,
            )
            cls.katastr.suppress_signal = True
            cls.katastr.save()

            # Pian + napojení na katastr (aby DJ.record_postprocessing nešel přes vytvor_pian)
            pian_typ_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_PIAN_TYP, defaults={"nazev": "pian_typ"})
            pian_typ, _ = Heslar.objects.get_or_create(
                ident_cely="HES-PIANTYP-DJ-001",
                defaults={
                    "nazev_heslare": pian_typ_nazev,
                    "heslo": "Bod",
                    "heslo_en": "Point",
                    "zkratka": "B",
                    "razeni": 1,
                },
            )
            presnost_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_PIAN_PRESNOST, defaults={"nazev": "pian_presnost"}
            )
            presnost, _ = Heslar.objects.get_or_create(
                ident_cely="HES-PIANPR-DJ-001",
                defaults={
                    "nazev_heslare": presnost_nazev,
                    "heslo": "Přesný",
                    "heslo_en": "Accurate",
                    "zkratka": "1",
                    "razeni": 1,
                },
            )
            polygon_5514_wkt = (
                "SRID=5514;POLYGON((-700000 -1000000, -700000 -1100000, -800000 -1100000,"
                " -800000 -1000000, -700000 -1000000))"
            )
            zm10 = Kladyzm.objects.create(cislo="DJZM10", kategorie=10, the_geom=polygon_5514_wkt)
            zm50 = Kladyzm.objects.create(cislo="DJZM50", kategorie=50, the_geom=polygon_5514_wkt)
            pian = Pian(
                ident_cely="P-0001-100001",
                stav=1,
                geom_system="5514",
                geom="SRID=4326;POINT(14.5 50.0)",
                geom_sjtsk="SRID=5514;POINT(-700000 -1050000)",
                typ=pian_typ,
                presnost=presnost,
                zm10=zm10,
                zm50=zm50,
            )
            pian.suppress_signal = True
            pian.save()
            cls.katastr.pian = pian
            cls.katastr.suppress_signal = True
            cls.katastr.save()
            cls.pian = pian

            # ArcheologickyZaznam (typ Akce) — naváže na katastr
            az = ArcheologickyZaznam(
                ident_cely=AZ_IDENT,
                typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_AKCE,
                pristupnost=cls.pristupnost,
                stav=AZ_STAV_ZAPSANY,
                hlavni_katastr=cls.katastr,
            )
            az.suppress_signal = True
            az.save()
            cls.az = az

    @staticmethod
    def _build_insert_payload(ident_cely: str = DJ_IDENT) -> dict:
        return {
            "__file_name": FILE_KEY,
            "ident_cely": ident_cely,
            "negativni_jednotka": False,
            "nazev": "Importovaná DJ",
            "archeologicky_zaznam": AZ_IDENT,
            "pian": "P-0001-100001",
            "typ": DJ_TYP_IDENT,
        }

    def _build_redis(self, performed_action: str) -> FakeRedis:
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
            serialized_record = {"__file_name": FILE_KEY, "ident_cely": DJ_IDENT}
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
        ) as fedora_deletion_mock:
            fedora_transaction_mock.return_value = MagicMock(uid="test-fedora-uid", updated_ident_cely=set())
            fedora_deletion_mock.return_value = MagicMock(uid="test-fedora-deletion-uid", updated_ident_cely=set())
            cron_tasks.run_data_import(JOB_ID, self.user.id, LOCK_TOKEN)
        return save_metadata_calls

    def _create_existing_dj(self) -> DokumentacniJednotka:
        dj = DokumentacniJednotka(
            ident_cely=DJ_IDENT,
            negativni_jednotka=False,
            nazev="Původní DJ",
            archeologicky_zaznam=self.az,
            pian=self.pian,
            typ=self.dj_typ,
        )
        dj.suppress_signal = True
        dj.save()
        return dj

    def _assert_import_failed(self, fake_redis: FakeRedis):
        progress_raw = fake_redis.get(f"import_data_progress_{JOB_ID}")
        self.assertIsNotNone(progress_raw)
        self.assertEqual(int(progress_raw.decode("utf-8")), cron_tasks.IMPORT_PROGRESS_PHASE_FAILED)
        self.assertIsNotNone(fake_redis.get(f"import_data_stop_{JOB_ID}"))

    def test_insert_writes_dj_to_database(self):
        """Ověřuje, že INSERT import zapíše záznam dokumentacni jednotka do databáze."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self.assertTrue(DokumentacniJednotka.objects.filter(ident_cely=DJ_IDENT).exists())

    def test_update_modifies_existing_dj(self):
        """Ověřuje, že UPDATE import upraví existující záznam dokumentacni jednotka."""
        self._create_existing_dj()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        updated = DokumentacniJednotka.objects.get(ident_cely=DJ_IDENT)
        self.assertEqual(updated.nazev, "Importovaná DJ")

    def test_delete_removes_dj_from_database(self):
        """Ověřuje, že DELETE import smaže záznam dokumentacni jednotka z databáze."""
        self._create_existing_dj()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        self.assertFalse(DokumentacniJednotka.objects.filter(ident_cely=DJ_IDENT).exists())

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu dokumentacni jednotka označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání DB.")

        with patch.object(DokumentacniJednotka, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu dokumentacni jednotka označí import jako selhaný."""
        from historie.models import Historie

        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání Historie.")

        # DokumentacniJednotkaMapper.get_record_history vrací AZ → loop běží přirozeně.
        with patch.object(Historie, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení metadat Fedory pro záznam dokumentacni jednotka označí import jako selhaný."""
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
        """Ověřuje, že selhání uprostřed dávky vrátí vložené záznamy dokumentacni jednotka zpět."""
        first = self._build_insert_payload("C-202300001A-D11")
        duplicate = self._build_insert_payload("C-202300001A-D11")
        third = self._build_insert_payload("C-202300001A-D13")
        fake_redis = self._build_multi_record_redis([first, duplicate, third])

        self._run_import(fake_redis)

        self.assertFalse(
            DokumentacniJednotka.objects.filter(ident_cely__in=["C-202300001A-D11", "C-202300001A-D13"]).exists()
        )
        self._assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu dokumentacni jednotka nastaví stav zastaveno."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)
        fake_redis.set(f"import_data_stop_{JOB_ID}", "1")

        self._run_import(fake_redis)

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu dokumentacni jednotka označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_insert_of_duplicate_ident_marks_import_as_failed(self):
        """Ověřuje, že INSERT duplicitního ident pro záznam dokumentacni jednotka označí import jako selhaný."""
        self._create_existing_dj()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu dokumentacni jednotka nastaví stav failed_lock_lost."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis, refresh_lock_side_effect=[True, False, False, False, False])

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self._assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Ověřuje, že úspěšný import záznamu dokumentacni jednotka zapíše success marker do detailu průběhu."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)
