"""Jednotkové testy pro ``cron.tasks.run_data_import`` — mapper ``SouborMapper``."""

import json
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, mock_open, patch

from core.constants import IMPORT, SN_ZAPSANY, SOUBOR_RELATION_TYPE
from core.forms import ImportDataAdminForm
from core.models import Soubor
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from historie.models import Historie, HistorieVazby
from pas.models import SamostatnyNalez

SOUBOR_FILE_KEY = "soubory"


class RunDataImportSouborTest(RunDataImportMapperTestBase):
    """Testy ``run_data_import`` pro mapper ``SouborMapper``."""

    def _soubor_phase_patches(self):
        """Patche potřebné pro fázi importu souborů (čtení z disku, Fedora binary upload).

        Mock ``FedoraRepositoryConnector`` ukládá do ``self.connector_mock`` a všechny instance
        vyrobené patchnutou továrnou jsou dostupné v ``self.connector_instances`` pro inspekci
        volání jednotlivých metod (např. ``delete_binary_file``).
        """
        settings_value = SimpleNamespace(value=json.dumps({"DIRECTORY_PATH": "/tmp/import-data"}))
        binary_result = SimpleNamespace(
            size_mb=0.001,
            sha_512="sha",
            url_without_domain="/fedora/import-test.txt",
        )
        self.connector_instances: list[MagicMock] = []

        def connector_factory(*args, **kwargs):
            instance = MagicMock()
            instance.save_binary_file.return_value = binary_result
            instance.update_binary_file.return_value = binary_result
            instance.init_args = args
            instance.init_kwargs = kwargs
            self.connector_instances.append(instance)
            return instance

        return [
            patch("cron.tasks.CustomAdminSettings.objects.get", return_value=settings_value),
            patch("cron.tasks.os.path.isdir", return_value=True),
            patch("cron.tasks.os.path.isfile", return_value=True),
            patch("builtins.open", mock_open(read_data=b"data")),
            patch("core.models.Soubor.get_mime_types", return_value="text/plain"),
            patch("cron.tasks.FedoraRepositoryConnector", side_effect=connector_factory),
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

    def _create_existing_soubor(self, nazev="existing.txt", vazba=None) -> Soubor:
        """Vytvoří v DB Soubor navázaný na předanou souborovou vazbu pro UPDATE/DELETE testy."""
        historie_vazba = HistorieVazby.objects.create(typ_vazby=SOUBOR_RELATION_TYPE)
        soubor = Soubor(
            nazev=nazev,
            mimetype="text/plain",
            vazba=vazba or self.dokument.soubory,
            size_mb=0.001,
            path=f"AMCR/record/test-record/file/{uuid.uuid4()}",
            historie=historie_vazba,
        )
        soubor.suppress_signal = True
        soubor.save()
        return soubor

    def _create_samostatny_nalez_for_soubor(self, ident_cely="C-202399001-N90001") -> SamostatnyNalez:
        """Vytvoří samostatný nález s vlastní ``soubory`` vazbou pro test importu Souboru."""
        nalez = SamostatnyNalez(
            ident_cely=ident_cely,
            stav=SN_ZAPSANY,
            projekt=self.projekt,
            pristupnost=self.base_heslars["pristupnost"],
            katastr=self.katastr,
            nalezce=self.osoba,
            obdobi=self.extra_heslars["obdobi"],
            druh_nalezu=self.extra_heslars["predmet_druh"],
        )
        nalez.suppress_signal = True
        nalez.save()
        return nalez

    def _soubor_related_records(self, suffix):
        """Vrátí testovací cíle pokrývající všechny podporované typy vazby Souboru."""
        return (
            ("projekt", self.projekt),
            ("dokument", self.dokument),
            ("samostatny_nalez", self._create_samostatny_nalez_for_soubor(f"C-202399001-N90{suffix}")),
        )

    def _soubor_related_history_records(self, suffix):
        """Vrátí dvojice objektu pro Soubor.vazba a cíle pro historii hlavního záznamu."""
        samostatny_nalez = self._create_samostatny_nalez_for_soubor(f"C-202399001-N91{suffix}")
        return (
            ("projekt", self.projekt, self.projekt),
            ("archeologicky_zaznam", self.dokument, self.az),
            ("samostatny_nalez", samostatny_nalez, samostatny_nalez),
        )

    def _history_record_result(self, fake_redis):
        raw = fake_redis.get(f"import_data_history_record_result_{JOB_ID}")
        return json.loads(raw.decode("utf-8"))

    def _fedora_update_result(self, fake_redis):
        raw = fake_redis.get(f"import_fedora_result_{JOB_ID}")
        return json.loads(raw.decode("utf-8"))

    def _file_import_results(self, fake_redis):
        raw = fake_redis.get(f"import_data_files_{JOB_ID}")
        return json.loads(raw.decode("utf-8"))

    def assert_delete_binary_file_called_for_soubor(self, deleted_soubor):
        """Ověří, že byl zavolán ``FedoraRepositoryConnector.delete_binary_file(soubor)``.

        Prohlédne ``self.connector_instances`` zachycené patchnutou továrnou v ``_soubor_phase_patches``
        a hledá alespoň jeden connector, na kterém byla metoda zavolána s argumentem nesoucím stejné
        ``nazev`` jako mazaný Soubor. (Po ``record.delete()`` Django nuluje ``pk``, takže porovnání
        identity ani ``pk`` není spolehlivé — porovnáváme tedy ``nazev``, který na in-memory instanci
        zůstává.)

        :param deleted_soubor: Instance ``Soubor`` očekávaná jako argument volání ``delete_binary_file``.
        """
        matching = [
            conn
            for conn in self.connector_instances
            if conn.delete_binary_file.called
            and any(
                call.args and getattr(call.args[0], "nazev", None) == deleted_soubor.nazev
                for call in conn.delete_binary_file.call_args_list
            )
        ]
        self.assertTrue(
            matching,
            "Po DELETE Souboru musí být na ``FedoraRepositoryConnector`` zavolána metoda "
            "``delete_binary_file(soubor)`` pro mazaný Soubor (nazev={!r}). "
            "Zachycené connectory: {} z {} celkem.".format(
                deleted_soubor.nazev, len(matching), len(self.connector_instances)
            ),
        )

    def assert_history_record_result_contains_item(self, fake_redis, record_id="0"):
        """Ověří pomocnou podmínku importního testu.

        :param fake_redis: Hodnota použitá v testovacím importním scénáři.
        :param record_id: Hodnota použitá v testovacím importním scénáři."""
        history_record_result = self._history_record_result(fake_redis)
        self.assertIn(record_id, history_record_result)
        self.assertIn("history_record_created", history_record_result[record_id])

    def assert_related_record_save_metadata_called(self, save_metadata_calls, related_record):
        """Ověří, že Fedora metadata byla uložena pro objekt dohledaný přes ``Soubor.vazba``.

        :param save_metadata_calls: Seznam objektů, pro které bylo zavoláno ``save_metadata`` ve Fedoře.
        :param related_record: Navázaný hlavní záznam, jehož ``ident_cely`` se očekává mezi voláními."""
        ident_celies = [getattr(item, "ident_cely", None) for item in save_metadata_calls]
        self.assertIn(
            related_record.ident_cely,
            ident_celies,
            "``save_metadata`` musí být zavoláno pro navázaný objekt "
            f"({related_record.ident_cely}). Volání pro: {ident_celies}",
        )

    def assert_related_record_metadata_updated(self, save_metadata_calls, related_history_record):
        """Ověří, že import souboru spustil Fedora ``save_metadata`` na navázaném hlavním záznamu.

        :param save_metadata_calls: Seznam objektů, pro které bylo zavoláno ``save_metadata`` ve Fedoře.
        :param related_history_record: Navázaný hlavní záznam, u něhož mají být přegenerována Fedora metadata."""
        ident_celies = [getattr(item, "ident_cely", None) for item in save_metadata_calls]
        self.assertIn(
            related_history_record.ident_cely,
            ident_celies,
            "Import Souboru musí přegenerovat Fedora metadata navázaného záznamu "
            f"({related_history_record.ident_cely}). Volání pro: {ident_celies}",
        )

    def assert_no_related_history_record_created(self, related_history_record, file_name):
        """Ověří, že na navázaném hlavním záznamu nevznikla historie o importu souboru.

        :param related_history_record: Navázaný hlavní záznam, jehož historie se kontroluje.
        :param file_name: Název souboru očekávaný v poznámce historického záznamu."""
        history_count = Historie.objects.filter(
            vazba=related_history_record.historie,
            typ_zmeny=IMPORT,
            poznamka__contains=file_name,
        ).count()
        self.assertEqual(
            history_count,
            0,
            "Import Souboru NESMÍ zapisovat historii na navázaný záznam "
            f"({related_history_record.ident_cely}); namísto historie se aktualizují pouze Fedora metadata.",
        )

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

    def test_insert_soubor_updates_related_metadata_creates_history_and_reports_it(self):
        """INSERT Souboru musí aktualizovat metadata, vytvořit historii a propsat ji do reportu."""
        file_name = "report-check.txt"
        fake_redis, save_metadata_calls = self._run_soubor_import(
            [{"vazba": self.dokument.ident_cely, "nazev": file_name}],
        )

        self.assert_import_success(fake_redis)
        soubor = Soubor.objects.get(vazba=self.dokument.soubory, nazev=file_name)
        self.assert_related_record_metadata_updated(save_metadata_calls, self.az)
        self.assertTrue(
            Historie.objects.filter(
                vazba=soubor.historie,
                typ_zmeny=IMPORT,
                poznamka__contains=file_name,
            ).exists(),
            "Import Souboru musí vytvořit historický záznam na historii importovaného Souboru.",
        )
        history_record_result = self._history_record_result(fake_redis)
        self.assertIn("0", history_record_result)
        self.assertIn("history_record_created", history_record_result["0"])
        fedora_update_result = self._fedora_update_result(fake_redis)
        self.assertIn("0", fedora_update_result)
        self.assertTrue(
            any(self.az.ident_cely in item for item in fedora_update_result["0"]),
            "Report musí obsahovat informaci o aktualizaci Fedora metadat navázaného záznamu.",
        )

    def test_insert_soubor_saves_related_record_metadata_for_all_supported_vazba_types(self):
        """INSERT Souboru musí uložit metadata objektu navázaného přes ``Soubor.vazba``."""
        for label, related_record in self._soubor_related_records("001"):
            with self.subTest(vazba=label):
                file_name = f"insert-{label}.txt"
                fake_redis, save_metadata_calls = self._run_soubor_import(
                    [{"vazba": related_record.ident_cely, "nazev": file_name}],
                )

                self.assert_import_success(fake_redis)
                soubor = Soubor.objects.get(vazba=related_record.soubory, nazev=file_name)
                self.assertEqual(soubor.vazba.navazany_objekt, related_record)
                self.assert_related_record_save_metadata_called(save_metadata_calls, related_record)

    def test_insert_soubor_updates_related_record_metadata_for_supported_targets(self):
        """INSERT Souboru musí přegenerovat Fedora metadata navázaného hlavního záznamu a nezapsat na něj historii."""
        for label, soubor_related_record, related_history_record in self._soubor_related_history_records("001"):
            with self.subTest(vazba=label):
                file_name = f"insert-history-{label}.txt"
                fake_redis, save_metadata_calls = self._run_soubor_import(
                    [{"vazba": soubor_related_record.ident_cely, "nazev": file_name}],
                )

                self.assert_import_success(fake_redis)
                self.assert_related_record_metadata_updated(save_metadata_calls, related_history_record)
                self.assert_no_related_history_record_created(related_history_record, file_name)

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
        self.assertIsNotNone(existing.rozsah)
        self.assertEqual(existing.rozsah, 1)
        navazany_ident_celies = [getattr(item, "ident_cely", None) for item in save_metadata_calls]
        self.assertIn(navazany_ident_cely, navazany_ident_celies)
        self.assert_history_record_result_contains_item(fake_redis)

    def test_update_soubor_saves_related_record_metadata_for_all_supported_vazba_types(self):
        """UPDATE Souboru musí uložit metadata objektu navázaného přes ``Soubor.vazba``."""
        for label, related_record in self._soubor_related_records("002"):
            with self.subTest(vazba=label):
                file_name = f"update-{label}.txt"
                existing = self._create_existing_soubor(nazev=file_name, vazba=related_record.soubory)
                fake_redis, save_metadata_calls = self._run_soubor_import(
                    [
                        {
                            "id": f"soub-{existing.id}",
                            "vazba": related_record.ident_cely,
                            "nazev": file_name,
                        }
                    ],
                    performed_action=ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
                )

                self.assert_import_success(fake_redis)
                existing.refresh_from_db()
                self.assertEqual(existing.vazba.navazany_objekt, related_record)
                self.assert_related_record_save_metadata_called(save_metadata_calls, related_record)

    def test_update_soubor_updates_related_record_metadata_for_supported_targets(self):
        """UPDATE Souboru musí přegenerovat Fedora metadata navázaného hlavního záznamu a nezapsat na něj historii."""
        for label, soubor_related_record, related_history_record in self._soubor_related_history_records("002"):
            with self.subTest(vazba=label):
                file_name = f"update-history-{label}.txt"
                existing = self._create_existing_soubor(nazev=file_name, vazba=soubor_related_record.soubory)
                fake_redis, save_metadata_calls = self._run_soubor_import(
                    [
                        {
                            "id": f"soub-{existing.id}",
                            "vazba": soubor_related_record.ident_cely,
                            "nazev": file_name,
                        }
                    ],
                    performed_action=ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
                )

                self.assert_import_success(fake_redis)
                self.assert_related_record_metadata_updated(save_metadata_calls, related_history_record)
                self.assert_no_related_history_record_created(related_history_record, file_name)

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
        from arch_z.models import ArcheologickyZaznam as AzModel
        from dokument.models import Dokument as DokumentModel

        existing = self._create_existing_soubor(nazev="to-delete.txt")
        soubor_id = existing.id
        navazany_ident_cely = self.dokument.ident_cely

        def real_get_record_from_ident(ident_cely):
            for model in (DokumentModel, AzModel):
                try:
                    return model.objects.get(ident_cely=ident_cely)
                except model.DoesNotExist:
                    continue
            raise DokumentModel.DoesNotExist(ident_cely)

        # Sledujeme datovou (DELETE) transakci, ze které FedoraRepositoryConnector dědí override_tombstone.
        # FedoraTransaction ve Fedora-update fázi pouze obnovuje metadata rodičů a record_deletion
        # tam nevolá, takže override_tombstone na ní nemá smysl a zůstává ve výchozí hodnotě False.
        deletion_transactions: list[MagicMock] = []

        def deletion_transaction_factory(*args, **kwargs):
            transaction_mock = MagicMock(uid="test-deletion-uid", updated_ident_cely=set())
            transaction_mock.override_tombstone = False
            deletion_transactions.append(transaction_mock)
            return transaction_mock

        fake_redis, save_metadata_calls = self._run_soubor_import(
            [{"id": f"soub-{soubor_id}"}],
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_DELETE,
            extra_patches=[
                patch("cron.tasks.get_record_from_ident", side_effect=real_get_record_from_ident),
                patch("cron.tasks.FedoraDeletionOnlyTransaction", side_effect=deletion_transaction_factory),
            ],
        )

        self.assert_import_success(fake_redis)
        self.assertTrue(
            deletion_transactions,
            "Během DELETE Souboru musí být v ``run_data_import`` vytvořena alespoň jedna "
            "``FedoraDeletionOnlyTransaction``.",
        )
        self.assertTrue(
            all(t.override_tombstone is True for t in deletion_transactions),
            "Každá ``FedoraDeletionOnlyTransaction`` vytvořená v ``run_data_import`` musí mít "
            "``override_tombstone=True``, aby ji ``FedoraRepositoryConnector.record_deletion`` "
            "převzal jako podklad pro hlavičku ``Overwrite-Tombstone``. "
            f"Zachycené hodnoty: {[t.override_tombstone for t in deletion_transactions]}",
        )
        self.assertFalse(
            Soubor.objects.filter(id=soubor_id).exists(),
            "Po DELETE akci pro SouborMapper musí být řádek v DB skutečně smazán.",
        )
        self.assert_history_record_result_contains_item(fake_redis)
        navazany_ident_celies = [getattr(item, "ident_cely", None) for item in save_metadata_calls]
        self.assertIn(
            navazany_ident_cely,
            navazany_ident_celies,
            "Po smazání Souboru musí být ``save_metadata`` zavoláno pro navázaný objekt "
            f"({navazany_ident_cely}). Volání pro: {navazany_ident_celies}",
        )
        self.assertIn(
            self.az.ident_cely,
            navazany_ident_celies,
            "Po smazání Souboru musí být ``save_metadata`` zavoláno i pro archeologický záznam "
            "navázaný přes ``DokumentCast`` "
            f"({self.az.ident_cely}). Volání pro: {navazany_ident_celies}",
        )
        self.assert_delete_binary_file_called_for_soubor(existing)

    def test_delete_soubor_updates_parent_record_metadata_for_supported_vazba_types(self):
        """DELETE Souboru musí přegenerovat Fedora metadata rodičovského záznamu."""
        from arch_z.models import ArcheologickyZaznam as AzModel
        from dokument.models import Dokument as DokumentModel
        from pas.models import SamostatnyNalez as SamostatnyNalezModel
        from projekt.models import Projekt as ProjektModel

        def real_get_record_from_ident(ident_cely):
            for model in (ProjektModel, DokumentModel, SamostatnyNalezModel, AzModel):
                try:
                    return model.objects.get(ident_cely=ident_cely)
                except model.DoesNotExist:
                    continue
            raise DokumentModel.DoesNotExist(ident_cely)

        for label, parent_record in self._soubor_related_records("003"):
            with self.subTest(vazba=label):
                existing = self._create_existing_soubor(
                    nazev="delete-parent-{}.txt".format(label),
                    vazba=parent_record.soubory,
                )
                soubor_id = existing.id
                fake_redis, save_metadata_calls = self._run_soubor_import(
                    [{"id": "soub-{}".format(soubor_id)}],
                    performed_action=ImportDataAdminForm.PERFORMED_ACTION_DELETE,
                    extra_patches=[
                        patch("cron.tasks.get_record_from_ident", side_effect=real_get_record_from_ident),
                    ],
                )

                self.assert_import_success(fake_redis)
                self.assertFalse(Soubor.objects.filter(id=soubor_id).exists())
                self.assert_history_record_result_contains_item(fake_redis)
                self.assert_related_record_save_metadata_called(save_metadata_calls, parent_record)
                self.assert_delete_binary_file_called_for_soubor(existing)

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

    def test_update_rename_to_conflicting_name_marks_import_as_failed(self):
        """UPDATE Souboru, jehož cílový ``nazev`` je již obsazen jiným souborem téže vazby, nesmí uspět."""
        existing = self._create_existing_soubor(nazev="old-name.txt")
        self._create_existing_soubor(nazev="taken-name.txt", vazba=self.dokument.soubory)
        fake_redis, _ = self._run_soubor_import(
            [
                {
                    "id": f"soub-{existing.id}",
                    "vazba": self.dokument.ident_cely,
                    "nazev": "taken-name.txt",
                }
            ],
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_UPDATE,
        )

        self.assert_import_failed(fake_redis)
        file_results = self._file_import_results(fake_redis)
        self.assertEqual(file_results[0]["file_name"], "taken-name.txt")
        self.assertIn("already_exists", file_results[0]["additional_info"])

    def test_insert_existing_target_file_record_marks_import_as_failed(self):
        """INSERT Souboru na existující ``nazev`` + ``vazba`` nesmí skončit jako úspěšný import."""
        self._create_existing_soubor(nazev="already-present.txt", vazba=self.dokument.soubory)
        fake_redis, _ = self._run_soubor_import(
            [{"vazba": self.dokument.ident_cely, "nazev": "already-present.txt"}],
        )

        self.assert_import_failed(fake_redis)
        file_results = self._file_import_results(fake_redis)
        self.assertEqual(file_results[0]["file_name"], "already-present.txt")
        self.assertIn("already_exists", file_results[0]["additional_info"])

    def test_missing_binary_file_marks_import_as_failed(self):
        """Chybějící binární soubor v importním adresáři nesmí skončit jako úspěšný import."""
        fake_redis, _ = self._run_soubor_import(
            [{"vazba": self.dokument.ident_cely, "nazev": "missing-binary.txt"}],
            extra_patches=[patch("cron.tasks.os.path.isfile", return_value=False)],
        )

        self.assert_import_failed(fake_redis)
        file_results = self._file_import_results(fake_redis)
        self.assertEqual(file_results[0]["file_name"], "missing-binary.txt")
        self.assertIn("file_not_found_in_directory", file_results[0]["additional_info"])

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
