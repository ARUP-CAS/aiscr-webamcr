from unittest.mock import patch

from core.translation import format_message
from django.template import Context, Engine
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


class TranslateFormatTagTest(SimpleTestCase):
    """Testy pro šablonový tag ``translate_format``."""

    def render(self, source, context=None):
        """
        Vykreslí šablonu s načtenou knihovnou ``template_tags``.

        :param source: Zdroj šablony.
        :param context: Slovník kontextu šablony.

            :return: Vrací vykreslený řetězec.
        """
        engine = Engine(libraries={"translation_tags": "core.templatetags.translation_tags"})
        return engine.from_string(source).render(Context(context or {}))

    def test_tag_interpolates_named_params(self):
        """Tag dosadí hodnoty do pojmenovaných zástupných znaků překladu."""
        with patch("core.translation.gettext", return_value="Záznam {child} odkazuje na {parent}."):
            rendered = self.render(
                '{% load translation_tags %}{% translate_format "test.message" child="ORG-CHILD" parent="ORG-PARENT" %}'
            )
        self.assertEqual(rendered, "Záznam ORG-CHILD odkazuje na ORG-PARENT.")

    def test_tag_keeps_html_from_translated_message(self):
        """HTML z překladu zůstane neescapované, protože katalog je důvěryhodný."""
        with patch("core.translation.gettext", return_value="<p>Pište na {mail}.</p>"):
            rendered = self.render(
                '{% load translation_tags %}{% translate_format "test.message" mail=mail %}',
                {"mail": "x@example.org"},
            )
        self.assertEqual(rendered, "<p>Pište na x@example.org.</p>")

    def test_tag_escapes_html_in_parameters(self):
        """HTML v hodnotě parametru se escapuje, stejně jako u nahrazeného blocktranslate."""
        with patch("core.translation.gettext", return_value="Pište na {mail}."):
            rendered = self.render(
                '{% load translation_tags %}{% translate_format "test.message" mail=mail %}',
                {"mail": '<a href="mailto:x@example.org">x@example.org</a>'},
            )
        self.assertEqual(
            rendered,
            "Pište na &lt;a href=&quot;mailto:x@example.org&quot;&gt;x@example.org&lt;/a&gt;.",
        )

    def test_tag_keeps_explicitly_safe_parameter(self):
        """Hodnota označená jako bezpečná se neescapuje, takže výjimku lze povolit explicitně."""
        with patch("core.translation.gettext", return_value="Pište na {mail}."):
            rendered = self.render(
                '{% load translation_tags %}{% translate_format "test.message" mail=mail|safe %}',
                {"mail": '<a href="mailto:x@example.org">x@example.org</a>'},
            )
        self.assertEqual(rendered, 'Pište na <a href="mailto:x@example.org">x@example.org</a>.')
