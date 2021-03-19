from django.test import RequestFactory, TestCase
from heslar.views import RuianKatastrAutocomplete


class HeslarTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_heslar_katastr(self):
        request = self.factory.get("/heslar/katastr")
        response = RuianKatastrAutocomplete.as_view()(request, q="ODROVICE")
        self.assertEqual(200, response.status_code)
