"""
Testy mapperu paradat souborů (``paradata.csv``, issue #3527).

Pokrývají strukturu sloupců podle akce, dohledání souboru podle ``path``, ověření distribuce,
ke které paradata patří, a přípravu záznamu pro fázi importu. Paradata nemění databázi ani
metadata záznamu a nezapisují historii – kontroluje se i to. Dotaz do Fedory je nahrazen mockem.
"""

from unittest.mock import patch

from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    DistribuceImportIntegrityError,
    DistribuceMissingRepositoryUuidError,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ImportDataInvalidDistributionError,
    ImportDataMissingReferencedValueError,
    ImportDataReservedDistributionError,
    ParadataMapper,
)
from core.models import Soubor
from core.repository_connector import FedoraNoResponseError, FedoraRepositoryConnector
from core.tests.test_mappers.fixtures import create_dokument_fixture, create_soubor_fixture
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "path": "rest/AMCR/record/C-TX-PARA-001/file/11111111-2222-3333-4444-555555555555",
    "nazev": "paradata.json",
    "mimetype": "application/json",
    "distribution": "orig",
}


class ParadataMapperStructureTest(TestCase):
    """Testy struktury sloupců ``paradata.csv`` podle prováděné akce."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        with self.assertRaises(ImportDataIncorrectStructureError):
            ParadataMapper(row).map(INSERT, serialize=True, include_primary_key=True)

    def test_id_column_is_not_accepted(self):
        """Paradata se odkazují cestou souboru, sloupec id je proto navíc."""
        row = VALID_ROW.copy()
        row["id"] = "soub-1"
        with self.assertRaises(ImportDataIncorrectStructureError):
            ParadataMapper(row).map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_path_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci path."""
        row = VALID_ROW.copy()
        del row["path"]
        with self.assertRaises(ImportDataIncorrectStructureError):
            ParadataMapper(row).map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        with self.assertRaises(ImportDataIncorrectStructureError):
            ParadataMapper({}).map(INSERT, serialize=True, include_primary_key=True)

    def test_delete_expects_only_path_and_distribution(self):
        """DELETE projde se sloupci path a distribution; nazev a mimetype jsou navíc."""
        ParadataMapper({"path": VALID_ROW["path"], "distribution": "orig"}).map(DELETE, serialize=True)
        with self.assertRaises(ImportDataIncorrectStructureError):
            ParadataMapper(VALID_ROW.copy()).map(DELETE, serialize=True)

    def test_map_returns_all_columns(self):
        """map() vrátí všechny sloupce importu včetně cesty souboru."""
        result = ParadataMapper(VALID_ROW.copy()).map(INSERT, serialize=True, include_primary_key=True)

        self.assertEqual(set(result.keys()), {"path", "nazev", "mimetype", "distribution"})
        self.assertEqual(result["path"], VALID_ROW["path"])


class ParadataMapperNameValidationTest(TestCase):
    """Testy validace názvu distribuce a cesty, které nepotřebují existující soubor."""

    def test_reserved_names_rejected(self):
        """Paradata nelze připojit ke kontejneru ``paradata`` ani pod ``thumb/page``."""
        for distribution in ("paradata", "thumb/page", "thumb/page/1"):
            with self.subTest(distribution=distribution):
                row = VALID_ROW.copy()
                row["distribution"] = distribution
                with self.assertRaises(ImportDataReservedDistributionError):
                    ParadataMapper(row).import_validation(INSERT)

    def test_unsafe_segments_rejected(self):
        """Názvy s prázdným segmentem nebo průchodem adresáři se odmítnou už při validaci."""
        for distribution in ("ocr//alto-xml", "../orig", "ocr/../../orig"):
            with self.subTest(distribution=distribution):
                row = VALID_ROW.copy()
                row["distribution"] = distribution
                with self.assertRaises(ImportDataInvalidDistributionError):
                    ParadataMapper(row).import_validation(INSERT)

    def test_empty_distribution_rejected(self):
        """Prázdný název distribuce se odmítne jako chybějící povinná hodnota."""
        row = VALID_ROW.copy()
        row["distribution"] = "  "
        with self.assertRaises(ImportDataError):
            ParadataMapper(row).import_validation(INSERT)

    def test_empty_path_rejected(self):
        """Prázdná cesta souboru se odmítne jako chybějící povinná hodnota."""
        row = VALID_ROW.copy()
        row["path"] = "   "
        with self.assertRaises(ImportDataError):
            ParadataMapper(row).import_validation(INSERT)


