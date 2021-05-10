from core.tests.runner import KATASTR_ODROVICE_ID
from django.test import TestCase
from heslar.hesla import TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import Heslar, RuianKatastr
from projekt.models import Projekt


class TestProjektSignals(TestCase):
    def setUp(self):
        pass

    def test_create_projekt_vazby(self):
        p = Projekt(
            stav=0,
            typ_projektu=Heslar.objects.get(pk=TYP_PROJEKTU_ZACHRANNY_ID),
            hlavni_katastr=RuianKatastr.objects.get(id=KATASTR_ODROVICE_ID),
        )
        p.save()
        self.assertTrue(p.historie)
        self.assertTrue(p.soubory)
