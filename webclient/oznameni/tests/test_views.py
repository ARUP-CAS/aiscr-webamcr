import json

from core.tests.runner import EXISTING_PROJECT_IDENT_ZACHRANNY
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse
from oznameni.models import Oznamovatel
from oznameni.views import index, post_poi2kat
from projekt.models import Projekt
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")

    def test_get_index(self):
        request = self.factory.get("/oznameni/")
        request.user = AnonymousUser()

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
            "latitude": "50.089616",
            "longitude": "14.417222",
        }
        request = self.factory.post("/oznameni/", data)
        request.user = AnonymousUser()
        response = index(request, test_run=True)
        self.assertEqual(200, response.status_code)
        self.assertTrue("error" not in response.content.decode("utf-8"))

    def test_post_poi2kat(self):
        josefov = (14.417222, 50.089616)
        request = self.factory.post(
            "/oznameni/get-katastr-from-point",
            {"corY": josefov[0], "corX": josefov[1]},
            content_type="application/json",
        )
        request.user = AnonymousUser()
        response = post_poi2kat(request)
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        self.assertEqual(data["cadastre"], "JOSEFOV (Praha)")

    def test_get_add_oznamovatel(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            reverse(
                "projekt:pridat-oznamovatele",
                kwargs={"ident_cely": EXISTING_PROJECT_IDENT_ZACHRANNY},
            )
        )
        self.assertEqual(200, response.status_code)

    def test_post_add_oznamovatel(self):
        stav = Projekt.objects.get(ident_cely=EXISTING_PROJECT_IDENT_ZACHRANNY).stav
        data = {
            "csrfmiddlewaretoken": "27ZVK57GOldButY8IAxsDdqBlpUtsWBcpykJT7DgTENfOsy7uqkfoSoYWkbXmcu2",
            "old_stav": str(stav),
            "oznamovatel": "Janko Hrasko",
            "odpovedna_osoba": "Matus Macko",
            "adresa": "Praha",
            "telefon": "+420555666777",
            "email": "email@email.cz",
        }
        oznamovatel_count = Oznamovatel.objects.count()
        self.client.force_login(self.existing_user)
        response = self.client.post(
            reverse(
                "projekt:pridat-oznamovatele",
                kwargs={"ident_cely": EXISTING_PROJECT_IDENT_ZACHRANNY},
            ),
            data,
        )
        new_oznamovatel_count = Oznamovatel.objects.count()
        self.assertEqual(200, response.status_code)
        self.assertEqual(oznamovatel_count + 1, new_oznamovatel_count)
