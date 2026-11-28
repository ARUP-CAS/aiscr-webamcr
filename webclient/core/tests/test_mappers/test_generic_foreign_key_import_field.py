from core.import_data_mappers import GenericForeignKeyImportField, ImportDataError
from django.test import SimpleTestCase
from heslar.models import RuianKatastr, RuianKraj, RuianOkres


class GenericForeignKeyImportFieldTest(SimpleTestCase):
    """Testy zpracování hodnoty v ``GenericForeignKeyImportField`` s číselným vyhledávacím polem."""

    def test_non_numeric_value_raises_import_data_error(self):
        """Hodnota, kterou číselné pole ``kod`` odmítne, vyvolá chybu řádku místo pádu validace."""
        for value in ("abc", "ruian-12x", "ruian-"):
            with self.subTest(value=value):
                field = GenericForeignKeyImportField([RuianKatastr, RuianOkres, RuianKraj], "kod", "kod")
                with self.assertRaises(ImportDataError):
                    field.value = value
