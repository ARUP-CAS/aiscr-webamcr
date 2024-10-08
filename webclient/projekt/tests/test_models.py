from core.constants import OBLAST_CECHY, OBLAST_MORAVA
from django.test import TestCase
from projekt.models import Projekt


class ProjectModelsTests(TestCase):
    def setUp(self):
        pass

    def test_parse_ident_cely(self):
        p = Projekt()
        self.assertEqual(p.parse_ident_cely(), (None, None, None, None))
        p.ident_cely = "X-M-202000001"
        self.assertEqual(p.parse_ident_cely(), (False, OBLAST_MORAVA, "2020", "00001"))
        p.ident_cely = "C-201100001"
        self.assertEqual(p.parse_ident_cely(), (True, OBLAST_CECHY, "2011", "00001"))
        p.ident_cely = "M-2010100001"
        self.assertEqual(p.parse_ident_cely(), (True, OBLAST_MORAVA, "2010", "100001"))

    def test_check_pred_uzavrenim(self):
        pass
        # TODO napsat test na check projektu pred uzavrenim
