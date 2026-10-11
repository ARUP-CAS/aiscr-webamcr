"""
Testy nabídky autorů a editorů ve formuláři externího zdroje (issue #4291).

Našeptávací widget vykresluje jen vybrané hodnoty a popisek k nim hledá ve svých volbách. Testy
hlídají, že se po neúspěšné validaci zobrazí jména osob, ne jejich čísla. Databáze se nepoužívá –
dotazy do ní jsou nahrazeny mockem.
"""

from unittest import mock

from django.http import QueryDict
from django.test import SimpleTestCase


class NabidkaOsobExterniZdrojTest(SimpleTestCase):
    """Testy naplnění nabídky polí ``autori`` a ``editori`` v :class:`ez.forms.ExterniZdrojForm`."""

    def test_odeslane_hodnoty_dostanou_jmena(self):
        """Po odeslání formuláře se pro zadané autory i editory nabídnou jejich jména, ne čísla."""
        from ez.forms import ExterniZdrojForm

        data = QueryDict(mutable=True)
        data.setlist("autori", ["31146", "30958"])
        data.setlist("editori", ["30958"])
        manager = mock.MagicMock()
        manager.filter.return_value.values_list.return_value = [(30958, "Absolon, A."), (31146, "Abrahám, Milan")]
        with mock.patch("dokument.forms.Osoba.objects", manager):
            form = ExterniZdrojForm(data)
        self.assertEqual(form.fields["autori"].widget.choices, [(31146, "Abrahám, Milan"), (30958, "Absolon, A.")])
        self.assertEqual(form.fields["editori"].widget.choices, [(30958, "Absolon, A.")])

    def test_nabidky_plni_sdileny_pomocnik(self):
        """Obě pole plní sdílený pomocník s vazbou a pořadím autorů, resp. editorů externího zdroje."""
        from ez import forms

        with mock.patch.object(forms, "nastav_nabidku_osob") as nastav:
            forms.ExterniZdrojForm(readonly=True)
        form = nastav.call_args_list[0].args[0]
        self.assertEqual(
            [volani.args for volani in nastav.call_args_list],
            [
                (form, "autori", "externizdrojautor__externi_zdroj", "externizdrojautor__poradi"),
                (form, "editori", "externizdrojeditor__externi_zdroj", "externizdrojeditor__poradi"),
            ],
        )
