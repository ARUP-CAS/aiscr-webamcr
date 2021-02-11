import json

from django.test import RequestFactory, TestCase
from oznameni.views import index, post_poi2kat


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_index(self):
        request = self.factory.get("/oznameni/")

        response = index(request)
        self.assertEqual(200, response.status_code)

    def test_post_index(self):
        data = {
            "oznamovatel": "Tester",
            "odpovedna_osoba": "Někdo s Ř ve jméně",
            "adresa": "Moje adresa /25",
            "telefon": "722803058",
            "email": "jurajskvarla@yahoo.com",
            "katastralni_uzemi": "VYSOČANY (Hlavní město Praha)",
            "planovane_zahajeni": "21.01.2021 - 21.01.2021",
            "podnet": "Musime kopat",
            "lokalizace": "U nas na zahrade",
            "parcelni_cislo": "123",
            "oznaceni_stavby": "Zahrada A",
            "souhlas": "on",
            "g-recaptcha-response": "03AGdBq27IRpUJzEs-legIVY7uue3HQ",
            "latitude": "50.106212483846356",
            "longitude": "14.496384859085085",
        }
        request = self.factory.post("/oznameni/", data)
        response = index(request)
        self.assertEqual(200, response.status_code)
        self.assertTrue("error" not in response.content.decode("utf-8"))

    def test_post_poi2kat(self):
        josefov = (14.417222, 50.089616)
        request = self.factory.post(
            "/oznameni/get-katastr-from-point",
            {"corY": josefov[0], "corX": josefov[1]},
            content_type="application/json",
        )
        response = post_poi2kat(request)
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(data["cadastre"], "JOSEFOV")
