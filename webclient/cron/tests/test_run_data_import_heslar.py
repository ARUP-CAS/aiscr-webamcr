"""Jednotkové testy pro ``cron.tasks.run_data_import`` — import jednoho záznamu Heslář."""

import json
from unittest.mock import MagicMock, patch

from core.constants import ROLE_BADATEL_ID
from core.forms import ImportDataAdminForm
from core.tests.fake_redis import FakeRedis
from cron import tasks as cron_tasks
from django.contrib.auth.models import Group
from django.test import TestCase
from heslar.hesla import HESLAR_LICENCE, HESLAR_OBDOBI, HESLAR_ORGANIZACE_TYP, HESLAR_PRISTUPNOST
from heslar.models import Heslar, HeslarNazev
from uzivatel.models import Organizace, User

HESLAR_FILE_KEY = "heslar"
JOB_ID = "test-job-heslar"
LOCK_TOKEN = "test-lock-token"

HESLAR_IDENT = "HES-999001"
HESLAR_NAZEV_HESLARE = "obdobi"


class RunDataImportHeslarTest(TestCase):
    """Testy ``run_data_import`` pro mapper ``HeslarMapper`` s mocknutým Redis i Fedora repozitářem."""

    @classmethod
    def setUpTestData(cls):
        """Připraví minimální fixtures — ``HeslarNazev``, organizaci a uživatele běžícího import."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch("xml_generator.models.ModelWithMetadata.save_metadata", lambda *a, **kw: None):
            cls.heslar_nazev, _ = HeslarNazev.objects.get_or_create(
                id=HESLAR_OBDOBI, defaults={"nazev": HESLAR_NAZEV_HESLARE}
            )

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
                ident_cely="ORG-IMP-HES-001",
                defaults={
                    "nazev": "Org pro import",
                    "nazev_zkraceny": "ORGIMP",
                    "typ_organizace": typ_org,
                    "zverejneni_pristupnost": pristupnost,
                    "licence": licence,
                },
            )
            cls.user = User.objects.create_user(  # type: ignore[attr-defined]
                email="import-runner@example.cz",
                password="pass",
                is_active=True,
                organizace=cls.organizace,
                ident_cely="U-IMP-001",
                first_name="Import",
                last_name="Runner",
            )

    def _build_redis(self, performed_action: str) -> FakeRedis:
        """Sestaví ``FakeRedis`` s jedním serializovaným ``Heslar`` záznamem připraveným pro import.

        DELETE smí obsahovat pouze sloupec primárního klíče — jinak ``_check_column_structure``
        vyhodnotí ostatní sloupce jako ``excess`` a vyhodí ``ImportDataIncorrectStructureError``.
        """
        if performed_action == ImportDataAdminForm.PERFORMED_ACTION_DELETE:
            serialized_record = {
                "__file_name": HESLAR_FILE_KEY,
                "ident_cely": HESLAR_IDENT,
            }
        else:
            serialized_record = {
                "__file_name": HESLAR_FILE_KEY,
                "ident_cely": HESLAR_IDENT,
                "heslo": "Doba železná",
                "heslo_en": "Iron Age",
                "popis": "Popis období",
                "popis_en": "Period description",
                "zkratka": "DZ-IMP",
                "razeni": 10,
                "nazev_heslare": HESLAR_NAZEV_HESLARE,
            }
        return FakeRedis(
            {
                f"import_data_count_{JOB_ID}": "1",
                f"import_performed_action_{JOB_ID}": performed_action,
                f"import_data_{JOB_ID}_record_0": json.dumps(serialized_record),
            }
        )

    def test_insert_writes_heslar_to_database_and_saves_to_fedora(self):
        """run_data_import vloží jeden Heslář záznam do DB a zapíše ho do Fedory přes ``save_metadata``."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        save_metadata_calls: list[Heslar] = []

        def fake_save_metadata(self, fedora_transaction, skip_container_check=False):
            save_metadata_calls.append(self)

        with patch("core.connectors.RedisConnector.get_connection", return_value=fake_redis), patch(
            "core.connectors.RedisConnector.refresh_import_lock", return_value=True
        ), patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ), patch(
            "xml_generator.models.ModelWithMetadata.save_metadata",
            autospec=True,
            side_effect=fake_save_metadata,
        ), patch(
            "cron.tasks.FedoraTransaction"
        ) as fedora_transaction_mock:
            fedora_transaction_mock.return_value = MagicMock(uid="test-fedora-uid")

            cron_tasks.run_data_import(JOB_ID, self.user.id, LOCK_TOKEN)

        # 1) DB save: hesla bylo zapsáno do databáze.
        self.assertTrue(
            Heslar.objects.filter(ident_cely=HESLAR_IDENT).exists(),
            "Očekáván nově vytvořený Heslář záznam v DB.",
        )
        created = Heslar.objects.get(ident_cely=HESLAR_IDENT)
        self.assertEqual(created.heslo, "Doba železná")
        self.assertEqual(created.heslo_en, "Iron Age")
        self.assertEqual(created.zkratka, "DZ-IMP")
        self.assertEqual(created.nazev_heslare, self.heslar_nazev)

        # 2) Fedora save: save_metadata bylo zavoláno právě pro nově vytvořený Heslář.
        saved_ident_cely = [record.ident_cely for record in save_metadata_calls]
        self.assertIn(
            HESLAR_IDENT,
            saved_ident_cely,
            f"save_metadata mělo být zavoláno pro {HESLAR_IDENT}, voláno pro: {saved_ident_cely}",
        )

        # 3) Redis primární klíče: import zapsal výsledek importu pod správným klíčem.
        primary_keys_raw = fake_redis.get(f"import_data_primary_keys_{JOB_ID}")
        self.assertIsNotNone(primary_keys_raw, "import_data_primary_keys nemělo zůstat prázdné.")
        primary_keys = json.loads(primary_keys_raw.decode("utf-8"))
        self.assertEqual(primary_keys.get("0"), f"ident_cely: {HESLAR_IDENT}")

    def _run_import(
        self,
        fake_redis: FakeRedis,
        save_metadata_side_effect=None,
        refresh_lock_side_effect=None,
    ):
        """Spustí ``run_data_import`` s mocknutým Redis a Fedora; vrátí seznam volání ``save_metadata``."""
        save_metadata_calls: list[Heslar] = []

        def default_side_effect(self, fedora_transaction, skip_container_check=False):
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
            "cron.tasks.FedoraTransaction"
        ) as fedora_transaction_mock, patch(
            "cron.tasks.FedoraDeletionOnlyTransaction"
        ) as fedora_deletion_mock, patch(
            "heslar.signals.FedoraTransaction"
        ) as signals_fedora_transaction_mock:
            fedora_transaction_mock.return_value = MagicMock(uid="test-fedora-uid")
            fedora_deletion_mock.return_value = MagicMock(uid="test-fedora-deletion-uid", updated_ident_cely=set())
            signals_fedora_transaction_mock.return_value = MagicMock(uid="test-signals-fedora-uid")
            cron_tasks.run_data_import(JOB_ID, self.user.id, LOCK_TOKEN)
        return save_metadata_calls

    def _create_existing_heslar(self) -> Heslar:
        """Vytvoří v DB heslo, na které se navazují testy update/delete."""
        return Heslar.objects.create(
            ident_cely=HESLAR_IDENT,
            nazev_heslare=self.heslar_nazev,
            heslo="Původní heslo",
            heslo_en="Original term",
            zkratka="ORIG",
            razeni=1,
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

    def test_update_modifies_existing_heslar_and_saves_to_fedora(self):
        """run_data_import s akcí UPDATE přepíše existující záznam a zavolá ``save_metadata``."""
        self._create_existing_heslar()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        save_metadata_calls = self._run_import(fake_redis)

        updated = Heslar.objects.get(ident_cely=HESLAR_IDENT)
        self.assertEqual(updated.heslo, "Doba železná")
        self.assertEqual(updated.heslo_en, "Iron Age")
        self.assertEqual(updated.zkratka, "DZ-IMP")
        self.assertIn(
            HESLAR_IDENT,
            [record.ident_cely for record in save_metadata_calls],
            "save_metadata mělo být zavoláno i při UPDATE.",
        )

    def test_delete_removes_heslar_from_database(self):
        """run_data_import s akcí DELETE odstraní záznam z databáze."""
        self._create_existing_heslar()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_DELETE)

        self._run_import(fake_redis)

        self.assertFalse(
            Heslar.objects.filter(ident_cely=HESLAR_IDENT).exists(),
            "Po DELETE importu nesmí Heslář v DB existovat.",
        )

    def test_database_save_failure_marks_import_as_failed(self):
        """Pokud ``record.save()`` v DB fázi vyvolá výjimku, import skončí jako selhalý."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB při ukládání záznamu.")

        with patch.object(Heslar, "save", failing_save):
            self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Pokud uložení Historie záznamu selže, import skončí jako selhalý."""
        from core.import_data_mappers import HeslarMapper
        from historie.models import Historie

        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB při ukládání Historie.")

        # HeslarMapper.get_record_history vrací výchozí None, takže historický loop by
        # nikdy neběžel. Pro účely testu vrátíme samotný záznam, aby Historie.save bylo voláno.
        with patch.object(HeslarMapper, "get_record_history", staticmethod(lambda record: record)), patch.object(
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
        record_payload = {
            "__file_name": HESLAR_FILE_KEY,
            "heslo": "Doba železná",
            "heslo_en": "Iron Age",
            "popis": "",
            "popis_en": "",
            "zkratka": "DZ",
            "razeni": 1,
            "nazev_heslare": HESLAR_NAZEV_HESLARE,
        }
        records = [
            {**record_payload, "ident_cely": "HES-MULTI-01"},
            # Záměrný duplikát ident_cely se prvním záznamem: druhý INSERT skončí IntegrityError.
            {**record_payload, "ident_cely": "HES-MULTI-01"},
            {**record_payload, "ident_cely": "HES-MULTI-03"},
        ]
        fake_redis = self._build_multi_record_redis(records)

        self._run_import(fake_redis)

        self.assertFalse(
            Heslar.objects.filter(ident_cely__in=["HES-MULTI-01", "HES-MULTI-03"]).exists(),
            "Při selhání uprostřed dávky se musí všechny dosud uložené záznamy odvolat.",
        )
        self._assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Předem nastavený stop flag způsobí, že se import po prvním záznamu zastaví a hlásí ``stopped_by_user``."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)
        # Stop flag nastavený před spuštěním importu — kontrola v cyklu ho zachytí
        # po zpracování prvního záznamu a nastaví status ``stopped_by_user``.
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
        # Záměrně nevytvoříme Heslar — UPDATE narazí na ``model_class.objects.get(...)`` -> DoesNotExist.
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_UPDATE)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)
        self.assertFalse(
            Heslar.objects.filter(ident_cely=HESLAR_IDENT).exists(),
            "Selhaný UPDATE nesmí vytvořit nový záznam.",
        )

    def test_insert_of_duplicate_ident_marks_import_as_failed(self):
        """INSERT záznamu s již existujícím ``ident_cely`` skončí IntegrityError a původní záznam zůstane beze změny."""
        original = self._create_existing_heslar()
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        self._assert_import_failed(fake_redis)
        existing = Heslar.objects.get(pk=original.pk)
        self.assertEqual(
            existing.heslo,
            "Původní heslo",
            "Selhaný INSERT nesmí přepsat hodnoty původního záznamu.",
        )

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Pokud ``refresh_import_lock`` během importu vrátí False, vyvolá se ``ImportLockLostError`` a status zůstane ``failed_lock_lost``."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        # První volání (lock acquisition před hlavní smyčkou) musí projít, další selhat,
        # aby se vyvolala ``ImportLockLostError`` ze závěrečného ``refresh_import_lock()`` v cyklu.
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
        """Úspěšný import zapíše do ``import_data_progress_details_{job_id}`` značku ``success`` pro každý záznam."""
        fake_redis = self._build_redis(ImportDataAdminForm.PERFORMED_ACTION_INSERT)

        self._run_import(fake_redis)

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn(
            "cron.tasks.run_data_import.success",
            decoded,
            "Po úspěšném importu musí být v progress_details značka ``success``.",
        )
