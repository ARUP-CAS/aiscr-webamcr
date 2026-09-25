from datetime import date, time
from unittest.mock import ANY, MagicMock, patch

from core.admin import OdstavkaSystemuAdmin
from core.forms import OdstavkaSystemuForm
from core.models import OdstavkaSystemu
from core.templatetags import template_tags
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.utils.translation import override


class OdstavkaSystemuModelTests(TestCase):
    """Ověřuje ukládání vícejazyčných textů odstávky do databáze."""

    def test_texts_are_persisted_in_the_database(self):
        """Kontroluje, že český a anglický text zůstanou po uložení beze změny."""
        outage = OdstavkaSystemu.objects.create(
            info_od=date(2026, 1, 1),
            datum_odstavky=date(2026, 1, 2),
            cas_odstavky=time(1, 2),
            text_cs="Česká zpráva",
            text_en="English message",
        )

        stored = OdstavkaSystemu.objects.get(pk=outage.pk)

        self.assertEqual(stored.text_cs, "Česká zpráva")
        self.assertEqual(stored.text_en, "English message")


class OdstavkaSystemuFormTests(TestCase):
    """Ověřuje inicializaci formuláře odstávky z textů modelu."""

    @patch("core.forms.BeautifulSoup")
    @patch("builtins.open")
    def test_form_uses_model_texts_instead_of_translation_catalog(self, mocked_open, mocked_soup):
        """Kontroluje, že formulář používá texty modelu místo překladového katalogu.

        :param mocked_open: Mock pro přístup k souborům s odstávkovými šablonami.
        :param mocked_soup: Mock parseru HTML šablon.
        """
        mocked_open.return_value.__enter__.return_value = MagicMock()
        mocked_soup.return_value.find.return_value = None
        outage = OdstavkaSystemu(
            info_od=date(2026, 1, 1),
            datum_odstavky=date(2026, 1, 2),
            cas_odstavky=time(1, 2),
            text_cs="Česká zpráva",
            text_en="English message",
        )

        form = OdstavkaSystemuForm(instance=outage)

        self.assertEqual(form.initial["text_cs"], "Česká zpráva")
        self.assertEqual(form.initial["text_en"], "English message")
        self.assertNotIn("django.po", str(mocked_open.call_args_list))


class OdstavkaSystemuAdminTests(TestCase):
    """Ověřuje ukládání odstávky prostřednictvím administrace."""

    @patch.object(OdstavkaSystemuAdmin, "file_handler")
    @patch("core.admin.cache.delete")
    def test_save_model_does_not_update_translation_catalog(self, cache_delete, file_handler):
        """Kontroluje uložení textů modelu, vyčištění cache a aktualizaci šablon.

        :param cache_delete: Mock vyčištění cache s odstávkou.
        :param file_handler: Mock aktualizace odstávkových šablon.
        """
        outage = OdstavkaSystemu(
            info_od=date(2026, 1, 1),
            datum_odstavky=date(2026, 1, 2),
            cas_odstavky=time(1, 2),
            text_cs="Česká zpráva",
            text_en="English message",
        )
        admin = OdstavkaSystemuAdmin(OdstavkaSystemu, MagicMock())

        admin.save_model(MagicMock(), outage, MagicMock(), change=False)

        stored = OdstavkaSystemu.objects.get(pk=outage.pk)
        self.assertEqual(stored.text_cs, "Česká zpráva")
        self.assertEqual(stored.text_en, "English message")
        cache_delete.assert_called_once_with("maintenance")
        file_handler.assert_any_call("cs", ANY)
        file_handler.assert_any_call("en", ANY)


class MaintenanceTemplateTests(TestCase):
    """Ověřuje vykreslení textu odstávky podle aktivního jazyka."""

    @override_settings(LANGUAGE_CODE="cs")
    @patch.object(template_tags, "get_set_maintenance_in_cache")
    def test_banner_uses_czech_model_text(self, get_maintenance):
        """Kontroluje, že české prostředí zobrazí český text odstávky.

        :param get_maintenance: Mock načtení aktuální odstávky z cache.
        """
        get_maintenance.return_value = OdstavkaSystemu(text_cs="Česká zpráva", text_en="English message")
        template = Template(
            "{% load i18n template_tags %}{% get_maintenance as action %}"
            "{% get_current_language as LANGUAGE_CODE %}"
            '{% if LANGUAGE_CODE == "en" %}{{ action.text_en }}{% else %}{{ action.text_cs }}{% endif %}'
        )

        with override("cs"):
            self.assertEqual(template.render(Context()), "Česká zpráva")

    @patch.object(template_tags, "get_set_maintenance_in_cache")
    def test_banner_uses_english_model_text(self, get_maintenance):
        """Kontroluje, že anglické prostředí zobrazí anglický text odstávky.

        :param get_maintenance: Mock načtení aktuální odstávky z cache.
        """
        get_maintenance.return_value = OdstavkaSystemu(text_cs="Česká zpráva", text_en="English message")
        template = Template(
            "{% load i18n template_tags %}{% get_maintenance as action %}"
            "{% get_current_language as LANGUAGE_CODE %}"
            '{% if LANGUAGE_CODE == "en" %}{{ action.text_en }}{% else %}{{ action.text_cs }}{% endif %}'
        )

        with override("en"):
            self.assertEqual(template.render(Context()), "English message")
