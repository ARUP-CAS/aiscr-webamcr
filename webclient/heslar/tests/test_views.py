from django.test import RequestFactory, TestCase
from heslar.views import RuianKatastrAutocomplete, zjisti_vychozi_hodnotu


class HeslarTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_heslar_katastr(self):
        request = self.factory.get("/heslar/katastr")
        response = RuianKatastrAutocomplete.as_view()(request, q="ODROVICE")
        self.assertEqual(200, response.status_code)

    def test_get_initial_bad_request(self):
        request = self.factory.get("/heslat/zjisti-vychozi-hodnotu?nadrazene=400")
        response = zjisti_vychozi_hodnotu(request)
        self.assertEqual(400, response.status_code)

    def test_get_initial_value(self):
        request = self.factory.get("/heslat/zjisti-vychozi-hodnotu?nadrazene=200")
        response = zjisti_vychozi_hodnotu(request)
        self.assertContains(response=response, text="999", status_code=200)
