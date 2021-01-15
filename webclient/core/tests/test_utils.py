from core.utils import get_cadastre_from_point, get_mime_type
from django.contrib.gis.geos import Point
from django.test import TestCase


class UtilsTests(TestCase):
    def test_get_mime_type(self):
        txt = get_mime_type("mime.txt")
        pdf = get_mime_type("mime.pdf")
        csv = get_mime_type("mime.csv")

        self.assertEqual(txt, "text/plain")
        self.assertEqual(pdf, "application/pdf")
        self.assertEqual(csv, "text/csv")

    def test_get_cadastre_from_point(self):

        praha_centrum = Point(50.086872, 14.417970)
        katastr = get_cadastre_from_point(praha_centrum)
        self.assertEqual(katastr, None)
