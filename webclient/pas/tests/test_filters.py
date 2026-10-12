"""
Testy filtru samostatných nálezů (``pas.filters``).
"""

from crispy_forms.layout import Div
from django.test import SimpleTestCase
from pas.filters import SamostatnyNalezFilter, SamostatnyNalezFilterFormHelper
from pas.models import SamostatnyNalez
from uzivatel.models import Organizace


def pole_layoutu(layout):
    """
    Vrátí názvy polí vykreslených v layoutu (rekurzivně přes vnořené ``Div``).

    :param layout: Layout nebo jeho prvek.

        :return: Množina názvů polí.
    """
    nazvy = set()
    for prvek in layout.fields:
        if isinstance(prvek, str):
            nazvy.add(prvek)
        elif isinstance(prvek, Div):
            nazvy |= pole_layoutu(prvek)
    return nazvy


class SamostatnyNalezFilterOrganizaceTest(SimpleTestCase):
    """Filtr ``organizace_nalezu`` pro odkaz „Potvrdit“ (issue #4199)."""

    def test_organizace_nalezu_filtruje_projekt_i_predano_organizace(self):
        """Podmínka musí pokrýt organizaci projektu i cílovou organizaci nálezu."""
        organizace = Organizace(pk=315755)
        qs = SamostatnyNalezFilter.filter_organizace_nalezu(
            None, SamostatnyNalez.objects.all(), "organizace_nalezu", [organizace]
        )
        sql = str(qs.query)
        self.assertIn('"projekt"."organizace" IN (315755)', sql)
        self.assertIn('"samostatny_nalez"."predano_organizace" IN (315755)', sql)
        self.assertIn(" OR ", sql)

    def test_organizace_nalezu_prazdna_hodnota_nefiltruje(self):
        """Nevyplněné pole (prázdný QuerySet z ``ModelMultipleChoiceField``) nesmí výsledky zúžit."""
        qs = SamostatnyNalez.objects.all()
        for prazdna in (Organizace.objects.none(), []):
            vysledek = SamostatnyNalezFilter.filter_organizace_nalezu(None, qs, "organizace_nalezu", prazdna)
            self.assertIs(vysledek, qs)

    def test_layout_obsahuje_pole_organizaci(self):
        """Pole musí být ve formuláři, jinak se podmínka při úpravě filtru ztratí z dotazu."""
        nazvy = pole_layoutu(SamostatnyNalezFilterFormHelper().layout)
        self.assertIn("projekt_organizace", nazvy)
        self.assertIn("organizace_nalezu", nazvy)
