from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    HistorieMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "datum_zmeny": "2024-01-01T10:00:00Z",
    "typ_zmeny": "ZAP",
    "poznamka": "test",
    "vazba": "C-AZ-999999999",
    "uzivatel": "U-000001",
}


class HistorieMapperInvalidStructureTest(TestCase):
    """Testy pro HistorieMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = HistorieMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_datum_zmeny_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci datum_zmeny."""
        row = VALID_ROW.copy()
        del row["datum_zmeny"]
        mapper = HistorieMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_typ_zmeny_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci typ_zmeny."""
        row = VALID_ROW.copy()
        del row["typ_zmeny"]
        mapper = HistorieMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_vazba_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci vazba."""
        row = VALID_ROW.copy()
        del row["vazba"]
        mapper = HistorieMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = HistorieMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_update_missing_id_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError, pokud chybí primární klíč id."""
        mapper = HistorieMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)


class HistorieMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro HistorieMapper.check_required_fields — bez DB."""

    def test_datum_zmeny_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je datum_zmeny None (not null)."""
        row = VALID_ROW.copy()
        row["datum_zmeny"] = None
        mapper = HistorieMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_typ_zmeny_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je typ_zmeny None (not null)."""
        row = VALID_ROW.copy()
        row["typ_zmeny"] = None
        mapper = HistorieMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_poznamka_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je poznamka None (nullable pole)."""
        row = VALID_ROW.copy()
        row["poznamka"] = None
        mapper = HistorieMapper(row)
        mapper.check_required_fields(INSERT)
