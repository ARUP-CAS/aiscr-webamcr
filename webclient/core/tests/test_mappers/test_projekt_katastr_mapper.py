from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    ProjektKatastrMapper,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "projekt": "C-999999999",
    "katastr": "999999",
}


class ProjektKatastrMapperInvalidStructureTest(TestCase):
    """Testy pro ProjektKatastrMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = ProjektKatastrMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_projekt_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci projekt."""
        row = VALID_ROW.copy()
        del row["projekt"]
        mapper = ProjektKatastrMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_katastr_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci katastr."""
        row = VALID_ROW.copy()
        del row["katastr"]
        mapper = ProjektKatastrMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = ProjektKatastrMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class ProjektKatastrMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro ProjektKatastrMapper.check_required_fields."""

    def test_projekt_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je projekt None (not null FK)."""
        row = VALID_ROW.copy()
        row["projekt"] = None
        mapper = ProjektKatastrMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_katastr_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je katastr None (not null FK)."""
        row = VALID_ROW.copy()
        row["katastr"] = None
        mapper = ProjektKatastrMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
