from unittest.mock import MagicMock, patch

from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    SouborImportIntegrityError,
    SouborMapper,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "nazev": "dokument.pdf",
    "vazba": "C-AZ-999999999",
}


class SouborMapperInvalidStructureTest(TestCase):
    """Testy pro SouborMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = SouborMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_nazev_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci nazev."""
        row = VALID_ROW.copy()
        del row["nazev"]
        mapper = SouborMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_vazba_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci vazba."""
        row = VALID_ROW.copy()
        del row["vazba"]
        mapper = SouborMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = SouborMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_update_missing_id_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError, pokud chybí primární klíč id."""
        mapper = SouborMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)


class SouborMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro SouborMapper.check_required_fields — bez DB."""

    def test_nazev_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je nazev None (not null pole)."""
        row = VALID_ROW.copy()
        row["nazev"] = None
        mapper = SouborMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)


class SouborMapperImportValidationSeenInBatchTest(TestCase):
    """Testy pro SouborMapper.import_validation — detekce duplikátů v rámci jedné dávky."""

    def _make_mapper(self, nazev, vazba_pk):
        """Vytvoří SouborMapper s namockovaným map() vracejícím daný nazev a SouborVazby s daným pk."""
        mock_vazba = MagicMock()
        mock_vazba.pk = vazba_pk
        mapper = SouborMapper(VALID_ROW.copy())
        mapper.map = MagicMock(return_value={"nazev": nazev, "vazba": mock_vazba})
        return mapper

    @patch("core.import_data_mappers.Soubor.objects")
    def test_first_occurrence_returns_dict_and_adds_to_batch(self, mock_objects):
        """import_validation() INSERT vrátí slovník a přidá klíč do seen_in_batch.

        :param mock_objects: Mock pro ``Soubor.objects`` simulující prázdnou DB.
        """
        mock_objects.filter.return_value.exists.return_value = False
        seen = set()
        result = self._make_mapper("test.pdf", 1).import_validation(INSERT, seen_in_batch=seen)
        self.assertIsInstance(result, dict)
        self.assertIn(("test.pdf", 1), seen)

    @patch("core.import_data_mappers.Soubor.objects")
    def test_duplicate_in_batch_raises_integrity_error(self, mock_objects):
        """import_validation() INSERT vyvolá SouborImportIntegrityError pro druhý řádek se shodným nazev+vazba.

        :param mock_objects: Mock pro ``Soubor.objects`` simulující prázdnou DB.
        """
        mock_objects.filter.return_value.exists.return_value = False
        seen = set()
        self._make_mapper("test.pdf", 1).import_validation(INSERT, seen_in_batch=seen)
        with self.assertRaises(SouborImportIntegrityError):
            self._make_mapper("test.pdf", 1).import_validation(INSERT, seen_in_batch=seen)

    @patch("core.import_data_mappers.Soubor.objects")
    def test_same_name_different_vazba_does_not_raise(self, mock_objects):
        """import_validation() INSERT nehlásí chybu pro shodný nazev s jinou vazbou.

        :param mock_objects: Mock pro ``Soubor.objects`` simulující prázdnou DB.
        """
        mock_objects.filter.return_value.exists.return_value = False
        seen = set()
        self._make_mapper("test.pdf", 1).import_validation(INSERT, seen_in_batch=seen)
        result = self._make_mapper("test.pdf", 2).import_validation(INSERT, seen_in_batch=seen)
        self.assertIsInstance(result, dict)

    @patch("core.import_data_mappers.Soubor.objects")
    def test_seen_in_batch_none_skips_batch_check(self, mock_objects):
        """import_validation() INSERT s seen_in_batch=None nevyvolá chybu ani pro shodné řádky.

        :param mock_objects: Mock pro ``Soubor.objects`` simulující prázdnou DB.
        """
        mock_objects.filter.return_value.exists.return_value = False
        self._make_mapper("test.pdf", 1).import_validation(INSERT, seen_in_batch=None)
        result = self._make_mapper("test.pdf", 1).import_validation(INSERT, seen_in_batch=None)
        self.assertIsInstance(result, dict)
