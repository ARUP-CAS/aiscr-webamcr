from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataIncorrectStructureContentObjectError,
    UzivatelNotifikaceProjektMapper,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW_IMPORT = {
    "uzivatel": "U-000001",
    "ruian": "123456",
}

VALID_ROW_JOB = {
    "uzivatel": "U-000001",
    "content_type": "ruian.ruiankatastr",
    "object_id": "123456",
}


class UzivatelNotifikaceProjektMapperInvalidStructureTest(TestCase):
    """Testy pro UzivatelNotifikaceProjektMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """_check_column_structure() vyvolá ImportDataIncorrectStructureContentObjectError při neznámém sloupci."""
        row = VALID_ROW_IMPORT.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = UzivatelNotifikaceProjektMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureContentObjectError):
            mapper._check_column_structure(INSERT)

    def test_missing_uzivatel_raises_error(self):
        """_check_column_structure() vyvolá ImportDataIncorrectStructureContentObjectError při chybějícím uzivatel."""
        row = {"ruian": "123456"}
        mapper = UzivatelNotifikaceProjektMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureContentObjectError):
            mapper._check_column_structure(INSERT)

    def test_missing_ruian_raises_error(self):
        """_check_column_structure() vyvolá ImportDataIncorrectStructureContentObjectError při chybějícím ruian."""
        row = {"uzivatel": "U-000001"}
        mapper = UzivatelNotifikaceProjektMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureContentObjectError):
            mapper._check_column_structure(INSERT)

    def test_empty_dict_raises_error(self):
        """_check_column_structure() vyvolá ImportDataIncorrectStructureContentObjectError pro prázdný slovník."""
        mapper = UzivatelNotifikaceProjektMapper({})
        with self.assertRaises(ImportDataIncorrectStructureContentObjectError):
            mapper._check_column_structure(INSERT)

    def test_valid_import_row_passes(self):
        """_check_column_structure() projde bez výjimky pro platný import formát (uzivatel + ruian)."""
        mapper = UzivatelNotifikaceProjektMapper(VALID_ROW_IMPORT.copy())
        mapper._check_column_structure(INSERT)

    def test_valid_job_row_passes(self):
        """_check_column_structure() projde bez výjimky pro platný job formát (uzivatel + content_type + object_id)."""
        mapper = UzivatelNotifikaceProjektMapper(VALID_ROW_JOB.copy())
        mapper._check_column_structure(INSERT)
