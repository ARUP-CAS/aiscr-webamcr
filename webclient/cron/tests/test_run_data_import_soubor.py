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

    def _soubor_phase_patches(self, mimetype="text/plain"):
        """Patche potřebné pro fázi importu souborů (čtení z disku, Fedora binary upload).

        Mock ``FedoraRepositoryConnector`` ukládá do ``self.connector_mock`` a všechny instance
        vyrobené patchnutou továrnou jsou dostupné v ``self.connector_instances`` pro inspekci
        volání jednotlivých metod (např. ``delete_binary_file``).

        :param mimetype: MIME typ vrácený mockem ``Soubor.get_mime_types``; musí odpovídat
            příponě importovaného souboru i whitelistu navázaného záznamu.
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
            patch("core.models.Soubor.get_mime_types", return_value=mimetype),
            patch("cron.tasks.FedoraRepositoryConnector", side_effect=connector_factory),
        ]

    def _run_soubor_import(self, payloads, performed_action=ImportDataAdminForm.PERFORMED_ACTION_INSERT, **kwargs):
        extra = kwargs.pop("extra_patches", None) or []
        mimetype = kwargs.pop("mimetype", "text/plain")
        return self.run_import_records(
            SOUBOR_FILE_KEY,
            payloads,
            performed_action,
            extra_patches=self._soubor_phase_patches(mimetype=mimetype) + list(extra),
            **kwargs,
        )

    @staticmethod
    def _file_fixture_for_vazba(label):
        """Vrátí příponu a MIME typ souboru vhodné pro whitelist daného typu vazby.

        Samostatný nález přijímá pouze obrazové formáty, ostatní typy vazby přijímají ``text/plain``.

        :param label: Označení typu vazby (``projekt``, ``dokument`` nebo ``samostatny_nalez``).
        :return: Dvojice ``(extension, mimetype)``.
        """
        if label == "samostatny_nalez":
            return "jpg", "image/jpeg"
        return "txt", "text/plain"

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
            ("dokument", self.dokument, self.dokument),
            ("samostatny_nalez", samostatny_nalez, samostatny_nalez),
        )

    def _history_record_result(self, fake_redis):
        raw = fake_redis.get(f"import_data_history_record_result_tr_{JOB_ID}")
        return json.loads(raw.decode("utf-8"))

    def _fedora_update_result(self, fake_redis):
        raw = fake_redis.get(f"import_fedora_result_tr_{JOB_ID}")
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
        details = fake_redis.lrange(f"import_data_progress_details_tr_{JOB_ID}", 0, -1)
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
        self.assert_related_record_metadata_updated(save_metadata_calls, self.dokument)
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
            any(self.dokument.ident_cely in item for item in fedora_update_result["0"]),
            "Report musí obsahovat informaci o aktualizaci Fedora metadat navázaného záznamu.",
        )

    def test_insert_soubor_saves_related_record_metadata_for_all_supported_vazba_types(self):
        """INSERT Souboru musí uložit metadata objektu navázaného přes ``Soubor.vazba``."""
        for label, related_record in self._soubor_related_records("001"):
            with self.subTest(vazba=label):
                extension, mimetype = self._file_fixture_for_vazba(label)
                file_name = f"insert-{label}.{extension}"
                fake_redis, save_metadata_calls = self._run_soubor_import(
                    [{"vazba": related_record.ident_cely, "nazev": file_name}],
                    mimetype=mimetype,
                )

                self.assert_import_success(fake_redis)
                soubor = Soubor.objects.get(vazba=related_record.soubory, nazev=file_name)
                self.assertEqual(soubor.vazba.navazany_objekt, related_record)
                self.assert_related_record_save_metadata_called(save_metadata_calls, related_record)

    def test_insert_soubor_updates_related_record_metadata_for_supported_targets(self):
        """INSERT Souboru musí přegenerovat Fedora metadata navázaného hlavního záznamu a nezapsat na něj historii."""
        for label, soubor_related_record, related_history_record in self._soubor_related_history_records("001"):
            with self.subTest(vazba=label):
                extension, mimetype = self._file_fixture_for_vazba(label)
                file_name = f"insert-history-{label}.{extension}"
                fake_redis, save_metadata_calls = self._run_soubor_import(
                    [{"vazba": soubor_related_record.ident_cely, "nazev": file_name}],
                    mimetype=mimetype,
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
                extension, mimetype = self._file_fixture_for_vazba(label)
                file_name = f"update-{label}.{extension}"
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
                    mimetype=mimetype,
                )

                self.assert_import_success(fake_redis)
                existing.refresh_from_db()
                self.assertEqual(existing.vazba.navazany_objekt, related_record)
                self.assert_related_record_save_metadata_called(save_metadata_calls, related_record)

    def test_update_soubor_updates_related_record_metadata_for_supported_targets(self):
        """UPDATE Souboru musí přegenerovat Fedora metadata navázaného hlavního záznamu a nezapsat na něj historii."""
        for label, soubor_related_record, related_history_record in self._soubor_related_history_records("002"):
            with self.subTest(vazba=label):
                extension, mimetype = self._file_fixture_for_vazba(label)
                file_name = f"update-history-{label}.{extension}"
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
                    mimetype=mimetype,
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

    def _run_soubor_delete_batch(self, count, extra_patches):
        """Spustí DELETE import několika Souborů najednou pro testy konzistence DB a Fedory.

        :param count: Počet mazaných Souborů (a tím i importovaných záznamů).
        :param extra_patches: Patche navíc předané importnímu běhu.
        :return: Trojice ``(fake_redis, seznam vytvořených Souborů, seznam jejich ID)``."""
        souborys = [self._create_existing_soubor(nazev="delete-batch-{}.txt".format(index)) for index in range(count)]
        soubor_ids = [soubor.id for soubor in souborys]
        fake_redis, _ = self._run_soubor_import(
            [{"id": "soub-{}".format(soubor_id)} for soubor_id in soubor_ids],
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_DELETE,
            extra_patches=extra_patches,
        )
        return fake_redis, souborys, soubor_ids

    def test_fedora_deletes_are_committed_only_after_the_database_commit(self):
        """Uvnitř otevřené databázové transakce se nesmí potvrdit žádná Fedora transakce mazání.

        Potvrzení jsou zaregistrována přes ``transaction.on_commit``; test callback zachytí místo spuštění
        a ověří, že do té chvíle nebylo potvrzeno nic a po jeho spuštění je potvrzeno všechno."""
        transaction_patch, transactions, commits = self.fedora_deletion_transaction_recorder()
        on_commit_patch, captured_callbacks = self.capture_fedora_delete_commit_patch()

        fake_redis, _souborys, soubor_ids = self._run_soubor_delete_batch(
            3, extra_patches=[transaction_patch, on_commit_patch]
        )

        self.assert_import_success(fake_redis)
        self.assertEqual(
            commits,
            [],
            "Dokud je databázová transakce otevřená, nesmí být potvrzena žádná Fedora transakce mazání "
            "(potvrzeno {} z {}).".format(len(commits), len(transactions)),
        )
        self.assertEqual(
            len(captured_callbacks),
            1,
            "Datová fáze musí zaregistrovat právě jeden ``on_commit`` callback potvrzující Fedora mazání.",
        )
        captured_callbacks[0]()
        self.assertEqual(
            len(commits),
            len(transactions),
            "Po commitu databáze musí být potvrzeny všechny zařazené Fedora transakce mazání.",
        )
        self.assertFalse(Soubor.objects.filter(id__in=soubor_ids).exists())

    def test_nth_fedora_delete_commit_failure_keeps_data_committed_and_reports_it(self):
        """Selhání N-tého potvrzení Fedora transakce nesmí zastavit zbytek fronty ani shodit import.

        Databáze je v tu chvíli již potvrzená, takže zbývající mazání musí doběhnout. Nedokončené mazání
        zůstává ve Fedoře jako osiřelý objekt — musí se objevit v reportu u dotčeného záznamu.

        Fronta potvrzení má pro tři mazané Soubory šest položek: tři prázdné transakce z datové smyčky
        a tři skutečné transakce mazání. Páté potvrzení je tedy mazání druhého Souboru."""
        transaction_patch, transactions, commits = self.fedora_deletion_transaction_recorder(fail_on_commit_number=5)

        fake_redis, souborys, soubor_ids = self._run_soubor_delete_batch(3, extra_patches=[transaction_patch])

        self.assert_import_success(fake_redis)
        self.assertFalse(
            Soubor.objects.filter(id__in=soubor_ids).exists(),
            "Selhání potvrzení ve Fedoře nesmí vrátit zpět již potvrzené mazání záznamů v databázi.",
        )
        self.assertEqual(
            len(commits),
            len(transactions),
            "Po selhání jednoho potvrzení musí fronta pokračovat zbývajícími transakcemi "
            "(potvrzeno {} z {}).".format(len(commits), len(transactions)),
        )
        reported = [item for items in self._fedora_update_result(fake_redis).values() for item in items]
        self.assertTrue(
            any("fedora_delete_commit_failed" in item and souborys[1].nazev in item for item in reported),
            "Nedokončené mazání ve Fedoře musí být nahlášeno v reportu i s identifikací souboru "
            "({}). Report: {}".format(souborys[1].nazev, reported),
        )

    def test_database_commit_failure_leaves_no_fedora_delete_committed(self):
        """Selhání commitu databáze nesmí zanechat potvrzené mazání ve Fedoře.

        Callbacky ``on_commit`` se při selhaném commitu nespustí, takže žádná zařazená transakce není
        potvrzena a všechny se musí zrušit."""
        transaction_patch, transactions, commits = self.fedora_deletion_transaction_recorder()

        fake_redis, _souborys, soubor_ids = self._run_soubor_delete_batch(
            3, extra_patches=[transaction_patch, self.failing_database_commit_patch()]
        )

        self.assert_import_failed(fake_redis)
        self.assertEqual(
            commits,
            [],
            "Při selhaném commitu databáze nesmí být potvrzena žádná Fedora transakce mazání.",
        )
        self.assertTrue(transactions, "Test musí vytvořit alespoň jednu Fedora transakci mazání.")
        for transaction_mock in transactions:
            transaction_mock.rollback_transaction.assert_called()
        self.assertEqual(
            Soubor.objects.filter(id__in=soubor_ids).count(),
            len(soubor_ids),
            "Po selhaném commitu se musí vrátit i mazání záznamů v databázi.",
        )

    def test_record_failure_rolls_back_fedora_transactions_of_earlier_records(self):
        """Chyba u pozdějšího záznamu musí zrušit Fedora transakce zařazené předchozími záznamy."""
        transaction_patch, transactions, commits = self.fedora_deletion_transaction_recorder()
        existing = self._create_existing_soubor(nazev="rollback-earlier.txt")

        fake_redis, _ = self._run_soubor_import(
            [{"id": "soub-{}".format(existing.id)}, {"id": "soub-0"}],
            performed_action=ImportDataAdminForm.PERFORMED_ACTION_DELETE,
            extra_patches=[transaction_patch],
        )

        self.assert_import_failed(fake_redis)
        self.assertEqual(commits, [], "Zrušená datová fáze nesmí potvrdit žádnou Fedora transakci mazání.")
        self.assertTrue(transactions, "První záznam musí stihnout vytvořit Fedora transakci mazání.")
        for transaction_mock in transactions:
            transaction_mock.rollback_transaction.assert_called()
        self.assertTrue(Soubor.objects.filter(id=existing.id).exists())

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
        self.assertIn("already_exists", file_results[0]["additional_info_tr"])

    def test_insert_existing_target_file_record_marks_import_as_failed(self):
        """INSERT Souboru na existující ``nazev`` + ``vazba`` nesmí skončit jako úspěšný import."""
        self._create_existing_soubor(nazev="already-present.txt", vazba=self.dokument.soubory)
        fake_redis, _ = self._run_soubor_import(
            [{"vazba": self.dokument.ident_cely, "nazev": "already-present.txt"}],
        )

        self.assert_import_failed(fake_redis)
        file_results = self._file_import_results(fake_redis)
        self.assertEqual(file_results[0]["file_name"], "already-present.txt")
        self.assertIn("already_exists", file_results[0]["additional_info_tr"])

    def test_missing_binary_file_marks_import_as_failed(self):
        """Chybějící binární soubor v importním adresáři nesmí skončit jako úspěšný import."""
        fake_redis, _ = self._run_soubor_import(
            [{"vazba": self.dokument.ident_cely, "nazev": "missing-binary.txt"}],
            extra_patches=[patch("cron.tasks.os.path.isfile", return_value=False)],
        )

        self.assert_import_failed(fake_redis)
        file_results = self._file_import_results(fake_redis)
        self.assertEqual(file_results[0]["file_name"], "missing-binary.txt")
        self.assertIn("file_not_found_in_directory", file_results[0]["additional_info_tr"])

    def test_insert_file_with_mismatched_extension_marks_import_as_failed(self):
        """INSERT souboru, jehož přípona neodpovídá MIME typu detekovanému z obsahu, nesmí uspět."""
        fake_redis, _ = self._run_soubor_import(
            [{"vazba": self.dokument.ident_cely, "nazev": "renamed-photo.tif"}],
        )

        self.assert_import_failed(fake_redis)
        status_message = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}").decode("utf-8")
        self.assertEqual(status_message, "cron.tasks.run_data_import.failed_mime_extension_mismatch")
        fedora_result = self._fedora_update_result(fake_redis)
        self.assertIn("does not match detected mime type", fedora_result["0"][0])

    def test_insert_file_with_unsupported_mime_marks_import_as_failed(self):
        """INSERT souboru, jehož detekovaný MIME typ není v mapě podporovaných formátů, nesmí uspět."""
        fake_redis, _ = self._run_soubor_import(
            [{"vazba": self.dokument.ident_cely, "nazev": "neznamy.bin"}],
            mimetype="application/octet-stream",
        )

        self.assert_import_failed(fake_redis)
        status_message = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}").decode("utf-8")
        self.assertEqual(status_message, "cron.tasks.run_data_import.failed_mime_unsupported")
        fedora_result = self._fedora_update_result(fake_redis)
        self.assertIn("is not supported", fedora_result["0"][0])

    def test_insert_file_with_disallowed_mime_for_record_marks_import_as_failed(self):
        """INSERT souboru, jehož MIME typ není ve whitelistu navázaného záznamu, nesmí uspět.

        Samostatný nález přijímá pouze obrazové formáty — textový soubor s konzistentní
        příponou tedy projde kontrolou přípony, ale musí selhat na whitelistu záznamu.
        """
        nalez = self._create_samostatny_nalez_for_soubor("C-202399001-N95001")
        fake_redis, _ = self._run_soubor_import(
            [{"vazba": nalez.ident_cely, "nazev": "poznamka.txt"}],
        )

        self.assert_import_failed(fake_redis)
        status_message = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}").decode("utf-8")
        self.assertEqual(status_message, "cron.tasks.run_data_import.failed_mime_not_allowed")
        fedora_result = self._fedora_update_result(fake_redis)
        self.assertIn("is not allowed for record", fedora_result["0"][0])

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

        status_raw = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}")
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

        status_raw = fake_redis.get(f"import_data_status_message_tr_{JOB_ID}")
        self.assertIsNotNone(status_raw)
        self.assertIn("failed_lock_lost", status_raw.decode("utf-8"))
        self.assert_import_failed(fake_redis)

    def test_successful_import_writes_file_marker_into_progress_details(self):
        """Úspěšný import Souboru zapíše do ``import_data_progress_details_tr_{JOB_ID}`` značku ``file``.

        SouborMapper běží ve speciální fázi souborů a zapisuje vlastní značku
        ``cron.tasks.run_data_import.file`` (nikoli generický ``success``).
        """
        fake_redis, _ = self._run_soubor_import(
            [{"vazba": self.dokument.ident_cely, "nazev": "marker.txt"}],
        )

        details = fake_redis.lrange(f"import_data_progress_details_tr_{JOB_ID}", 0, -1)
        decoded = [item.decode("utf-8") for item in details]
        self.assertIn("cron.tasks.run_data_import.file", decoded)
        self.assert_history_record_result_contains_item(fake_redis)
