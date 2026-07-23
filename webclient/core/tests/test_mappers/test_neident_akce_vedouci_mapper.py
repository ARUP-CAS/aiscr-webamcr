from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    NeidentAkceVedouciMapper,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "neident_akce": "DC-C-TX-000001-D01",
    "vedouci": "OS-000001",
}


class NeidentAkceVedouciMapperInvalidStructureTest(TestCase):
    """Testy pro NeidentAkceVedouciMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = NeidentAkceVedouciMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_neident_akce_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci neident_akce."""
        row = VALID_ROW.copy()
        del row["neident_akce"]
        mapper = NeidentAkceVedouciMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_vedouci_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci vedouci."""
        row = VALID_ROW.copy()
        del row["vedouci"]
        mapper = NeidentAkceVedouciMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = NeidentAkceVedouciMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class NeidentAkceVedouciMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro NeidentAkceVedouciMapper.check_required_fields."""

    def test_neident_akce_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je neident_akce None (not null FK)."""
        row = VALID_ROW.copy()
        row["neident_akce"] = None
        mapper = NeidentAkceVedouciMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_vedouci_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je vedouci None (not null FK)."""
        row = VALID_ROW.copy()
        row["vedouci"] = None
        mapper = NeidentAkceVedouciMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
