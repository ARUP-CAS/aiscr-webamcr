"""Jednotkové testy pro ``cron.tasks.run_data_import`` — import jednoho záznamu Osoba."""

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
from uzivatel.models import Organizace, Osoba, User

OSOBA_FILE_KEY = "osoby"
JOB_ID = "test-job-osoba"
LOCK_TOKEN = "test-lock-token"

OSOBA_IDENT = "OS-999001"


class RunDataImportOsobaTest(TestCase):
    """Testy ``run_data_import`` pro mapper ``OsobaMapper`` s mocknutým Redis i Fedora repozitářem."""

    @classmethod
    def setUpTestData(cls):
        """Připraví minimální fixtures — organizaci a uživatele běžícího import."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            typ_org_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_ORGANIZACE_TYP, defaults={"nazev": "typ_organizace"}
            )
            typ_org, _ = Heslar.objects.get_or_create(
                nazev_heslare=typ_org_nazev,
                zkratka="T",
                defaults={"ident_cely": "HES-IMP-TYPORG-001", "heslo": "Test", "heslo_en": "Test"},
            )
            pristupnost_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_PRISTUPNOST, defaults={"nazev": "pristupnost"}
            )
            pristupnost, _ = Heslar.objects.get_or_create(
                nazev_heslare=pristupnost_nazev,
                zkratka="A",
                defaults={"ident_cely": "HES-IMP-PRST-001", "heslo": "Veřejný", "heslo_en": "Public"},
            )
            licence_nazev, _ = HeslarNazev.objects.get_or_create(id=HESLAR_LICENCE, defaults={"nazev": "licence"})
            licence, _ = Heslar.objects.get_or_create(
                nazev_heslare=licence_nazev,
                zkratka="L",
                defaults={"ident_cely": "HES-IMP-LIC-001", "heslo": "Lic", "heslo_en": "Lic"},
            )

            cls.organizace, _ = Organizace.objects.get_or_create(
                ident_cely="ORG-IMP-OS-001",
                defaults={
                    "nazev": "Org pro import osob",
                    "nazev_zkraceny": "ORGOSIMP",
                    "typ_organizace": typ_org,
                    "zverejneni_pristupnost": pristupnost,
                    "licence": licence,
                },
            )
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner-os@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-IMP-OS-001",
                first_name="Import",
                last_name="Runner",
            )

    @staticmethod
    def _build_insert_payload(ident_cely: str) -> dict:
        """Vrátí kompletní payload pro INSERT/UPDATE Osoba."""
        return {
            "__file_name": OSOBA_FILE_KEY,
            "ident_cely": ident_cely,
            "vypis_cely": "Novák, Jan",
            "vypis": "Novák J.",
            "jmeno": "Jan",
            "prijmeni": "Novák",
            "rodne_prijmeni": None,
            "rok_narozeni": 1970,
            "rok_umrti": None,
            "orcid": None,
            "wikidata": None,
        }

    def _build_redis(self, performed_action: str) -> FakeRedis:
        """Sestaví ``FakeRedis`` s jedním serializovaným ``Osoba`` záznamem připraveným pro import."""
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
            serialized_record = {
                "__file_name": OSOBA_FILE_KEY,
                "ident_cely": OSOBA_IDENT,
            }
        else:
            serialized_record = self._build_insert_payload(OSOBA_IDENT)
        return FakeRedis(
            {
                f"import_data_count_{JOB_ID}": "1",
                f"import_performed_action_{JOB_ID}": performed_action,
                f"import_data_{JOB_ID}_record_0": json.dumps(serialized_record),
            }
        )

    def test_insert_writes_osoba_to_database_and_saves_to_fedora(self):
        """run_data_import vloží jeden Osoba záznam do DB a zapíše ho do Fedory přes ``save_metadata``."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        save_metadata_calls = self._run_import(fake_redis)

        self.assertTrue(
            Osoba.objects.filter(ident_cely=OSOBA_IDENT).exists(),
            "Očekáván nově vytvořený Osoba záznam v DB.",
        )
        created = Osoba.objects.get(ident_cely=OSOBA_IDENT)
        self.assertEqual(created.jmeno, "Jan")
        self.assertEqual(created.prijmeni, "Novák")
        self.assertEqual(created.rok_narozeni, 1970)

        saved_ident_cely = [getattr(record, "ident_cely", None) for record in save_metadata_calls]
        self.assertIn(
            OSOBA_IDENT,
            saved_ident_cely,
            f"save_metadata mělo být zavoláno pro {OSOBA_IDENT}, voláno pro: {saved_ident_cely}",
        )

        primary_keys_raw = fake_redis.get(f"import_data_primary_keys_{JOB_ID}")
        self.assertIsNotNone(primary_keys_raw, "import_data_primary_keys nemělo zůstat prázdné.")
        primary_keys = json.loads(primary_keys_raw.decode("utf-8"))
        self.assertEqual(primary_keys.get("0"), f"ident_cely: {OSOBA_IDENT}")

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

    def _create_existing_osoba(self) -> Osoba:
        """Vytvoří v DB osobu, na kterou navazují testy update/delete.

        Osoba.post_save signál volá synchronně ``save_metadata``, proto je třeba
        i fixture-vytvoření obalit do Fedora patches.
        """
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None), patch(
            "uzivatel.signals.FedoraTransaction"
        ) as signals_fedora_transaction_mock:
            signals_fedora_transaction_mock.return_value = MagicMock(uid="fixture-tx-uid")
            return Osoba.objects.create(
                ident_cely=OSOBA_IDENT,
                jmeno="Původní",
                prijmeni="Příjmení",
                vypis="Původní V.",
                vypis_cely="Příjmení, Původní",
                rok_narozeni=1950,
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

    def test_update_modifies_existing_osoba_and_saves_to_fedora(self):
        """run_data_import s akcí UPDATE přepíše existující záznam a zavolá ``save_metadata``."""
        self._create_existing_osoba()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        save_metadata_calls = self._run_import(fake_redis)

        updated = Osoba.objects.get(ident_cely=OSOBA_IDENT)
        self.assertEqual(updated.jmeno, "Jan")
        self.assertEqual(updated.prijmeni, "Novák")
        self.assertEqual(updated.rok_narozeni, 1970)
        self.assertIn(
            OSOBA_IDENT,
            [getattr(record, "ident_cely", None) for record in save_metadata_calls],
            "save_metadata mělo být zavoláno i při UPDATE.",
        )

    def test_delete_removes_osoba_from_database(self):
        """run_data_import s akcí DELETE odstraní záznam z databáze."""
        self._create_existing_osoba()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        self.assertFalse(
            Osoba.objects.filter(ident_cely=OSOBA_IDENT).exists(),
            "Po DELETE importu nesmí Osoba v DB existovat.",
        )

    def test_database_save_failure_marks_import_as_failed(self):
        """Pokud ``record.save()`` v DB fázi vyvolá výjimku, import skončí jako selhalý."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB při ukládání záznamu.")

        with patch.object(Osoba, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Pokud uložení Historie záznamu selže, import skončí jako selhalý."""
        from core.import_data_mappers import OsobaMapper
        from historie.models import Historie

        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB při ukládání Historie.")

        with patch.object(OsobaMapper, "get_record_history", staticmethod(lambda record: record)), patch.object(
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
        first = self._build_insert_payload("OS-999011")
        # Záměrný duplikát ident_cely se prvním záznamem: druhý INSERT skončí IntegrityError.
        duplicate = self._build_insert_payload("OS-999011")
        third = self._build_insert_payload("OS-999013")
        fake_redis = self._build_multi_record_redis([first, duplicate, third])

        self._run_import(fake_redis)

        self.assertFalse(
            Osoba.objects.filter(ident_cely__in=["OS-999011", "OS-999013"]).exists(),
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
            Osoba.objects.filter(ident_cely=OSOBA_IDENT).exists(),
            "Selhaný UPDATE nesmí vytvořit nový záznam.",
        )

    def test_insert_of_duplicate_ident_marks_import_as_failed(self):
        """INSERT záznamu s již existujícím ``ident_cely`` skončí IntegrityError a původní záznam zůstane beze změny."""
        original = self._create_existing_osoba()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)
        existing = Osoba.objects.get(pk=original.pk)
        self.assertEqual(
            existing.jmeno,
            "Původní",
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
