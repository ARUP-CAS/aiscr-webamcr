from core.import_data_mappers import ImportDataError, RuianLookupImportField
from django.test import SimpleTestCase
from heslar.models import RuianKatastr


class RuianLookupImportFieldTest(SimpleTestCase):
    """Testy převodu hodnoty ``ruian-<kód>`` v ``RuianLookupImportField``."""

    def test_invalid_value_raises_import_data_error(self):
        """Hodnota, která nemá přesně tvar ``ruian-<číslice>``, vyvolá chybu řádku místo pádu validace."""
        for value in ("MISSING-REFERENCE-1", "ruian-", "ruian-12x", "123"):
            with self.subTest(value=value):
                field = RuianLookupImportField(RuianKatastr, "kod")
                with self.assertRaises(ImportDataError):
                    field.value = value
