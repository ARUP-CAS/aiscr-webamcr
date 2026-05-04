from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataIncorrectStructureError,
    UzivatelOpravneniMapper,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "uzivatel": "U-000001",
    "skupina": "archeolog",
}


class UzivatelOpravneniMapperInvalidStructureTest(TestCase):
    """Testy pro UzivatelOpravneniMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = UzivatelOpravneniMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_uzivatel_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci uzivatel."""
        row = VALID_ROW.copy()
        del row["uzivatel"]
        mapper = UzivatelOpravneniMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_skupina_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci skupina."""
        row = VALID_ROW.copy()
        del row["skupina"]
        mapper = UzivatelOpravneniMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = UzivatelOpravneniMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)
