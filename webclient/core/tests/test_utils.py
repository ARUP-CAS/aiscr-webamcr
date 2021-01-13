from core.utils import get_mime_type
from django.test import TestCase


class UtilsTests(TestCase):
    def test_get_mime_type(self):
        txt = get_mime_type("mime.txt")
        pdf = get_mime_type("mime.pdf")
        csv = get_mime_type("mime.csv")

        self.assertEqual(txt, "text/plain")
        self.assertEqual(pdf, "application/pdf")
        self.assertEqual(csv, "text/csv")
