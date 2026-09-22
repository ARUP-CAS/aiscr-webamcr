from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ArcheologickyZaznamKatastrMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "archeologicky_zaznam": "C-AZ-999999999",
    "katastr": "999999",
}


class ArcheologickyZaznamKatastrMapperInvalidStructureTest(TestCase):
    """Testy pro ArcheologickyZaznamKatastrMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = ArcheologickyZaznamKatastrMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_archeologicky_zaznam_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci archeologicky_zaznam."""
        row = VALID_ROW.copy()
        del row["archeologicky_zaznam"]
        mapper = ArcheologickyZaznamKatastrMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_katastr_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci katastr."""
        row = VALID_ROW.copy()
        del row["katastr"]
        mapper = ArcheologickyZaznamKatastrMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = ArcheologickyZaznamKatastrMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class ArcheologickyZaznamKatastrMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro ArcheologickyZaznamKatastrMapper.check_required_fields."""

    def test_archeologicky_zaznam_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je archeologicky_zaznam None (not null FK)."""
        row = VALID_ROW.copy()
        row["archeologicky_zaznam"] = None
        mapper = ArcheologickyZaznamKatastrMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_katastr_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je katastr None (not null FK)."""
        row = VALID_ROW.copy()
        row["katastr"] = None
        mapper = ArcheologickyZaznamKatastrMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
