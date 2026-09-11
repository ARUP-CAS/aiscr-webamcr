from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    AdbMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "ident_cely": "C-AZ-999999999-D01-ADB",
    "uzivatelske_oznaceni_sondy": "S-001",
    "trat": "Trať A",
    "cislo_popisne": "42",
    "parcelni_cislo": "1234",
    "stratigraficke_jednotky": "5",
    "rok_popisu": "2023",
    "rok_revize": "2024",
    "poznamka": "test",
    "dokumentacni_jednotka": "C-AZ-999999999-D01",
    "typ_sondy": "HES-ADBT-001",
    "podnet": "HES-ADBP-001",
    "autor_popisu": "OS-000001",
    "autor_revize": "OS-000002",
    "sm5": "12345",
}


class AdbMapperInvalidStructureTest(TestCase):
    """Testy pro AdbMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = AdbMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci ident_cely."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = AdbMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_dokumentacni_jednotka_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci dokumentacni_jednotka."""
        row = VALID_ROW.copy()
        del row["dokumentacni_jednotka"]
        mapper = AdbMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = AdbMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_unknown_column_in_update_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["id"] = "adb-1"
        row["neznamy_sloupec"] = "hodnota"
        mapper = AdbMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper._check_column_structure(UPDATE, include_primary_key=True)


class AdbMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro AdbMapper.check_required_fields — bez DB."""

    def test_ident_cely_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely None (not null)."""
        row = VALID_ROW.copy()
        row["ident_cely"] = None
        mapper = AdbMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_dokumentacni_jednotka_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je dokumentacni_jednotka None (not null FK)."""
        row = VALID_ROW.copy()
        row["dokumentacni_jednotka"] = None
        mapper = AdbMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_poznamka_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je poznamka None (nullable pole)."""
        row = VALID_ROW.copy()
        row["poznamka"] = None
        mapper = AdbMapper(row)
        mapper.check_required_fields(INSERT)

    def test_typ_sondy_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je typ_sondy None (nullable FK)."""
        row = VALID_ROW.copy()
        row["typ_sondy"] = None
        mapper = AdbMapper(row)
        mapper.check_required_fields(INSERT)
