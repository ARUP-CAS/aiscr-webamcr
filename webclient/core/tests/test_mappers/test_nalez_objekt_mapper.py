from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    NalezObjektMapper,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "pocet": "5",
    "poznamka": "test",
    "komponenta": "C-AZ-999999999-D01-K001",
    "druh": "HES-OBJDRUH-001",
    "specifikace": "HES-OBJSPEC-001",
}


class NalezObjektMapperInvalidStructureTest(TestCase):
    """Testy pro NalezObjektMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = NalezObjektMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_komponenta_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci komponenta."""
        row = VALID_ROW.copy()
        del row["komponenta"]
        mapper = NalezObjektMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_druh_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci druh."""
        row = VALID_ROW.copy()
        del row["druh"]
        mapper = NalezObjektMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = NalezObjektMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_update_missing_id_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError, pokud chybí primární klíč id."""
        mapper = NalezObjektMapper(VALID_ROW.copy())
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)


class NalezObjektMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro NalezObjektMapper.check_required_fields — bez DB."""

    def test_komponenta_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je komponenta None (not null FK)."""
        row = VALID_ROW.copy()
        row["komponenta"] = None
        mapper = NalezObjektMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_druh_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je druh None (not null FK)."""
        row = VALID_ROW.copy()
        row["druh"] = None
        mapper = NalezObjektMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_specifikace_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je specifikace None (nullable FK)."""
        row = VALID_ROW.copy()
        row["specifikace"] = None
        mapper = NalezObjektMapper(row)
        mapper.check_required_fields(INSERT)

    def test_pocet_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je pocet None (nullable pole)."""
        row = VALID_ROW.copy()
        row["pocet"] = None
        mapper = NalezObjektMapper(row)
        mapper.check_required_fields(INSERT)

    def test_poznamka_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je poznamka None (nullable pole)."""
        row = VALID_ROW.copy()
        row["poznamka"] = None
        mapper = NalezObjektMapper(row)
        mapper.check_required_fields(INSERT)
