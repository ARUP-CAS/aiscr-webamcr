from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    NeidentAkceMapper,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "dokument_cast": "DC-C-TX-000001-D01",
    "katastr": "999999",
    "rok_zahajeni": "2020",
    "rok_ukonceni": "2021",
    "lokalizace": "testovací lokalizace",
    "popis": "testovací popis",
    "poznamka": "testovací poznámka",
    "pian": None,
}


class NeidentAkceMapperInvalidStructureTest(TestCase):
    """Testy pro NeidentAkceMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = NeidentAkceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_rok_zahajeni_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci rok_zahajeni."""
        row = VALID_ROW.copy()
        del row["rok_zahajeni"]
        mapper = NeidentAkceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_katastr_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci katastr."""
        row = VALID_ROW.copy()
        del row["katastr"]
        mapper = NeidentAkceMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = NeidentAkceMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class NeidentAkceMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro NeidentAkceMapper.check_required_fields."""

    def test_dokument_cast_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je dokument_cast None (not null FK)."""
        row = VALID_ROW.copy()
        row["dokument_cast"] = None
        mapper = NeidentAkceMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_katastr_none_passes(self):
        """check_required_fields() nevyvolá chybu, pokud je katastr None (nullable FK)."""
        row = VALID_ROW.copy()
        row["katastr"] = None
        mapper = NeidentAkceMapper(row)
        mapper.check_required_fields(INSERT)

    def test_rok_zahajeni_none_passes(self):
        """check_required_fields() nevyvolá chybu, pokud je rok_zahajeni None (nullable pole)."""
        row = VALID_ROW.copy()
        row["rok_zahajeni"] = None
        mapper = NeidentAkceMapper(row)
        mapper.check_required_fields(INSERT)

    def test_rok_ukonceni_none_passes(self):
        """check_required_fields() nevyvolá chybu, pokud je rok_ukonceni None (nullable pole)."""
        row = VALID_ROW.copy()
        row["rok_ukonceni"] = None
        mapper = NeidentAkceMapper(row)
        mapper.check_required_fields(INSERT)

    def test_lokalizace_none_passes(self):
        """check_required_fields() nevyvolá chybu, pokud je lokalizace None (nullable pole)."""
        row = VALID_ROW.copy()
        row["lokalizace"] = None
        mapper = NeidentAkceMapper(row)
        mapper.check_required_fields(INSERT)

    def test_popis_none_passes(self):
        """check_required_fields() nevyvolá chybu, pokud je popis None (nullable pole)."""
        row = VALID_ROW.copy()
        row["popis"] = None
        mapper = NeidentAkceMapper(row)
        mapper.check_required_fields(INSERT)

    def test_poznamka_none_passes(self):
        """check_required_fields() nevyvolá chybu, pokud je poznamka None (nullable pole)."""
        row = VALID_ROW.copy()
        row["poznamka"] = None
        mapper = NeidentAkceMapper(row)
        mapper.check_required_fields(INSERT)

    def test_pian_none_passes(self):
        """check_required_fields() nevyvolá chybu, pokud je pian None (nullable pole)."""
        row = VALID_ROW.copy()
        row["pian"] = None
        mapper = NeidentAkceMapper(row)
        mapper.check_required_fields(INSERT)
