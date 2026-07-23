"""Testy importních polí pro hodnoty ``date``, ``datetime``, ``integer`` a generické FK."""

from unittest.mock import MagicMock

from core.import_data_mappers import (
    DateImportField,
    DateTimeImportField,
    GenericForeignKeyImportField,
    ImportDataError,
    IntegerImportField,
    PositiveIntegerImportField,
)
from django.test import SimpleTestCase
from django.utils import timezone


class DateImportFieldTest(SimpleTestCase):
    """Testy chování importního pole ``DateImportField`` při zpracování datových hodnot."""

    def test_accepts_iso_date_format(self):
        """Ověřuje, že pole přijme formát ``YYYY-MM-DD``."""
        field = DateImportField()

        field.value = "2026-05-31"

        self.assertEqual(field.serialized_value, "2026-05-31")

    def test_accepts_localized_date_format(self):
        """Ověřuje, že pole přijme formát ``DD.MM.YYYY``."""
        field = DateImportField()

        field.value = "31.05.2026"

        self.assertEqual(field.serialized_value, "2026-05-31")

    def test_strips_timestamp_from_iso_value(self):
        """Ověřuje, že čas u formátu ``YYYY-MM-DD HH:MM:SS`` se ignoruje."""
        field = DateImportField()

        field.value = "2026-05-31 13:45:59"

        self.assertEqual(field.serialized_value, "2026-05-31")

    def test_strips_timestamp_from_localized_value(self):
        """Ověřuje, že čas u formátu ``DD.MM.YYYY HH:MM:SS`` se ignoruje."""
        field = DateImportField()

        field.value = "31.05.2026 13:45:59"

        self.assertEqual(field.serialized_value, "2026-05-31")

    def test_strips_timestamp_from_dotted_year_first_value(self):
        """Ověřuje, že čas u formátu ``YYYY.M.D HH:MM:SS`` se ignoruje."""
        field = DateImportField()

        field.value = "2011.1.1 0:00:00"

        self.assertEqual(field.serialized_value, "2011-01-01")

    def test_value_setter_raises_error_for_invalid_date_format(self):
        """Ověřuje, že přiřazení neplatné hodnoty přes ``value`` setter vyvolá chybu."""
        field = DateImportField()

        with self.assertRaises(ImportDataError):
            field.value = "31/05/2026"

    def test_value_setter_wraps_invalid_calendar_date_as_import_error(self):
        """Ověřuje, že kalendářně neplatné datum vyvolá ImportDataError."""
        field = DateImportField()

        with self.assertRaises(ImportDataError):
            field.value = "2026-13-31 13:45:59"


class DateTimeImportFieldTest(SimpleTestCase):
    """Testy chování importního pole ``DateTimeImportField`` při zpracování hodnot s časem."""

    def test_accepts_iso_datetime_format(self):
        """Ověřuje, že pole přijme formát ``YYYY-MM-DD HH:MM:SS``."""
        field = DateTimeImportField()

        field.value = "2026-05-31 13:45:59"

        self.assertEqual(field.serialized_value, "2026-05-31 13:45:59")
        self.assertTrue(timezone.is_aware(field._value))

    def test_accepts_dotted_datetime_format(self):
        """Ověřuje, že pole přijme formát ``YYYY.MM.DD HH:MM:SS``."""
        field = DateTimeImportField()

        field.value = "2026.05.31 13:45:59"

        self.assertEqual(field.serialized_value, "2026-05-31 13:45:59")
        self.assertTrue(timezone.is_aware(field._value))

    def test_accepts_single_digit_dotted_datetime_format(self):
        """Ověřuje, že pole přijme formát ``YYYY.M.D H:MM:SS``."""
        field = DateTimeImportField()

        field.value = "2011.1.1 0:00:00"

        self.assertEqual(field.serialized_value, "2011-01-01 00:00:00")
        self.assertTrue(timezone.is_aware(field._value))

    def test_accepts_czech_datetime_format(self):
        """Ověřuje, že pole přijme formát ``DD.MM.YYYY HH:MM:SS``."""
        field = DateTimeImportField()

        field.value = "31.05.2026 13:45:59"

        self.assertEqual(field.serialized_value, "2026-05-31 13:45:59")
        self.assertTrue(timezone.is_aware(field._value))

    def test_value_setter_raises_error_for_invalid_datetime_format(self):
        """Ověřuje, že přiřazení neplatné hodnoty přes ``value`` setter vyvolá chybu."""
        field = DateTimeImportField()

        with self.assertRaises(ImportDataError):
            field.value = "31/05/2026 13:45:59"

    def test_value_setter_wraps_invalid_calendar_datetime_as_import_error(self):
        """Ověřuje, že kalendářně neplatný datetime vyvolá ImportDataError."""
        field = DateTimeImportField()

        with self.assertRaises(ImportDataError):
            field.value = "2026.13.31 13:45:59"


