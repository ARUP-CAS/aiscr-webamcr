"""Jednotkové testy pro ``cron.tasks.run_data_import`` — import Lokalita (MultipleClassImportModelMapper).

``LokalitaMapper`` na rozdíl od ``ArcheologickyZaznamAkceMapper`` nemá vlastní
``record_postprocessing``, který by archeologickému záznamu nastavil ``typ_zaznamu = "L"``.
Bez toho narazí AZ na CheckConstraint (``typ_zaznamu in ("L","A")``). Aby test mohl prověřit
celý běh importu, ``record_postprocessing`` se přes patch chová jako u Akce mapperu a
nastaví ``typ_zaznamu = "L"``.
"""

import json
from unittest.mock import MagicMock, patch

from arch_z.models import ArcheologickyZaznam
from core.constants import ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.tests.fake_redis import FakeRedis
from cron import tasks as cron_tasks
from cron.tests._import_test_fixtures import (
    create_heslar_fixtures,
    create_organizace,
    create_ruian_with_pian,
)
from django.contrib.auth.models import Group
from django.test import TestCase
from heslar.hesla import (
    HESLAR_JISTOTA_URCENI,
    HESLAR_LOKALITA_DRUH,
    HESLAR_LOKALITA_TYP,
    HESLAR_STAV_DOCHOVANI,
)
from heslar.models import Heslar, HeslarNazev
from lokalita.models import Lokalita
from uzivatel.models import User

FILE_KEY = "az_lokality"
JOB_ID = "test-job-loc"
LOCK_TOKEN = "test-lock-token"

LOK_IDENT = "C-L00100001"


def _lokalita_record_postprocessing(cls, record, performed_action, fedora_transaction):
    """Patchovaný postprocessing — pro INSERT nastaví AZ typ_zaznamu na 'L'."""
    if isinstance(record, ArcheologickyZaznam) and performed_action == ImportDataAdminForm.PERFORMED_ACTION_INSERT:
        record.typ_zaznamu = ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA
    return record


