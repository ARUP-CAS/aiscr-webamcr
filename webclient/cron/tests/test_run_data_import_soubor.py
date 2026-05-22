"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``SouborMapper``."""

import json
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, mock_open, patch

from core.constants import SOUBOR_RELATION_TYPE
from core.forms import ImportDataAdminForm
from core.models import Soubor
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from historie.models import Historie, HistorieVazby

SOUBOR_FILE_KEY = "soubory"


class RunDataImportSouborTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``SouborMapper``."""

    def _soubor_phase_patches(self):
        """Patche potřebné pro fázi importu souborů (čtení z disku, Fedora binary upload)."""
        settings_value = SimpleNamespace(value=json.dumps({"DIRECTORY_PATH": "/tmp/import-data"}))
        binary_result = SimpleNamespace(
            size_mb=0.001,
            sha_512="sha",
            url_without_domain="/fedora/import-test.txt",
        )
        connector = MagicMock()
        connector.save_binary_file.return_value = binary_result
        connector.update_binary_file.return_value = binary_result
        return [
            patch("cron.tasks.CustomAdminSettings.objects.get", return_value=settings_value),
            patch("cron.tasks.os.path.isdir", return_value=True),
            patch("cron.tasks.os.path.isfile", return_value=True),
            patch("builtins.open", mock_open(read_data=b"data")),
            patch("core.models.Soubor.get_mime_types", return_value="text/plain"),
            patch("cron.tasks.FedoraRepositoryConnector", return_value=connector),
        ]

    def _run_soubor_import(self, payloads, performed_action=ImportDataAdminForm.PERFORMED_ACTION_INSERT, **kwargs):
        extra = kwargs.pop("extra_patches", None) or []
        return self.run_import_records(
            SOUBOR_FILE_KEY,
            payloads,
            performed_action,
            extra_patches=self._soubor_phase_patches() + list(extra),
            **kwargs,
        )

    def _create_existing_soubor(self, nazev="existing.txt") -> Soubor:
        """Vytvoří v DB Soubor navázaný na ``self.dokument.soubory`` pro UPDATE/DELETE testy."""
        historie_vazba = HistorieVazby.objects.create(typ_vazby=SOUBOR_RELATION_TYPE)
        soubor = Soubor(
            nazev=nazev,
            mimetype="text/plain",
            vazba=self.dokument.soubory,
            size_mb=0.001,
            historie=historie_vazba,
        )
        soubor.suppress_signal = True
        soubor.save()
        return soubor

    def _history_record_result(self, fake_redis):
        raw = fake_redis.get(f"import_data_history_record_result_{JOB_ID}")
        return json.loads(raw.decode("utf-8"))

    def assert_history_record_result_contains_item(self, fake_redis, record_id="0"):
        """Ověří pomocnou podmínku importního testu.

        :param fake_redis: Hodnota použitá v testovacím importním scénáři.
        :param record_id: Hodnota použitá v testovacím importním scénáři."""
        history_record_result = self._history_record_result(fake_redis)
        self.assertIn(record_id, history_record_result)
        self.assertIn("history_record_created", history_record_result[record_id])

    def test_insert_writes_soubor_to_database_and_saves_to_fedora(self):
        """INSERT vloží Soubor do DB, zapíše ho do Fedory a do progress značky přidá ``file``."""
        navazany_ident_cely = self.dokument.ident_cely
        fake_redis, save_metadata_calls = self._run_soubor_import(
            [{"vazba": self.dokument.ident_cely, "nazev": "import-test.txt"}],
        )

        self.assert_import_success(fake_redis)
        self.assertTrue(
            Soubor.objects.filter(vazba=self.dokument.soubory, nazev="import-test.txt").exists(),
            "Po INSERTu musí Soubor existovat v DB.",
        )
        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.file", decoded)
        navazany_ident_celies = [getattr(item, "ident_cely", None) for item in save_metadata_calls]
        self.assertIn(navazany_ident_cely, navazany_ident_celies)
        self.assert_history_record_result_contains_item(fake_redis)

    def test_update_re_uploads_binary_content_for_existing_soubor(self):
        """UPDATE pro Soubor je re-upload binárního obsahu se shodným ``nazev`` + ``vazba``.

        Fáze souborů vyhledává cílový Soubor podle ``nazev`` a ``vazba`` (nikoli podle PK)
        a při UPDATE volá ``update_binary_file``. Po úspěšném běhu se aktualizují
        atributy ``mimetype``, ``sha_512`` a ``path``.
        """
        existing = self._create_existing_soubor(nazev="reuploaded.txt")
        navazany_ident_cely = self.dokument.ident_cely
        fake_redis, save_metadata_calls = self._run_soubor_import(
            [
                {
                    "id": f"soub-{existing.id}",
                    "vazba": self.dokument.ident_cely,
                    "nazev": "reuploaded.txt",
                }
            ],
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_success(fake_redis)
        existing.refresh_from_db()
        self.assertEqual(existing.sha_512, "sha")
        self.assertEqual(existing.path, "/fedora/import-test.txt")
        navazany_ident_celies = [getattr(item, "ident_cely", None) for item in save_metadata_calls]
        self.assertIn(navazany_ident_cely, navazany_ident_celies)
        self.assert_history_record_result_contains_item(fake_redis)

    def test_delete_action_removes_soubor_from_database(self):
        """DELETE akce pro SouborMapper musí Soubor odstranit z DB a aktualizovat metadata navázaného objektu.

        ``run_data_import`` speciálně zpracuje SouborMapper s akcí DELETE přímo v datové fázi
        (``record.delete()`` se signálem potlačeným). Metadata navázaného objektu (``vazba.navazany_objekt``)
        se musí přesto přegenerovat — proto se přidává do ``fedora_update_targets_dict``
        a ve Fedora fázi se na něm volá ``save_metadata``.

        Base helper patchuje ``cron.tasks.get_record_from_ident`` na MagicMock — zde ho přepneme
        zpět na reálné načtení Dokumentu z DB, aby ``record.save_metadata`` skutečně dorazilo
        na patchovaný ``ModelWithMetadata.save_metadata``.
        """
        from dokument.models import Dokument as DokumentModel

        existing = self._create_existing_soubor(nazev="to-delete.txt")
        soubor_id = existing.id
        navazany_ident_cely = self.dokument.ident_cely

        def real_get_record_from_ident(ident_cely):
            return DokumentModel.objects.get(ident_cely=ident_cely)

        fake_redis, save_metadata_calls = self._run_soubor_import(
            [{"id": f"soub-{soubor_id}"}],
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_DELETE,
            extra_patches=[
                patch("cron.tasks.get_record_from_ident", side_effect=real_get_record_from_ident),
            ],
        )

        self.assert_import_success(fake_redis)
        self.assertFalse(
            Soubor.objects.filter(id=soubor_id).exists(),
            "Po DELETE akci pro SouborMapper musí být řádek v DB skutečně smazán.",
        )
        navazany_ident_celies = [getattr(item, "ident_cely", None) for item in save_metadata_calls]
        self.assertIn(
            navazany_ident_cely,
            navazany_ident_celies,
            "Po smazání Souboru musí být ``save_metadata`` zavoláno pro navázaný objekt "
            f"({navazany_ident_cely}). Volání pro: {navazany_ident_celies}",
        )

    def test_database_save_failure_marks_import_as_failed(self):
        """Selhání ``Soubor.save()`` v datové fázi musí import označit jako selhalý."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB při ukládání Souboru.")

        with patch.object(Soubor, "save", failing_save):
            fake_redis, _ = self._run_soubor_import(
                [{"vazba": self.dokument.ident_cely, "nazev": "fail-db.txt"}],
            )

        self.assert_import_failed(fake_redis)

    def test_history_save_failure_marks_import_as_failed(self):
        """Selhání ``Historie.save()`` během historické fáze musí import označit jako selhalý."""

        def failing_save(self, *args, **kwargs):
            raise RuntimeError("Simulované selhání DB při ukládání Historie.")

        with patch.object(Historie, "save", failing_save):
            fake_redis, _ = self._run_soubor_import(
                [{"vazba": self.dokument.ident_cely, "nazev": "fail-hist.txt"}],
            )

        self.assert_import_failed(fake_redis)

    def test_fedora_binary_upload_failure_marks_import_as_failed(self):
        """Selhání ``FedoraRepositoryConnector.save_binary_file`` ve fázi souborů musí import označit jako selhalý.

        SouborMapper nepoužívá ``save_metadata`` jako ostatní mappery — binární obsah
        se zapisuje přímo přes ``save_binary_file`` ve fázi importu souborů.
        """
        settings_value = SimpleNamespace(value=json.dumps({"DIRECTORY_PATH": "/tmp/import-data"}))
        failing_connector = MagicMock()
        failing_connector.save_binary_file.side_effect = RuntimeError("Simulované selhání Fedora binárního uploadu.")
        custom_patches = [
            patch("cron.tasks.CustomAdminSettings.objects.get", return_value=settings_value),
            patch("cron.tasks.os.path.isdir", return_value=True),
            patch("cron.tasks.os.path.isfile", return_value=True),
            patch("builtins.open", mock_open(read_data=b"data")),
            patch("core.models.Soubor.get_mime_types", return_value="text/plain"),
            patch("cron.tasks.FedoraRepositoryConnector", return_value=failing_connector),
        ]
        fake_redis, _ = self.run_import_records(
            SOUBOR_FILE_KEY,
            [{"vazba": self.dokument.ident_cely, "nazev": "fail-fedora-binary.txt"}],
            extra_patches=custom_patches,
        )

        self.assert_import_failed(fake_redis)

    def test_failure_mid_batch_marks_import_as_failed(self):
        """Selhání zápisu v polovině dávky ve fázi souborů musí celý import označit jako selhalý.

        Soubor mapper nesdílí atomický blok s ostatními mappery (zápisy jsou součástí
        samostatné fáze souborů), takže nelze zaručit, že už uložené záznamy zmizí.
        Ověřujeme proto pouze, že import skončí jako selhalý.
        """
        call_count = {"n": 0}
        original_save = Soubor.save

        def failing_second_save(self, *args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] >= 2:
                raise RuntimeError("Simulované selhání druhého záznamu.")
            return original_save(self, *args, **kwargs)

        with patch.object(Soubor, "save", failing_second_save):
            fake_redis, _ = self._run_soubor_import(
                [
                    {"vazba": self.dokument.ident_cely, "nazev": "batch-1.txt"},
                    {"vazba": self.dokument.ident_cely, "nazev": "batch-2.txt"},
                    {"vazba": self.dokument.ident_cely, "nazev": "batch-3.txt"},
                ],
            )

        self.assert_import_failed(fake_redis)

    def test_user_stop_during_import_marks_status_as_stopped(self):
        """Předem nastavený stop flag musí přepnout status na ``stopped_by_user``."""
        fake_redis, _ = self._run_soubor_import(
            [{"vazba": self.dokument.ident_cely, "nazev": "stop-me.txt"}],
            pre_redis_keys={f"import_data_stop_{JOB_ID}": "1"},
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("stopped_by_user", status_raw.decode("utf-8"))

    def test_update_of_nonexistent_record_marks_import_as_failed(self):
        """UPDATE záznamu, který v DB neexistuje, vyvolá ``DoesNotExist`` a import skončí jako selhalý."""
        bogus_id = str(uuid.uuid4())
        fake_redis, _ = self._run_soubor_import(
            [
                {
                    "id": f"soub-{bogus_id}",
                    "vazba": self.dokument.ident_cely,
                    "nazev": "ghost.txt",
                }
            ],
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)

    def test_delete_of_nonexistent_record_marks_import_as_failed(self):
        """DELETE záznamu, který v DB neexistuje, musí být zachycen a import označen jako selhalý.

        Soubor nemá přirozený duplicitní ``ident_cely`` (PK je auto UUID), takže místo
        duplicitního INSERTu testujeme DELETE na neexistující PK.
        """
        bogus_id = str(uuid.uuid4())
        fake_redis, _ = self._run_soubor_import(
            [{"id": f"soub-{bogus_id}"}],
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_DELETE,
        )

        self.assert_import_failed(fake_redis)

    def test_lock_lost_mid_import_sets_failed_lock_lost_status(self):
        """Pokud ``refresh_import_lock`` během importu vrátí False, status musí zůstat ``failed_lock_lost``."""
        fake_redis, _ = self._run_soubor_import(
            [{"vazba": self.dokument.ident_cely, "nazev": "lock-lost.txt"}],
            refresh_lock_side_effect=[True, False, False, False, False, False, False],
        )

        status_raw = fake_redis.get(f"import_data_status_message_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self.assert_import_failed(fake_redis)

    def test_successful_import_writes_file_marker_into_progress_details(self):
        """Úspěšný import Souboru zapíše do ``import_data_progress_details_{JOB_ID}`` značku ``file``.

        SouborMapper běží ve speciální fázi souborů a zapisuje vlastní značku
        ``cron.tasks.run_data_import.file`` (nikoli generický ``success``).
        """
        fake_redis, _ = self._run_soubor_import(
            [{"vazba": self.dokument.ident_cely, "nazev": "marker.txt"}],
        )

        details = fake_redis.lrange(f"import_data_progress_details_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.file", decoded)
        self.assert_history_record_result_contains_item(fake_redis)
