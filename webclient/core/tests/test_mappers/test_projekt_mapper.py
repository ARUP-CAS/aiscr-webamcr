from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    DateRangeImportField,
    ImportDataError,
    ImportDataIncorrectStructureError,
    ProjektMapper,
)
from django.test import TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
UPDATE = ImportDataAdminForm.PERFORMED_ACTION_UPDATE

VALID_ROW = {
    "ident_cely": "C-202401-000001",
    "stav": "1",
    "lokalizace": "Pole za vsí",
    "parcelni_cislo": "1234/5",
    "geom": None,
    "geom_system": "wgs84",
    "geom_sjtsk": None,
    "podnet": None,
    "planovane_zahajeni": None,
    "uzivatelske_oznaceni": None,
    "oznaceni_stavby": None,
    "kulturni_pamatka_cislo": None,
    "kulturni_pamatka_popis": None,
    "datum_zahajeni": None,
    "datum_ukonceni": None,
    "termin_odevzdani_nz": None,
    "typ_projektu": "HES-PROJTYP-001",
    "hlavni_katastr": "123456",
    "vedouci_projektu": None,
    "organizace": None,
    "kulturni_pamatka": None,
}

MAP_SAFE_ROW = {
    "ident_cely": "C-202401-000001",
    "stav": "1",
    "lokalizace": "Pole za vsí",
    "parcelni_cislo": "1234/5",
    "geom": None,
    "geom_system": "wgs84",
    "geom_sjtsk": None,
    "podnet": None,
    "planovane_zahajeni": None,
    "uzivatelske_oznaceni": None,
    "oznaceni_stavby": None,
    "kulturni_pamatka_cislo": None,
    "kulturni_pamatka_popis": None,
    "datum_zahajeni": None,
    "datum_ukonceni": None,
    "termin_odevzdani_nz": None,
    "typ_projektu": None,
    "hlavni_katastr": None,
    "vedouci_projektu": None,
    "organizace": None,
    "kulturni_pamatka": None,
}


class ProjektMapperInvalidStructureTest(TestCase):
    """Testy pro ProjektMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = ProjektMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_ident_cely_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci ident_cely."""
        row = VALID_ROW.copy()
        del row["ident_cely"]
        mapper = ProjektMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_hlavni_katastr_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci hlavni_katastr."""
        row = VALID_ROW.copy()
        del row["hlavni_katastr"]
        mapper = ProjektMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = ProjektMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_unknown_column_in_update_raises_error(self):
        """_check_column_structure() UPDATE vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = ProjektMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper._check_column_structure(UPDATE, include_primary_key=True)


class ProjektMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro ProjektMapper.check_required_fields — bez DB."""

    def test_ident_cely_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je ident_cely None (not null)."""
        row = VALID_ROW.copy()
        row["ident_cely"] = None
        mapper = ProjektMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_stav_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je stav None (not null)."""
        row = VALID_ROW.copy()
        row["stav"] = None
        mapper = ProjektMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_lokalizace_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je lokalizace None (nullable pole)."""
        row = VALID_ROW.copy()
        row["lokalizace"] = None
        mapper = ProjektMapper(row)
        mapper.check_required_fields(INSERT)

    def test_vedouci_projektu_none_passes(self):
        """check_required_fields() projde bez výjimky, pokud je vedouci_projektu None (nullable FK)."""
        row = VALID_ROW.copy()
        row["vedouci_projektu"] = None
        mapper = ProjektMapper(row)
        mapper.check_required_fields(INSERT)


class ProjektMapperMapValidTest(TestCase):
    """Testy pro ProjektMapper — platný dataset pro map()."""

    def test_map_returns_dict(self):
        """map() vrátí slovník pro platný řádek."""
        mapper = ProjektMapper(MAP_SAFE_ROW.copy())
        result = mapper.map(INSERT, serialize=False, include_primary_key=True)
        self.assertIsInstance(result, dict)

    def test_map_includes_all_expected_keys(self):
        """map() vrátí všechny očekávané klíče."""
        mapper = ProjektMapper(MAP_SAFE_ROW.copy())
        result = mapper.map(INSERT, serialize=False, include_primary_key=True)
        expected_keys = set(MAP_SAFE_ROW.keys())
        self.assertEqual(set(result.keys()), expected_keys)

    def test_map_serialize_with_null_planovane_zahajeni_returns_none(self):
        """map(serialize=True) vrátí None pro planovane_zahajeni=None — nesmí selhat na AttributeError."""
        mapper = ProjektMapper(MAP_SAFE_ROW.copy())
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertIsNone(result["planovane_zahajeni"])

    def test_map_serialize_with_valid_planovane_zahajeni_returns_string(self):
        """map(serialize=True) vrátí řetězec ve formátu [YYYY-MM-DD,YYYY-MM-DD) pro platnou hodnotu."""
        row = MAP_SAFE_ROW.copy()
        row["planovane_zahajeni"] = "[2024-01-01, 2024-06-30)"
        mapper = ProjektMapper(row)
        result = mapper.map(INSERT, serialize=True, include_primary_key=True)
        self.assertEqual(result["planovane_zahajeni"], "[2024-01-01,2024-06-30)")


class DateRangeImportFieldSerializedValueTest(TestCase):
    """Jednotkové testy pro DateRangeImportField.serialized_value."""

    def test_none_value_returns_none(self):
        """serialized_value vrátí None, pokud je hodnota pole None."""
        field = DateRangeImportField()
        field.value = None
        self.assertIsNone(field.serialized_value)

    def test_valid_range_returns_formatted_string(self):
        """serialized_value vrátí správně formátovaný řetězec pro platný DateRange."""
        import datetime

        from django.db.backends.postgresql.psycopg_any import DateRange

        field = DateRangeImportField()
        field._value = DateRange(datetime.date(2024, 1, 1), datetime.date(2024, 6, 30))
        self.assertEqual(field.serialized_value, "[2024-01-01,2024-06-30)")
