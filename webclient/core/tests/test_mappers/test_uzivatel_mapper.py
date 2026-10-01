from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    UzivatelMapper,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "ident_cely": "U-000001",
    "first_name": "Jan",
    "last_name": "Novák",
    "email": "jan.novak@test.cz",
    "telefon": "+420777000001",
    "orcid": None,
    "jazyk": "cs",
    "is_active": "true",
    "is_staff": "false",
    "is_superuser": "false",
    "date_joined": "2024-01-01T00:00:00Z",
    "last_login": None,
    "osoba": "OS-000001",
    "organizace": "ORG-T-001",
}


class UzivatelMapperInvalidStructureTest(TestCase):
    """Testy pro UzivatelMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = UzivatelMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci ident_cely."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = UzivatelMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_email_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci email."""
        row = VALID_ROW.copy()
        del row["email"]
        mapper = UzivatelMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = UzivatelMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_unknown_column_in_update_raises_error(self):
        """_check_column_structure() UPDATE vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = UzivatelMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper._check_column_structure(UPDATE, include_primary_key=True)


class UzivatelMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro UzivatelMapper.check_required_fields — bez DB."""

    def test_ident_cely_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely None (not null)."""
        row = VALID_ROW.copy()
        row["ident_cely"] = None
        mapper = UzivatelMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_email_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je email None (not null)."""
        row = VALID_ROW.copy()
        row["email"] = None
        mapper = UzivatelMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_orcid_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je orcid None (nullable pole)."""
        row = VALID_ROW.copy()
        row["orcid"] = None
        mapper = UzivatelMapper(row)
        mapper.check_required_fields(INSERT)

    def test_last_login_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je last_login None (nullable pole)."""
        row = VALID_ROW.copy()
        row["last_login"] = None
        mapper = UzivatelMapper(row)
        mapper.check_required_fields(INSERT)
