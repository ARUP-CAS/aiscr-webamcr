from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    PianMapper,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "ident_cely": "PIAN-C-000001",
    "stav": "1",
    "geom_system": "wgs84",
    "geom": None,
    "geom_sjtsk": None,
    "typ": "HES-PIANTYP-001",
    "presnost": "HES-PIANPRES-001",
    "zm10": "12345",
    "zm50": "6789",
}


class PianMapperInvalidStructureTest(TestCase):
    """Testy pro PianMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = PianMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci ident_cely."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = PianMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_geom_system_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci geom_system."""
        row = VALID_ROW.copy()
        del row["geom_system"]
        mapper = PianMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = PianMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_unknown_column_in_update_raises_error(self):
        """_check_column_structure() UPDATE vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = PianMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper._check_column_structure(UPDATE, include_primary_key=True)


class PianMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro PianMapper.check_required_fields — bez DB."""

    def test_ident_cely_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely None (not null)."""
        row = VALID_ROW.copy()
        row["ident_cely"] = None
        mapper = PianMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_typ_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je typ None (not null FK)."""
        row = VALID_ROW.copy()
        row["typ"] = None
        mapper = PianMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_geom_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je geom None (not null pole)."""
        row = VALID_ROW.copy()
        row["geom"] = None
        mapper = PianMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)