class ParadataMapperValidationTest(TestCase):
    """Testy validace importu paradat proti existujícím souborům a stavu distribucí ve Fedoře."""

    @classmethod
    def setUpTestData(cls):
        """Vytvoří dokument a soubor s cestou do Fedory."""
        cls.dokument = create_dokument_fixture(ident_cely="C-TX-PARA-001")
        cls.soubor = create_soubor_fixture(cls.dokument)

    def _row(self, **overrides):
        """Sestaví řádek importu ukazující na testovací soubor."""
        row = VALID_ROW.copy()
        row["path"] = self.soubor.path
        row.update(overrides)
        return row

    def _fedora(self, exists=True):
        """Nahradí dotaz do Fedory na existenci cílové distribuce pevnou odpovědí."""
        return patch.object(FedoraRepositoryConnector, "distribution_exists", return_value=exists)

    def test_implicit_distributions_are_checked_in_fedora(self):
        """I kontejnery vzniklé při importu souboru se ověřují ve Fedoře, kde na ně dosáhneme."""
        for distribution in ("orig", "thumb", "thumb-large"):
            with self.subTest(distribution=distribution):
                with patch.object(FedoraRepositoryConnector, "distribution_exists", return_value=True) as exists_mock:
                    result = ParadataMapper(self._row(distribution=distribution)).import_validation(INSERT)

                self.assertEqual(result, {"path": self.soubor.path})
                exists_mock.assert_called_once_with(self.soubor.repository_uuid, distribution)

    def test_missing_implicit_distribution_rejected(self):
        """Chybí-li ve Fedoře náhled, paradata k němu se odmítnou."""
        with self._fedora(exists=False):
            with self.assertRaises(DistribuceImportIntegrityError):
                ParadataMapper(self._row(distribution="thumb")).import_validation(INSERT)

    def test_alternative_distribution_must_exist(self):
        """Alternativní distribuce musí ve Fedoře existovat, jinak paradata nemají kam patřit."""
        with self._fedora(exists=False):
            with self.assertRaises(DistribuceImportIntegrityError):
                ParadataMapper(self._row(distribution="ocr/alto-xml")).import_validation(INSERT)

        with self._fedora(exists=True):
            self.assertEqual(
                ParadataMapper(self._row(distribution="ocr/alto-xml")).import_validation(INSERT),
                {"path": self.soubor.path},
            )

    def test_all_actions_check_only_target_distribution(self):
        """INSERT, UPDATE i DELETE ověřují shodně jen existenci cílové distribuce."""
        for action in (INSERT, UPDATE, DELETE):
            with self.subTest(action=action):
                row = (
                    {"path": self.soubor.path, "distribution": "orig"}
                    if action == DELETE
                    else self._row(distribution="orig")
                )
                with self._fedora(exists=True):
                    self.assertEqual(ParadataMapper(row).import_validation(action), {"path": self.soubor.path})

    def test_fedora_outage_propagates(self):
        """Nedostupná Fedora validaci zastaví místo tichého předpokladu o neexistenci."""
        with patch.object(
            FedoraRepositoryConnector,
            "distribution_exists",
            side_effect=FedoraNoResponseError("url", "No Fedora response", None),
        ):
            with self.assertRaises(FedoraNoResponseError):
                ParadataMapper(self._row()).import_validation(INSERT)

    def test_missing_soubor_rejected(self):
        """Neexistující cesta souboru se odmítne jako chybějící reference."""
        with self._fedora(exists=True):
            with self.assertRaises(ImportDataMissingReferencedValueError):
                ParadataMapper(self._row(path="rest/AMCR/record/C-TX-NEEXISTUJE/file/uuid")).import_validation(INSERT)

    def test_soubor_with_path_outside_fedora_rejected(self):
        """Soubor s cestou mimo Fedoru nemá UUID kontejneru a odmítne se už při validaci."""
        soubor = create_soubor_fixture(self.dokument, nazev="mimo.pdf", uuid="99999999-0000-0000-0000-000000000000")
        Soubor.objects.filter(pk=soubor.pk).update(path="mimo/fedoru/soubor.pdf")

        with patch.object(FedoraRepositoryConnector, "distribution_exists") as exists_mock:
            with self.assertRaises(DistribuceMissingRepositoryUuidError):
                ParadataMapper(self._row(path="mimo/fedoru/soubor.pdf")).import_validation(INSERT)
        exists_mock.assert_not_called()

    def test_duplicate_row_in_batch_rejected(self):
        """Táž dvojice (soubor, distribuce) se v jedné dávce nesmí opakovat."""
        seen: set = set()
        with self._fedora(exists=True):
            ParadataMapper(self._row()).import_validation(INSERT, seen_in_batch=seen)

            with self.assertRaises(DistribuceImportIntegrityError):
                ParadataMapper(self._row()).import_validation(INSERT, seen_in_batch=seen)

    def test_paradata_for_different_distributions_in_batch_pass(self):
        """Paradata k různým distribucím téhož souboru mohou být v jedné dávce."""
        seen: set = set()
        with self._fedora(exists=True):
            ParadataMapper(self._row(distribution="orig")).import_validation(INSERT, seen_in_batch=seen)
            ParadataMapper(self._row(distribution="thumb")).import_validation(INSERT, seen_in_batch=seen)

        self.assertEqual(len(seen), 2)


