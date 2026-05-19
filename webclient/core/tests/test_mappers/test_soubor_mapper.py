from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
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
