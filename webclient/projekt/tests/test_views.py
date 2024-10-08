import logging

from core.constants import SN_ZAPSANY
from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse
from heslar.hesla_dynamicka import PRISTUPNOST_ANONYM_ID, TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import Heslar, RuianKatastr
from oznameni.models import Oznamovatel
from pas.models import SamostatnyNalez
from projekt.models import Projekt
from uzivatel.models import User

logger = logging.getLogger("tests")


class UrlTests(TestCase):
    def setUp(self):
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")
        self.lokace_zahradky = Point(50.40, 15.70)
        self.projekt = Projekt(
            typ_projektu=Heslar.objects.get(id=TYP_PROJEKTU_ZACHRANNY_ID),
            ident_cely="M-202212541",
            lokalizace="Je to na zahradce",
            geom=self.lokace_zahradky,
            hlavni_katastr=RuianKatastr.objects.filter(nazev="ODROVICE").first(),
        )
        self.projekt.save()
        self.oznamovatel = Oznamovatel(
            email="tester@example.com",
            adresa="Nekde 123",
            odpovedna_osoba="Juraj Skvarla",
            oznamovatel="Juraj Skvarla",
            telefon="+420874521325",
            projekt=self.projekt,
        )
        self.oznamovatel.save()

    def test_get_detail_not_found(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("projekt:detail", kwargs={"ident_cely": "XXXXX"}))
        self.assertEqual(404, response.status_code)

    def test_get_detail_found(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("projekt:detail", kwargs={"ident_cely": self.projekt.ident_cely}))
        self.assertEqual(200, response.status_code)

    def test_edit_get_success(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("projekt:edit", kwargs={"ident_cely": self.projekt.ident_cely}))
        self.assertEqual(200, response.status_code)

    def test_edit_post_success(self):
        nova_lokalizace = "Neni to na zahradce"

        data = {
            "lokalizace": nova_lokalizace,
            "csrfmiddlewaretoken": "NYrbj266E2EKwDd9FQ5Nj4mtBRqnxhkWdxVjSfoXePMaDHQ6cfLYiqJKcJ7mhhKH",
            "typ_projektu": str(TYP_PROJEKTU_ZACHRANNY_ID),
            "hlavni_katastr": str(RuianKatastr.objects.filter(nazev="ODROVICE").first().pk),
            "planovane_zahajeni": "13.03.2021 - 21.03.2021",
            "podnet": "Trutnov knn pro p. č. 1865/4, IV-12-2020648",
            "parcelni_cislo": "1865/4, 2327/1",
            "oznaceni_stavby": "",
            "latitude": "50.55115833751426",
            "longitude": "15.89662240600137",
            "datum_zahajeni": "20.11.2020",
            "datum_ukonceni": "28.11.2020",
            "save": "Upravit",
        }

        self.client.force_login(self.existing_user)
        response = self.client.post(reverse("projekt:edit", kwargs={"ident_cely": self.projekt.ident_cely}), data)
        projekt = Projekt.objects.get(ident_cely=self.projekt.ident_cely)
        self.assertEqual(302, response.status_code)
        self.assertTrue("error" not in response.content.decode("utf-8"))
        self.assertTrue(projekt.lokalizace == nova_lokalizace)
        self.assertTrue(projekt.geom.coords != self.lokace_zahradky.coords)

    def test_get_smazat_check(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("projekt:smazat", kwargs={"ident_cely": self.projekt.ident_cely}))
        self.assertEqual(200, response.status_code)

    def test_get_smazat_samostatny_nalez_check(self):
        # Add samostatny nalez
        nalez = SamostatnyNalez(
            projekt=self.projekt,
            pristupnost=Heslar.objects.get(id=PRISTUPNOST_ANONYM_ID),
            stav=SN_ZAPSANY,
        )
        nalez.save()

        # Client is used there to follow redirect
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("projekt:smazat", kwargs={"ident_cely": self.projekt.ident_cely}))
        self.assertEqual(403, response.status_code)

    def test_post_create_success(self):
        data = {
            "csrfmiddlewaretoken": "NYrbj266E2EKwDd9FQ5Nj4mtBRqnxhkWdxVjSfoXePMaDHQ6cfLYiqJKcJ7mhhKH",
            "typ_projektu": str(TYP_PROJEKTU_ZACHRANNY_ID),
            "hlavni_katastr": str(RuianKatastr.objects.filter(nazev="ODROVICE").first().pk),
            "planovane_zahajeni": "13.03.2021 - 21.03.2021",
            "podnet": "Tralala",
            "lokalizace": "Helelelle",
            "parcelni_cislo": 123,
            "oznamovatel": "Nekdo",
            "odpovedna_osoba": "Nekdo jiny",
            "adresa": "123 street",
            "telefon": "+420587456321",
            "email": "tester@tester.tester",
            "old_stav": 0,
        }
        self.client.force_login(self.existing_user)

        projects_before = Projekt.objects.all().count()
        response = self.client.post(reverse("projekt:create"), data)
        projects_after = Projekt.objects.all().count()
        self.assertEqual(302, response.status_code)
        self.assertTrue("error" not in response.content.decode("utf-8"))
        self.assertTrue(projects_before < projects_after)

    def test_get_create_success(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("projekt:create"))
        self.assertEqual(200, response.status_code)