class ParadataMapperCreateRecordsTest(TestCase):
    """Testy přípravy záznamu paradat pro fázi importu."""

    @classmethod
    def setUpTestData(cls):
        """Vytvoří dokument a soubor, na který se importní řádek odkazuje."""
        cls.dokument = create_dokument_fixture(ident_cely="C-TX-PARA-004")
        cls.soubor = create_soubor_fixture(cls.dokument)

    def _row(self, **overrides):
        """Sestaví řádek importu ukazující na testovací soubor."""
        row = VALID_ROW.copy()
        row["path"] = self.soubor.path
        row.update(overrides)
        return row

    def test_returns_existing_soubor_with_transient_attributes(self):
        """create_records() vrátí existující soubor doplněný o přechodné atributy paradat."""
        records = ParadataMapper(self._row()).create_records(INSERT)

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.pk, self.soubor.pk)
        self.assertEqual(record.paradata_distribution, "orig")
        self.assertEqual(record.paradata_nazev, "paradata.json")
        self.assertEqual(record.paradata_mimetype, "application/json")
        self.assertEqual(record.paradata_performed_action, INSERT)

    def test_does_not_modify_database(self):
        """create_records() nesmí změnit databázový záznam souboru ani počet souborů."""
        pocet_pred = Soubor.objects.count()

        ParadataMapper(self._row(nazev="jina_paradata.json")).create_records(UPDATE)

        self.assertEqual(Soubor.objects.count(), pocet_pred)
        self.assertEqual(Soubor.objects.get(pk=self.soubor.pk).nazev, self.soubor.nazev)

    def test_delete_returns_soubor_without_deleting_it(self):
        """Ani DELETE nesmaže soubor – paradata se mažou jen ve Fedoře."""
        records = ParadataMapper({"path": self.soubor.path, "distribution": "orig"}).create_records(DELETE)

        self.assertEqual(records[0].pk, self.soubor.pk)
        self.assertTrue(Soubor.objects.filter(pk=self.soubor.pk).exists())


class ParadataMapperNoSideEffectTargetsTest(TestCase):
    """Testy, že paradata nezapisují historii ani neobnovují metadata záznamu."""

    @classmethod
    def setUpTestData(cls):
        """Vytvoří dokument a soubor pro dotazy na cíle historie a metadat."""
        cls.dokument = create_dokument_fixture(ident_cely="C-TX-PARA-005")
        cls.soubor = create_soubor_fixture(cls.dokument)

    def test_no_history_target(self):
        """Paradata se do historie nezapisují."""
        self.assertIsNone(ParadataMapper.get_record_history(self.soubor))

    def test_no_metadata_target(self):
        """Paradata nemění metadata záznamu, takže nevrací žádný cíl aktualizace."""
        self.assertEqual(ParadataMapper.fedora_update_targets(self.soubor), set())
