from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    AdbVyskovyBod,
    ImportDataError,
    ImportDataIncorrectStructureError,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "ident_cely": "C-AZ-999999999-D01-ADB-V001",
    "geom": "POINT(0 0 0)",
    "adb": "C-AZ-999999999-D01-ADB",
    "typ": "HES-VBOD-001",
}


class AdbVyskovyBodInvalidStructureTest(TestCase):
    """Testy pro AdbVyskovyBod — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = AdbVyskovyBod(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci ident_cely."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = AdbVyskovyBod(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_adb_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci adb."""
        row = VALID_ROW.copy()
        del row["adb"]
        mapper = AdbVyskovyBod(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = AdbVyskovyBod({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_unknown_column_in_update_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["id"] = "vbod-1"
        row["neznamy_sloupec"] = "hodnota"
        mapper = AdbVyskovyBod(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper._check_column_structure(UPDATE, include_primary_key=True)


class AdbVyskovyBodCheckRequiredFieldsTest(TestCase):
    """Testy pro AdbVyskovyBod.check_required_fields — bez DB."""

    def test_ident_cely_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely None (not null)."""
        row = VALID_ROW.copy()
        row["ident_cely"] = None
        mapper = AdbVyskovyBod(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_adb_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je adb None (not null FK)."""
        row = VALID_ROW.copy()
        row["adb"] = None
        mapper = AdbVyskovyBod(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_typ_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je typ None (not null FK)."""
        row = VALID_ROW.copy()
        row["typ"] = None
        mapper = AdbVyskovyBod(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
