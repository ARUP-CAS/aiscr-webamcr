from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataIncorrectStructureError,
    UzivatelNotifikaceMapper,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT

VALID_ROW = {
    "uzivatel": "U-000001",
    "notifikace": "S-E-N-001",
}


class UzivatelNotifikaceMapperInvalidStructureTest(TestCase):
    """Testy pro UzivatelNotifikaceMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = UzivatelNotifikaceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_uzivatel_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci uzivatel."""
        row = VALID_ROW.copy()
        del row["uzivatel"]
        mapper = UzivatelNotifikaceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_notifikace_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci notifikace."""
        row = VALID_ROW.copy()
        del row["notifikace"]
        mapper = UzivatelNotifikaceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = UzivatelNotifikaceMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)
