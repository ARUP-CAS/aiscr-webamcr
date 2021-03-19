from core.utils import calculate_crc_32, get_cadastre_from_point, get_mime_type
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
        latitude = 50.089616
        longitude = 14.417222
        praha_centrum = Point(longitude, latitude)
        katastr = get_cadastre_from_point(praha_centrum)
        self.assertEqual(katastr.nazev, "JOSEFOV")

    def test_calculate_crc_32(self):
        with open("core/tests/resources/mime.txt", "rb") as file:
            expected_checksum = "3775775224"  # For CRLF
            other_expected = "2455176644"  # For LF
            checksum = calculate_crc_32(file)
            one = checksum == expected_checksum
            two = checksum == other_expected
            self.assertTrue(one or two)
