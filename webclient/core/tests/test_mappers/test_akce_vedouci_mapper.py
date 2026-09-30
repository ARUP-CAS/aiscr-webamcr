from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    AkceVedouciMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "akce": "C-AZ-999999999",
    "vedouci": "OS-000001",
    "organizace": "ORG-T-999",
}


class AkceVedouciMapperInvalidStructureTest(TestCase):
    """Testy pro AkceVedouciMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = AkceVedouciMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_akce_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci akce."""
        row = VALID_ROW.copy()
        del row["akce"]
        mapper = AkceVedouciMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_vedouci_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci vedouci."""
        row = VALID_ROW.copy()
        del row["vedouci"]
        mapper = AkceVedouciMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_organizace_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci organizace."""
        row = VALID_ROW.copy()
        del row["organizace"]
        mapper = AkceVedouciMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = AkceVedouciMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class AkceVedouciMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro AkceVedouciMapper.check_required_fields."""

    def test_akce_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je akce None (not null FK)."""
        row = VALID_ROW.copy()
        row["akce"] = None
        mapper = AkceVedouciMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_vedouci_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je vedouci None (not null FK)."""
        row = VALID_ROW.copy()
        row["vedouci"] = None
        mapper = AkceVedouciMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_organizace_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je organizace None (not null FK)."""
        row = VALID_ROW.copy()
        row["organizace"] = None
        mapper = AkceVedouciMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