class IntegerImportFieldTest(SimpleTestCase):
    """Testy chování importního pole ``IntegerImportField``."""

    def test_positive_integer_parsed(self):
        """Kladné celé číslo je správně zpracováno."""
        field = IntegerImportField()
        field.value = "5000"
        self.assertEqual(field.value, 5000)

    def test_negative_integer_preserves_sign(self):
        """Záporné celé číslo si zachová znaménko (BCE data)."""
        field = IntegerImportField()
        field.value = "-5000"
        self.assertEqual(field.value, -5000)

    def test_negative_integer_as_int_input(self):
        """Záporné číslo zadané jako int je správně zpracováno."""
        field = IntegerImportField()
        field.value = -200
        self.assertEqual(field.value, -200)

    def test_none_returns_none(self):
        """None vstup vrátí None."""
        field = IntegerImportField()
        field.value = None
        self.assertIsNone(field.value)

    def test_invalid_value_raises_error(self):
        """Neplatná hodnota vyvolá ImportDataError."""
        field = IntegerImportField()
        with self.assertRaises(ImportDataError):
            field.value = "abc"

    def test_plain_integer_string_parsed(self):
        """Řetězec bez desetinné tečky (např. '4') se přijme jako int."""
        field = IntegerImportField()
        field.value = "4"
        self.assertEqual(field.value, 4)

    def test_float_string_x_dot_0_parsed_as_int(self):
        """'X.0' (pandas koerce celého čísla v nullable sloupci) se přijme jako int."""
        field = IntegerImportField()
        field.value = "5.0"
        self.assertEqual(field.value, 5)

    def test_negative_float_string_x_dot_0_parsed_as_int(self):
        """'-X.0' se přijme jako záporný int."""
        field = IntegerImportField()
        field.value = "-200.0"
        self.assertEqual(field.value, -200)

    def test_native_float_whole_number_parsed_as_int(self):
        """Nativní float s celou hodnotou (např. 5.0) se přijme jako int."""
        field = IntegerImportField()
        field.value = 5.0
        self.assertEqual(field.value, 5)

    def test_native_float_non_integer_raises_error(self):
        """Nativní float s desetinnou částí (např. 5.5) vyvolá ImportDataError."""
        field = IntegerImportField()
        with self.assertRaises(ImportDataError):
            field.value = 5.5


class PositiveIntegerImportFieldTest(SimpleTestCase):
    """Testy chování importního pole ``PositiveIntegerImportField``."""

    def test_positive_integer_parsed(self):
        """Kladné celé číslo je správně zpracováno."""
        field = PositiveIntegerImportField()
        field.value = "200"
        self.assertEqual(field.value, 200)

    def test_negative_integer_raises_error(self):
        """Záporné celé číslo vyvolá ImportDataError."""
        field = PositiveIntegerImportField()
        with self.assertRaises(ImportDataError):
            field.value = "-5000"

    def test_none_returns_none(self):
        """None vstup vrátí None."""
        field = PositiveIntegerImportField()
        field.value = None
        self.assertIsNone(field.value)

    def test_float_string_x_dot_0_parsed_as_int(self):
        """'X.0' se přijme jako kladný int."""
        field = PositiveIntegerImportField()
        field.value = "200.0"
        self.assertEqual(field.value, 200)

    def test_negative_float_string_raises_error(self):
        """'-X.0' vyvolá ImportDataError (záporná hodnota)."""
        field = PositiveIntegerImportField()
        with self.assertRaises(ImportDataError):
            field.value = "-200.0"


class GenericForeignKeyImportFieldSerializedValueTest(SimpleTestCase):
    """Testy pro ``GenericForeignKeyImportField.serialized_value`` — None-guard při chybějící instanci."""

    def test_none_instance_value_with_serialized_attribute_returns_none(self):
        """serialized_value vrátí None, pokud je _instance_value None a serialized_attribute je nastaveno."""
        field = GenericForeignKeyImportField(serialized_attribute="kod")
        field._instance_value = None
        self.assertIsNone(field.serialized_value)

    def test_valid_instance_value_returns_attribute(self):
        """serialized_value vrátí hodnotu atributu ze _instance_value, pokud instance existuje."""
        field = GenericForeignKeyImportField(serialized_attribute="kod")
        mock_instance = MagicMock()
        mock_instance.kod = "123456"
        field._instance_value = mock_instance
        self.assertEqual(field.serialized_value, "123456")

    def test_no_serialized_attribute_returns_raw_value(self):
        """Bez serialized_attribute vrátí serialized_value přímo _value (výchozí chování)."""
        field = GenericForeignKeyImportField()
        field._value = "raw-value"
        self.assertEqual(field.serialized_value, "raw-value")
