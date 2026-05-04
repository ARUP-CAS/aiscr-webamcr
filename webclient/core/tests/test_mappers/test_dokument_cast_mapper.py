from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    DokumentCastMapper,
    ImportDataError,
    ImportDataIncorrectStructureError,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "ident_cely": "DC-C-TX-000001-D01",
    "poznamka": "testovací poznámka",
    "dokument": "C-TX-000001",
    "archeologicky_zaznam": None,
    "projekt": None,
}


class DokumentCastMapperInvalidStructureTest(TestCase):
    """Testy pro DokumentCastMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = DokumentCastMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím ident_cely (require_primary_key_value=True)."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = DokumentCastMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_dokument_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci dokument."""
        row = VALID_ROW.copy()
        del row["dokument"]
        mapper = DokumentCastMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = DokumentCastMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_update_missing_primary_key_raises_error(self):
        """map() UPDATE vyvolá ImportDataIncorrectStructureError při chybějícím primárním klíči ident_cely."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = DokumentCastMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(UPDATE, serialize=True, include_primary_key=True)


class DokumentCastMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro DokumentCastMapper.check_required_fields."""

    def test_ident_cely_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely None (not null pole)."""
        row = VALID_ROW.copy()
        row["ident_cely"] = None
        mapper = DokumentCastMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_dokument_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je dokument None (not null FK)."""
        row = VALID_ROW.copy()
        row["dokument"] = None
        mapper = DokumentCastMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_poznamka_none_passes(self):
        """check_required_fields() nevyvolá chybu, pokud je poznamka None (nullable pole)."""
        row = VALID_ROW.copy()
        row["poznamka"] = None
        mapper = DokumentCastMapper(row)
        mapper.check_required_fields(INSERT)

    def test_archeologicky_zaznam_none_passes(self):
        """check_required_fields() nevyvolá chybu, pokud je archeologicky_zaznam None (nullable FK)."""
        row = VALID_ROW.copy()
        row["archeologicky_zaznam"] = None
        mapper = DokumentCastMapper(row)
        mapper.check_required_fields(INSERT)

    def test_projekt_none_passes(self):
        """check_required_fields() nevyvolá chybu, pokud je projekt None (nullable FK)."""
        row = VALID_ROW.copy()
        row["projekt"] = None
        mapper = DokumentCastMapper(row)
        mapper.check_required_fields(INSERT)
