"""Jednotkové testy pro ``cron.tasks.run_data_import`` — import jednoho záznamu User."""

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

UZIVATEL_FILE_KEY = "uzivatele"
JOB_ID = "test-job-uzivatel"
LOCK_TOKEN = "test-lock-token"

USER_IDENT = "U-999001"
USER_EMAIL = "imported-user@example.cz"
USER_ORGANIZACE_IDENT = "ORG-IMP-UZ-001"


class RunDataImportUzivatelTest(TestCase):
    """Testy ``run_data_import`` pro mapper ``UzivatelMapper`` s mocknutým Redis i Fedora repozitářem."""

    @classmethod
    def setUpTestData(cls):
        """Připraví minimální fixtures — organizaci pro import a uživatele běžícího import."""
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
                ident_cely=USER_ORGANIZACE_IDENT,
                defaults={
                    "nazev": "Org pro import uživatelů",
                    "nazev_zkraceny": "ORGUZIMP",
                    "typ_organizace": typ_org,
                    "zverejneni_pristupnost": pristupnost,
                    "licence": licence,
                },
            )
            cls.runner = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner-uz@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-IMP-RUNNER-001",
                first_name="Import",
                last_name="Runner",
            )

    @staticmethod
    def _build_insert_payload(ident_cely: str, email: str) -> dict:
        """Vrátí kompletní payload pro INSERT/UPDATE User."""
        return {
            "__file_name": UZIVATEL_FILE_KEY,
            "ident_cely": ident_cely,
            "first_name": "Jan",
            "last_name": "Importovaný",
            "email": email,
            "telefon": None,
            "orcid": None,
            "jazyk": "cs",
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
            "date_joined": "2024-01-01 00:00:00",
            "last_login": None,
            "osoba": None,
            "organizace": USER_ORGANIZACE_IDENT,
        }

    def _build_redis(self, performed_action: str) -> FakeRedis:
        """Sestaví ``FakeRedis`` s jedním serializovaným ``User`` záznamem připraveným pro import."""
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
            serialized_record = {
                "__file_name": UZIVATEL_FILE_KEY,
                "ident_cely": USER_IDENT,
            }
        else:
            serialized_record = self._build_insert_payload(USER_IDENT, USER_EMAIL)
        return FakeRedis(
            {
                f"import_data_count_{JOB_ID}": "1",
                f"import_performed_action_{JOB_ID}": performed_action,
                f"import_data_{JOB_ID}_record_0": json.dumps(serialized_record),
            }
        )

    def test_insert_writes_user_to_database_and_saves_to_fedora(self):
        """run_data_import vloží jeden User záznam do DB a zapíše ho do Fedory přes ``save_metadata``."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self.assertTrue(
            User.objects.filter(ident_cely=USER_IDENT).exists(),
            "Očekáván nově vytvořený User záznam v DB.",
        )
        created = User.objects.get(ident_cely=USER_IDENT)
        self.assertEqual(created.first_name, "Jan")
        self.assertEqual(created.last_name, "Importovaný")
        self.assertEqual(created.email, USER_EMAIL)
        self.assertEqual(created.organizace_id, self.organizace.pk)

        # ``User.user_post_save_method`` plánuje ``save_metadata`` přes
        # ``transaction.on_commit``, který se pod ``TestCase`` neprovede — proto se
        # zápis do Fedora repozitáře neasertuje, pouze stav v DB a Redis.

        primary_keys_raw = fake_redis.get(f"import_data_primary_keys_{JOB_ID}")
        self.assertIsNotNone(primary_keys_raw, "import_data_primary_keys nemělo zůstat prázdné.")
        primary_keys = json.loads(primary_keys_raw.decode("utf-8"))
        self.assertEqual(primary_keys.get("0"), f"ident_cely: {USER_IDENT}")

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
            "uzivatel.models.User.save_metadata",
            autospec=True,
            side_effect=side_effect,
        ), patch(
            "xml_generator.models.ModelWithMetadata.record_deletion",
            autospec=True,
            return_value=None,
        ), patch(
            "uzivatel.models.User.record_deletion",
            autospec=True,
            return_value=None,
        ), patch(
            "historie.models.Historie.save_record_deletion_record",
            return_value=None,
        ), patch(
            "uzivatel.signals.Mailer.send_eu03", return_value=None
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
            cron_tasks.run_data_import(JOB_ID, self.runner.id, LOCK_TOKEN)
        return save_metadata_calls

    def _create_existing_user(self) -> User:
        """Vytvoří v DB uživatele, na kterého navazují testy update/delete.

        User.pre_save i post_save signály volají fedora pipeline; obalíme proto i
        fixture-vytvoření do potřebných patches.
        """
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("uzivatel.models.User.save_metadata", lambda *a, **kw: None), patch(
            "uzivatel.signals.FedoraTransaction"
        ) as signals_fedora_transaction_mock:
            signals_fedora_transaction_mock.return_value = MagicMock(uid="fixture-tx-uid")
            return User.objects.create_user(  # type: ignore[attr-defined]
                email=USER_EMAIL,
                password="pass",
                is_active=False,
                organizace=self.organizace,
                ident_cely=USER_IDENT,
                first_name="Původní",
                last_name="Uživatel",
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

    def test_update_modifies_existing_user_and_saves_to_fedora(self):
        """run_data_import s akcí UPDATE přepíše existující záznam a zavolá ``save_metadata``."""
        self._create_existing_user()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        updated = User.objects.get(ident_cely=USER_IDENT)
        self.assertEqual(updated.first_name, "Jan")
        self.assertEqual(updated.last_name, "Importovaný")
        self.assertTrue(updated.is_active)

    def test_delete_removes_user_from_database(self):
        """run_data_import s akcí DELETE odstraní záznam z databáze."""
        self._create_existing_user()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        self.assertFalse(
            User.objects.filter(ident_cely=USER_IDENT).exists(),
            "Po DELETE importu nesmí User v DB existovat.",
        )

    def test_database_save_failure_marks_import_as_failed(self):
        """Pokud ``record.save()`` v DB fázi vyvolá výjimku, import skončí jako selhalý."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB při ukládání záznamu.")

        with patch.object(User, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Pokud uložení Historie záznamu selže, import skončí jako selhalý.

        ``UzivatelMapper.get_record_history`` vrací přímo uživatele, takže historický
        loop běží bez další patche; stačí podstrčit selhávající ``Historie.save``.
        """
        from historie.models import Historie

        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB při ukládání Historie.")

        with patch.object(Historie, "save", failing_save):
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
        first = self._build_insert_payload("U-999011", "multi-01@example.cz")
        # Záměrný duplikát ident_cely se prvním záznamem: druhý INSERT skončí IntegrityError.
        duplicate = self._build_insert_payload("U-999011", "multi-02@example.cz")
        third = self._build_insert_payload("U-999013", "multi-03@example.cz")
        fake_redis = self._build_multi_record_redis([first, duplicate, third])

        self._run_import(fake_redis)

        self.assertFalse(
            User.objects.filter(ident_cely__in=["U-999011", "U-999013"]).exists(),
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
            User.objects.filter(ident_cely=USER_IDENT).exists(),
            "Selhaný UPDATE nesmí vytvořit nový záznam.",
        )

    def test_insert_of_duplicate_ident_marks_import_as_failed(self):
        """INSERT záznamu s již existujícím ``ident_cely`` skončí IntegrityError a původní záznam zůstane beze změny."""
        original = self._create_existing_user()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)
        existing = User.objects.get(pk=original.pk)
        self.assertEqual(
            existing.first_name,
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
