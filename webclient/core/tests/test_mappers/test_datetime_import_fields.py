"""Testy importních polí pro hodnoty ``date`` a ``datetime``."""

from core.import_data_mappers import DateImportField, DateTimeImportField, ImportDataError
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

    def test_value_setter_raises_error_for_invalid_date_format(self):
        """Ověřuje, že přiřazení neplatné hodnoty přes ``value`` setter vyvolá chybu."""
        field = DateImportField()

        with self.assertRaises(ImportDataError):
            field.value = "31/05/2026"


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