class RunDataImportLokalitaTest(TestCase):
    """Testy ``run_data_import`` pro ``LokalitaMapper``."""

    @classmethod
    def setUpTestData(cls):
        """Připraví sdílená fixture data pro importní testy."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            heslars = create_heslar_fixtures("loc")
            cls.katastr, _ = create_ruian_with_pian("loc", "P-0002-000001", heslars)
            cls.organizace = create_organizace("loc", heslars)
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner-loc@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-IMP-LOC-001",
                first_name="Import",
                last_name="Runner",
            )
            cls.pristupnost = heslars["pristupnost"]

            typ_lok_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_LOKALITA_TYP, defaults={"nazev": "lokalita_typ"}
            )
            cls.typ_lokality = Heslar.objects.create(
                ident_cely="HES-LOKTYP-001",
                nazev_heslare=typ_lok_nazev,
                heslo="Sídliště",
                heslo_en="Settlement",
                zkratka="SD",
                razeni=1,
            )
            druh_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_LOKALITA_DRUH, defaults={"nazev": "lokalita_druh"}
            )
            cls.druh = Heslar.objects.create(
                ident_cely="HES-LOKDRH-001",
                nazev_heslare=druh_nazev,
                heslo="Archeologická lokalita",
                heslo_en="Archaeological site",
                zkratka="AL",
                razeni=1,
            )
            zachovalost_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_STAV_DOCHOVANI, defaults={"nazev": "stav_dochovani"}
            )
            cls.zachovalost = Heslar.objects.create(
                ident_cely="HES-ZACH-001",
                nazev_heslare=zachovalost_nazev,
                heslo="Dobrá",
                heslo_en="Good",
                zkratka="DB",
                razeni=1,
            )
            jistota_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_JISTOTA_URCENI, defaults={"nazev": "jistota_urceni"}
            )
            cls.jistota = Heslar.objects.create(
                ident_cely="HES-JIST-001",
                nazev_heslare=jistota_nazev,
                heslo="Jistá",
                heslo_en="Certain",
                zkratka="J",
                razeni=1,
            )

    def _build_insert_payload(self, ident_cely: str = LOK_IDENT) -> dict:
        return {
            "__file_name": FILE_KEY,
            "ident_cely": ident_cely,
            "igsn": None,
            "stav": 1,
            "pristupnost": self.pristupnost.ident_cely,
            "hlavni_katastr": f"ruian-{self.katastr.kod}",
            "nazev": "Importovaná lokalita",
            "uzivatelske_oznaceni": "LOK-IMP-01",
            "typ_lokality": self.typ_lokality.ident_cely,
            "druh": self.druh.ident_cely,
            "zachovalost": self.zachovalost.ident_cely,
            "jistota": self.jistota.ident_cely,
            "popis": "Popis",
            "poznamka": "Poznámka",
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
            "core.import_data_mappers.LokalitaMapper.record_postprocessing",
            classmethod(_lokalita_record_postprocessing),
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

    def _create_existing_lokalita(self):
        az = ArcheologickyZaznam(
            ident_cely=LOK_IDENT,
            typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA,
            pristupnost=self.pristupnost,
            stav=1,
            hlavni_katastr=self.katastr,
        )
        az.suppress_signal = True
        az.save()
        lok = Lokalita(
            archeologicky_zaznam=az,
            druh=self.druh,
            nazev="Původní",
            typ_lokality=self.typ_lokality,
        )
        lok.save()
        return az, lok

    def _assert_import_failed(self, fake_redis: FakeRedis):
        progress_raw = fake_redis.get(f"import_data_progress_{JOB_ID}")
        self.assertIsNotNone(progress_raw)
        self.assertEqual(int(progress_raw.decode("utf-8")), cron_tasks.IMPORT_PROGRESS_PHASE_FAILED)
        self.assertIsNotNone(fake_redis.get(f"import_data_stop_{JOB_ID}"))

    def test_insert_writes_az_and_lokalita_to_database(self):
        """Ověřuje, že INSERT import zapíše záznam az and lokalita do databáze."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self.assertTrue(ArcheologickyZaznam.objects.filter(ident_cely=LOK_IDENT).exists())
        az = ArcheologickyZaznam.objects.get(ident_cely=LOK_IDENT)
        self.assertEqual(az.typ_zaznamu, ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA)
        self.assertTrue(Lokalita.objects.filter(archeologicky_zaznam=az).exists())

    def test_update_modifies_existing_lokalita(self):
        """Ověřuje, že UPDATE import upraví existující záznam lokalita."""
        self._create_existing_lokalita()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        updated = Lokalita.objects.get(archeologicky_zaznam__ident_cely=LOK_IDENT)
        self.assertEqual(updated.nazev, "Importovaná lokalita")

    def test_database_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání databázového uložení záznamu lokalita označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání DB.")

        with patch.object(ArcheologickyZaznam, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení historie záznamu lokalita označí import jako selhaný."""
        from historie.models import Historie

        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Selhání Historie.")

        with patch.object(Historie, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Ověřuje, že selhání uložení metadat Fedory pro záznam lokalita označí import jako selhaný."""
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
        """Ověřuje, že selhání uprostřed dávky vrátí vložené záznamy lokalita zpět."""
        first = self._build_insert_payload("C-L00100011")
        duplicate = self._build_insert_payload("C-L00100011")
        third = self._build_insert_payload("C-L00100013")
        fake_redis = self._build_multi_record_redis([first, duplicate, third])

        self._run_import(fake_redis)

        self.assertFalse(ArcheologickyZaznam.objects.filter(ident_cely__in=["C-L00100011", "C-L00100013"]).exists())
        self._assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Ověřuje, že uživatelské zastavení importu záznamu lokalita nastaví stav zastaveno."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)
        fake_redis.set(f"import_data_stop_{JOB_ID}", "1")

        self._run_import(fake_redis)

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """Ověřuje, že UPDATE neexistujícího záznamu lokalita označí import jako selhaný."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_insert_of_duplicate_ident_marks_import_as_failed(self):
        """Ověřuje, že INSERT duplicitního ident pro záznam lokalita označí import jako selhaný."""
        self._create_existing_lokalita()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Ověřuje, že ztráta importního locku při importu záznamu lokalita nastaví stav failed_lock_lost."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis, refresh_lock_side_effect=[True, False, False, False, False])

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self._assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Ověřuje, že úspěšný import záznamu lokalita zapíše success marker do detailu průběhu."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.success", decoded)

    def test_delete_action_is_noop_for_multiple_class_mapper(self):
        """DELETE pro ``LokalitaMapper`` je no-op.

        ``MultipleClassImportModelMapper.create_records`` vrací pro DELETE prázdný seznam,
        takže žádný záznam se neoznačí ke smazání. Test fixuje toto chování — pokud
        by se v budoucnu DELETE skutečně implementoval, je třeba sem doplnit kontrolu
        smazaných řádků.
        """
        az, lok = self._create_existing_lokalita()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        self.assertTrue(
            ArcheologickyZaznam.objects.filter(pk=az.pk).exists(),
            "DELETE akce pro LokalitaMapper je no-op — řádek musí v DB zůstat.",
        )
        self.assertTrue(
            Lokalita.objects.filter(pk=lok.pk).exists(),
            "DELETE akce pro LokalitaMapper je no-op — Lokalita musí v DB zůstat.",
        )
