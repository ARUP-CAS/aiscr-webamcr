"""Jednotkové testy pro ``cron.tasks.run_data_import`` — import jednoho záznamu Organizace."""

import json
from unittest.mock import MagicMock, patch

from core.constants import ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.tests.fake_redis import FakeRedis
from cron import tasks as cron_tasks
from django.contrib.auth.models import Group
from django.test import TestCase
from heslar.hesla import HESLAR_LICENCE, HESLAR_ORGANIZACE_TYP, HESLAR_PRISTUPNOST
from heslar.models import Heslar, HeslarNazev
from uzivatel.models import Organizace, User

ORGANIZACE_FILE_KEY = "organizace"
JOB_ID = "test-job-organizace"
LOCK_TOKEN = "test-lock-token"

ORG_IDENT = "ORG-999001"
ORG_NAZEV_ZKRACENY = "ORGIMPTEST"
TYP_ORG_IDENT = "HES-IMP-TYPORG-001"
PRISTUPNOST_IDENT = "HES-IMP-PRST-001"
LICENCE_IDENT = "HES-IMP-LIC-001"


class RunDataImportOrganizaceTest(TestCase):
    """Testy ``run_data_import`` pro mapper ``OrganizaceMapper`` s mocknutým Redis i Fedora repozitářem."""

    @classmethod
    def setUpTestData(cls):
        """Připraví minimální fixtures — heslářové entity, organizaci uživatele a uživatele běžícího import."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            typ_org_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_ORGANIZACE_TYP, defaults={"nazev": "typ_organizace"}
            )
            cls.typ_org, _ = Heslar.objects.get_or_create(
                nazev_heslare=typ_org_nazev,
                zkratka="T",
                defaults={"ident_cely": TYP_ORG_IDENT, "heslo": "Test", "heslo_en": "Test"},
            )
            pristupnost_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_PRISTUPNOST, defaults={"nazev": "pristupnost"}
            )
            cls.pristupnost, _ = Heslar.objects.get_or_create(
                nazev_heslare=pristupnost_nazev,
                zkratka="A",
                defaults={"ident_cely": PRISTUPNOST_IDENT, "heslo": "Veřejný", "heslo_en": "Public"},
            )
            licence_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_LICENCE, defaults={"nazev": "licence"})
            cls.licence, _ = Heslar.objects.get_or_create(
                nazev_heslare=licence_nazev,
                zkratka="L",
                defaults={"ident_cely": LICENCE_IDENT, "heslo": "Lic", "heslo_en": "Lic"},
            )

            cls.user_organizace, _ = Organizace.objects.get_or_create(
                ident_cely="ORG-IMP-RUNNER-001",
                defaults={
                    "nazev": "Org pro běžce importu",
                    "nazev_zkraceny": "ORGRUNNER",
                    "typ_organizace": cls.typ_org,
                    "zverejneni_pristupnost": cls.pristupnost,
                    "licence": cls.licence,
                },
            )
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner-org@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.user_organizace,
                ident_cely="U-IMP-ORG-001",
                first_name="Import",
                last_name="Runner",
            )

    def _build_redis(self, performed_action: str) -> FakeRedis:
        """Sestaví ``FakeRedis`` s jedním serializovaným ``Organizace`` záznamem připraveným pro import.

        DELETE smí obsahovat pouze sloupec primárního klíče — jinak ``_check_column_structure``
        vyhodnotí ostatní sloupce jako ``excess`` a vyhodí ``ImportDataIncorrectStructureError``.
        """
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
            serialized_record = {
                "__file_name": ORGANIZACE_FILE_KEY,
                "ident_cely": ORG_IDENT,
            }
        else:
            serialized_record = self._build_insert_payload(ORG_IDENT, ORG_NAZEV_ZKRACENY)
        return FakeRedis(
            {
                f"import_data_count_{JOB_ID}": "1",
                f"import_performed_action_{JOB_ID}": performed_action,
                f"import_data_{JOB_ID}_record_0": json.dumps(serialized_record),
            }
        )

    @staticmethod
    def _build_insert_payload(ident_cely: str, nazev_zkraceny: str) -> dict:
        """Vrátí kompletní payload pro INSERT/UPDATE Organizace."""
        return {
            "__file_name": ORGANIZACE_FILE_KEY,
            "ident_cely": ident_cely,
            "nazev": "Importovaná organizace",
            "nazev_en": "Imported organization",
            "nazev_zkraceny": nazev_zkraceny,
            "nazev_zkraceny_en": f"{nazev_zkraceny}EN",
            "oao": False,
            "mesicu_do_zverejneni": 36,
            "email": "org@example.cz",
            "telefon": "+420123456789",
            "adresa": "Testovací 1, Praha",
            "ico": "12345678",
            "zanikla": False,
            "cteni_dokumentu": False,
            "ror": None,
            "web": None,
            "soucast": None,
            "typ_organizace": TYP_ORG_IDENT,
            "zverejneni_pristupnost": PRISTUPNOST_IDENT,
            "licence": LICENCE_IDENT,
        }

    def test_insert_writes_organizace_to_database_and_saves_to_fedora(self):
        """run_data_import vloží jeden Organizace záznam do DB a zapíše ho do Fedory přes ``save_metadata``."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        save_metadata_calls = self._run_import(fake_redis)

        self.assertTrue(
            Organizace.objects.filter(ident_cely=ORG_IDENT).exists(),
            "Očekáván nově vytvořený Organizace záznam v DB.",
        )
        created = Organizace.objects.get(ident_cely=ORG_IDENT)
        self.assertEqual(created.nazev, "Importovaná organizace")
        self.assertEqual(created.nazev_zkraceny, ORG_NAZEV_ZKRACENY)
        self.assertEqual(created.typ_organizace_id, self.typ_org.pk)
        self.assertEqual(created.licence_id, self.licence.pk)

        saved_ident_cely = [getattr(record, "ident_cely", None) for record in save_metadata_calls]
        self.assertIn(
            ORG_IDENT,
            saved_ident_cely,
            f"save_metadata mělo být zavoláno pro {ORG_IDENT}, voláno pro: {saved_ident_cely}",
        )

        primary_keys_raw = fake_redis.get(f"import_data_primary_keys_{JOB_ID}")
        self.assertIsNotNone(primary_keys_raw, "import_data_primary_keys nemělo zůstat prázdné.")
        primary_keys = json.loads(primary_keys_raw.decode("utf-8"))
        self.assertEqual(primary_keys.get("0"), f"ident_cely: {ORG_IDENT}")

    def _run_import(
        self,
        fake_redis: FakeRedis,
        save_metadata_side_effect=None,
        refresh_lock_side_effect=None,
    ):
        """Spustí ``run_data_import`` s mocknutým Redis a Fedora; vrátí seznam volání ``save_metadata``."""
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
            fedora_transaction_mock.return_value = MagicMock(uid="test-fedora-uid")
            fedora_deletion_mock.return_value = MagicMock(uid="test-fedora-deletion-uid", updated_ident_cely=set())
            signals_fedora_transaction_mock.return_value = MagicMock(uid="test-signals-fedora-uid")
            cron_tasks.run_data_import(JOB_ID, self.user.id, LOCK_TOKEN)
        return save_metadata_calls

    def _create_existing_organizace(self) -> Organizace:
        """Vytvoří v DB organizaci, na kterou navazují testy update/delete.

        Organizace.post_save signál volá synchronně ``save_metadata`` (bez ``on_commit``),
        proto je třeba i fixture-vytvoření obalit do Fedora patches.
        """
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None), patch(
            "uzivatel.signals.FedoraTransaction"
        ) as signals_fedora_transaction_mock:
            signals_fedora_transaction_mock.return_value = MagicMock(uid="fixture-tx-uid")
            return Organizace.objects.create(
                ident_cely=ORG_IDENT,
                nazev="Původní org",
                nazev_zkraceny=ORG_NAZEV_ZKRACENY,
                nazev_zkraceny_en=f"{ORG_NAZEV_ZKRACENY}EN",
                typ_organizace=self.typ_org,
                zverejneni_pristupnost=self.pristupnost,
                licence=self.licence,
            )

    def _assert_import_failed(self, fake_redis: FakeRedis):
        """Ověří, že import skončil ve stavu selhání: progress=0 a stop flag je nastaven."""
        progress_raw = fake_redis.get(f"import_data_progress_{JOB_ID}")
        self.assertIsNotNone(progress_raw, "import_data_progress musí být nastaveno.")
        self.assertEqual(
            int(progress_raw.decode("utf-8")),
            cron_tasks.IMPORT_PROGRESS_PHASE_FAILED,
            "Při selhání musí být progress resetován na IMPORT_PROGRESS_PHASE_FAILED (0).",
        )
        self.assertIsNotNone(
            fake_redis.get(f"import_data_stop_{JOB_ID}"),
            "Při selhání musí být nastaven stop flag.",
        )

    def test_update_modifies_existing_organizace_and_saves_to_fedora(self):
        """run_data_import s akcí UPDATE přepíše existující záznam a zavolá ``save_metadata``."""
        self._create_existing_organizace()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        save_metadata_calls = self._run_import(fake_redis)

        updated = Organizace.objects.get(ident_cely=ORG_IDENT)
        self.assertEqual(updated.nazev, "Importovaná organizace")
        self.assertEqual(updated.email, "org@example.cz")
        self.assertIn(
            ORG_IDENT,
            [getattr(record, "ident_cely", None) for record in save_metadata_calls],
            "save_metadata mělo být zavoláno i při UPDATE.",
        )

    def test_delete_removes_organizace_from_database(self):
        """run_data_import s akcí DELETE odstraní záznam z databáze."""
        self._create_existing_organizace()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        self.assertFalse(
            Organizace.objects.filter(ident_cely=ORG_IDENT).exists(),
            "Po DELETE importu nesmí Organizace v DB existovat.",
        )

    def test_database_save_failure_marks_import_as_failed(self):
        """Pokud ``record.save()`` v DB fázi vyvolá výjimku, import skončí jako selhalý."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB při ukládání záznamu.")

        with patch.object(Organizace, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Pokud uložení Historie záznamu selže, import skončí jako selhalý."""
        from core.import_data_mappers import OrganizaceMapper
        from historie.models import Historie

        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB při ukládání Historie.")

        with patch.object(OrganizaceMapper, "get_record_history", staticmethod(lambda record: record)), patch.object(
            Historie, "save", failing_save
        ):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_fedora_save_failure_marks_import_as_failed(self):
        """Pokud ``save_metadata`` selže při zápisu do Fedora repozitáře, import skončí jako selhalý."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save_metadata(self, fedora_transaction, skip_container_check=False):
            raise RuntimeError("Simulované selhání Fedora repozitáře.")

        self._run_import(fake_redis, save_metadata_side_effect=failing_save_metadata)

        self._assert_import_failed(fake_redis)

    def _build_multi_record_redis(self, records: list[dict]) -> FakeRedis:
        """Sestaví FakeRedis s několika serializovanými záznamy."""
        initial = {
            f"import_data_count_{JOB_ID}": str(len(records)),
            f"import_performed_action_{JOB_ID}": ImportDataAdminForm.PERFORMED_ACTION_INSERT,
        }
        for index, record in enumerate(records):
            initial[f"import_data_{JOB_ID}_record_{index}"] = json.dumps(record)
        return FakeRedis(initial)

    def test_failure_mid_batch_rolls_back_all_inserted_records(self):
        """Selhání druhého záznamu v atomickém bloku zruší i už úspěšně uložený první záznam."""
        first = self._build_insert_payload("ORG-999011", "ORGMULTI11")
        # Záměrný duplikát ident_cely se prvním záznamem: druhý INSERT skončí IntegrityError.
        duplicate = self._build_insert_payload("ORG-999011", "ORGMULTI12")
        third = self._build_insert_payload("ORG-999013", "ORGMULTI13")
        fake_redis = self._build_multi_record_redis([first, duplicate, third])

        self._run_import(fake_redis)

        self.assertFalse(
            Organizace.objects.filter(ident_cely__in=["ORG-999011", "ORG-999013"]).exists(),
            "Při selhání uprostřed dávky se musí všechny dosud uložené záznamy odvolat.",
        )
        self._assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Předem nastavený stop flag způsobí, že se import po prvním záznamu zastaví a hlásí ``stopped_by_user``."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)
        fake_redis.set(f"import_data_stop_{JOB_ID}", "1")

        self._run_import(fake_redis)

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw, "Status message musí být nastaven.")
        self.assertIn(
            "stopped_by_user",
            status_raw.decode("utf-8"),
            "Při uživatelském stopu musí status obsahovat klíč ``stopped_by_user``.",
        )

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """UPDATE záznamu, který v DB neexistuje, vyvolá ``DoesNotExist`` a import skončí jako selhalý."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)
        self.assertFalse(
            Organizace.objects.filter(ident_cely=ORG_IDENT).exists(),
            "Selhaný UPDATE nesmí vytvořit nový záznam.",
        )

    def test_insert_of_duplicate_ident_marks_import_as_failed(self):
        """INSERT záznamu s již existujícím ``ident_cely`` skončí IntegrityError a původní záznam zůstane beze změny."""
        original = self._create_existing_organizace()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)
        existing = Organizace.objects.get(pk=original.pk)
        self.assertEqual(
            existing.nazev,
            "Původní org",
            "Selhaný INSERT nesmí přepsat hodnoty původního záznamu.",
        )

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Pokud ``refresh_import_lock`` během importu vrátí False, vyvolá se ``ImportLockLostError``."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis, refresh_lock_side_effect=[True, False, False, False, False])

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw, "Status message musí být nastaven.")
        self.assertIn(
            "failed_lock_lost",
            status_raw.decode("utf-8"),
            "Při ztrátě locku musí status zůstat ``failed_lock_lost`` (nepřepisuje se generickou hláškou).",
        )
        self._assert_import_failed(fake_redis)

    def test_successful_import_writes_success_marker_into_progress_details(self):
        """Úspěšný import zapíše do ``import_data_progress_details_{job_id}`` značku ``success``."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn(
            "cron.tasks.run_data_import.success",
            decoded,
            "Po úspěšném importu musí být v progress_details značka ``success``.",
        )
