from django.test import TestCase
from heslar.hesla import PROJEKT_ZACHRANNY_ID
from projekt.models import Projekt


class TestProjektSignals(TestCase):
    def setUp(self):
        pass

    def test_create_projekt_vazby(self):
        p = Projekt(
            stav=0,
            typ_projektu=PROJEKT_ZACHRANNY_ID,
        )
        p.save()
        self.assertTrue(p.historie)
        self.assertTrue(p.soubory)
