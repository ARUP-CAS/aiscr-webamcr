from core.forms import ImportDataAdminForm
from core.import_data_mappers import (
    ImportDataError,
    ImportDataIncorrectPrimaryKeyFormatError,
    ImportDataIncorrectStructureError,
    ImportModelMapper,
    ProjektKatastrMapper,
)
from django.test import SimpleTestCase, TestCase

INSERT = ImportDataAdminForm.PERFORMED_ACTION_INSERT
DELETE = ImportDataAdminForm.PERFORMED_ACTION_DELETE

VALID_ROW = {
    "projekt": "C-999999999",
    "katastr": "999999",
}


class ProjektKatastrMapperInvalidStructureTest(TestCase):
    """Testy pro ProjektKatastrMapper — neplatná struktura dat."""

    def test_unknown_column_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při neznámém sloupci."""
        row = VALID_ROW.copy()
        row["neznamy_sloupec"] = "hodnota"
        mapper = ProjektKatastrMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_projekt_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci projekt."""
        row = VALID_ROW.copy()
        del row["projekt"]
        mapper = ProjektKatastrMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_missing_katastr_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError při chybějícím sloupci katastr."""
        row = VALID_ROW.copy()
        del row["katastr"]
        mapper = ProjektKatastrMapper(row)
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)

    def test_empty_dict_raises_error(self):
        """map() vyvolá ImportDataIncorrectStructureError pro prázdný slovník."""
        mapper = ProjektKatastrMapper({})
        with self.assertRaises(ImportDataIncorrectStructureError):
            mapper.map(INSERT, serialize=True, include_primary_key=True)


class ProjektKatastrMapperCheckRequiredFieldsTest(TestCase):
    """Testy pro ProjektKatastrMapper.check_required_fields."""

    def test_projekt_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je projekt None (not null FK)."""
        row = VALID_ROW.copy()
        row["projekt"] = None
        mapper = ProjektKatastrMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)

    def test_katastr_none_raises_error(self):
        """check_required_fields() vyvolá ImportDataError, pokud je katastr None (not null FK)."""
        row = VALID_ROW.copy()
        row["katastr"] = None
        mapper = ProjektKatastrMapper(row)
        with self.assertRaises(ImportDataError):
            mapper.check_required_fields(INSERT)


class ParsePrimaryKeyCustomPrefixTest(SimpleTestCase):
    """Jednotkové testy pro ``ImportModelMapper._parse_primary_key_custom_prefix``."""

    def test_valid_value_with_prefix_returns_integer(self):
        """Hodnota ve formátu ``{prefix}-{číslo}`` vrátí odpovídající celé číslo."""
        result = ImportModelMapper._parse_primary_key_custom_prefix("ruian-123456", "ruian")
        self.assertEqual(result, 123456)

    def test_malformed_value_raises_incorrect_primary_key_format_error(self):
        """Hodnota neodpovídající formátu ``{prefix}-{číslo}`` vyvolá ImportDataIncorrectPrimaryKeyFormatError."""
        with self.assertRaises(ImportDataIncorrectPrimaryKeyFormatError) as ctx:
            ImportModelMapper._parse_primary_key_custom_prefix("wrong-format", "ruian")
        self.assertEqual(ctx.exception.primary_key_value, "wrong-format")

    def test_malformed_value_error_message_contains_value(self):
        """Zpráva výjimky obsahuje chybnou hodnotu primárního klíče."""
        with self.assertRaises(ImportDataIncorrectPrimaryKeyFormatError) as ctx:
            ImportModelMapper._parse_primary_key_custom_prefix("neplatna-hodnota", "ruian")
        self.assertIn("neplatna-hodnota", str(ctx.exception))

    def test_value_without_any_prefix_passes_through(self):
        """Pokud je prefix None nebo prázdný, hodnota se vrátí beze změny."""
        self.assertEqual(ImportModelMapper._parse_primary_key_custom_prefix("123456", None), "123456")
        self.assertEqual(ImportModelMapper._parse_primary_key_custom_prefix("123456", ""), "123456")

    def test_non_string_value_without_prefix_passes_through(self):
        """Číselná hodnota bez prefixu se vrátí beze změny."""
        self.assertEqual(ImportModelMapper._parse_primary_key_custom_prefix(123456, None), 123456)

    def test_completely_missing_separator_raises_error(self):
        """Hodnota bez oddělovače ``-`` vyvolá ImportDataIncorrectPrimaryKeyFormatError."""
        with self.assertRaises(ImportDataIncorrectPrimaryKeyFormatError):
            ImportModelMapper._parse_primary_key_custom_prefix("ruian123456", "ruian")
