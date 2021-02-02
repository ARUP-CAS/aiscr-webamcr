from datetime import datetime
from unittest.mock import patch

from django.test import TestCase
from projekt.models import Projekt, ProjektKatastr


class ProjectModelsTests(TestCase):
    def setUp(self):
        pass

    # Example how to mock call ProjektKatastr.objects.filter in the get_main_cadastre method
    @patch(
        "projekt.models.ProjektKatastr.objects.filter",
        return_value=ProjektKatastr.objects.none(),
    )
    def test_get_main_cadastre_empty(self, mock):
        main_cadastre = Projekt().get_main_cadastre()
        self.assertEqual(main_cadastre, None)

    def test_get_zahajeni(self):
        datum_zahajeni = Projekt.objects.get(ident_cely="C-202000001").get_zahajeni()
        self.assertEqual(datum_zahajeni.date(), datetime.now().date())

    def test_parse_ident_cely(self):
        p = Projekt()
        self.assertEqual(p.parse_ident_cely(), (None, None, None, None))
        p.ident_cely = "X-M-202000001"
        self.assertEqual(p.parse_ident_cely(), (False, "M", "2020", "00001"))
        p.ident_cely = "C-201100001"
        self.assertEqual(p.parse_ident_cely(), (True, "C", "2011", "00001"))
        p.ident_cely = "M-2010100001"
        self.assertEqual(p.parse_ident_cely(), (True, "M", "2010", "100001"))
