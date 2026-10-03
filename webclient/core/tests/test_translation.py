from unittest.mock import patch

from core.translation import format_message
from django.test import SimpleTestCase


class FormatMessageTest(SimpleTestCase):
    """Testy pro format_message — překlad celé věty se zástupnými znaky."""

    def test_translated_message_interpolates_params(self):
        """Přeložená věta dostane hodnoty do pojmenovaných zástupných znaků."""
        with patch("core.translation.gettext", return_value="Záznam {child} odkazuje na {parent}."):
            message = format_message("test.message", child="ORG-CHILD", parent="ORG-PARENT")
        self.assertEqual(message, "Záznam ORG-CHILD odkazuje na ORG-PARENT.")

    def test_untranslated_message_keeps_params(self):
        """Bez překladu se parametry připojí za ID, aby se informace neztratila."""
        with patch("core.translation.gettext", side_effect=lambda message_id: message_id):
            message = format_message("test.message", child="ORG-CHILD", parent="ORG-PARENT")
        self.assertEqual(message, "test.message child=ORG-CHILD parent=ORG-PARENT")

    def test_translation_with_unknown_placeholder_falls_back_to_text(self):
        """Překlad s neznámým zástupným znakem se vrátí bez dosazení místo pádu."""
        with patch("core.translation.gettext", return_value="Hodnota {neexistuje}."):
            message = format_message("test.message", child="ORG-CHILD")
        self.assertEqual(message, "Hodnota {neexistuje}.")

    def test_translation_with_positional_placeholder_falls_back_to_text(self):
        """Překlad s pozičním zástupným znakem (IndexError) se vrátí bez dosazení."""
        with patch("core.translation.gettext", return_value="Hodnota {0}."):
            message = format_message("test.message", child="ORG-CHILD")
        self.assertEqual(message, "Hodnota {0}.")
