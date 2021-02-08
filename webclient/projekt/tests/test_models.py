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

    def test_parse_ident_cely(self):
        p = Projekt()
        self.assertEqual(p.parse_ident_cely(), (None, None, None, None))
        p.ident_cely = "X-M-202000001"
        self.assertEqual(p.parse_ident_cely(), (False, "M", "2020", "00001"))
        p.ident_cely = "C-201100001"
        self.assertEqual(p.parse_ident_cely(), (True, "C", "2011", "00001"))
        p.ident_cely = "M-2010100001"
        self.assertEqual(p.parse_ident_cely(), (True, "M", "2010", "100001"))
