from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    ProjektOznamovatelMapper,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "projekt": "C-999999999",
    "oznamovatel": "Testovací oznamovatel",
    "odpovedna_osoba": "Jan Novák",
    "adresa": "Testovací adresa 1",
    "telefon": "+420123456789",
    "email": "test@example.com",
    "poznamka": "testovací poznámka",
}


class ProjektOznamovatelMapperInvalidStructureTest(TestCase):
    """Testy pro ProjektOznamovatelMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = ProjektOznamovatelMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_oznamovatel_raises_error_2(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci (druhý případ)."""
        row = VALID_ROW.copy()
        del row["adresa"]
        mapper = ProjektOznamovatelMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_oznamovatel_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci oznamovatel."""
        row = VALID_ROW.copy()
        del row["oznamovatel"]
        mapper = ProjektOznamovatelMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_email_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci email."""
        row = VALID_ROW.copy()
        del row["email"]
        mapper = ProjektOznamovatelMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = ProjektOznamovatelMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class ProjektOznamovatelMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro ProjektOznamovatelMapper.check_required_fields."""

    def test_projekt_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je projekt None (not null FK)."""
        row = VALID_ROW.copy()
        row["projekt"] = None
        mapper = ProjektOznamovatelMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_poznamka_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je poznamka None (nullable pole)."""
        row = VALID_ROW.copy()
        row["poznamka"] = None
        mapper = ProjektOznamovatelMapper(row)
        mapper.check_required_fields(INSERT)
