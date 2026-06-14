from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectStructureError,
    KomponentaMapper,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "ident_cely": "C-AZ-999999999-D01-K001",
    "jistota": "true",
    "presna_datace": "středověk",
    "poznamka": "test",
    "vazba": "C-AZ-999999999-D01",
    "obdobi": "HES-OBDOBI-001",
    "areal": "HES-AREAL-001",
}

MAP_SAFE_ROW = {
    "ident_cely": "C-AZ-999999999-D01-K001",
    "jistota": "true",
    "presna_datace": "středověk",
    "poznamka": "test",
    "vazba": None,
    "obdobi": None,
    "areal": None,
}


class KomponentaMapperInvalidStructureTest(TestCase):
    """Testy pro KomponentaMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = KomponentaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci ident_cely."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = KomponentaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_vazba_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci vazba."""
        row = VALID_ROW.copy()
        del row["vazba"]
        mapper = KomponentaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = KomponentaMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_unknown_column_in_update_raises_error(self):
        """_check_column_structure() UPDATE vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = KomponentaMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper._check_column_structure(UPDATE, include_primary_key=True)


class KomponentaMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro KomponentaMapper.check_required_fields — bez DB."""

    def test_ident_cely_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely None (not null)."""
        row = VALID_ROW.copy()
        row["ident_cely"] = None
        mapper = KomponentaMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_poznamka_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je poznamka None (nullable pole)."""
        row = VALID_ROW.copy()
        row["poznamka"] = None
        mapper = KomponentaMapper(row)
        mapper.check_required_fields(INSERT)

    def test_obdobi_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je obdobi None (nullable FK)."""
        row = VALID_ROW.copy()
        row["obdobi"] = None
        mapper = KomponentaMapper(row)
        mapper.check_required_fields(INSERT)


class KomponentaMapperMapValidTest(TestCase):
    """Testy pro KomponentaMapper — platný dataset pro map()."""

    def test_map_returns_dict(self):
        """map() vrátí slovník pro platný řádek."""
        mapper = KomponentaMapper(MAP_SAFE_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_includes_all_expected_keys(self):
        """map() vrátí všechny očekávané klíče."""
        mapper = KomponentaMapper(MAP_SAFE_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        expected_keys = {"ident_cely", "jistota", "presna_datace", "poznamka", "vazba", "obdobi", "areal"}
        self.assertEqual(set(result.keys()), expected_keys)
