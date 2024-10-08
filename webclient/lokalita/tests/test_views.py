import re

from arch_z.models import ArcheologickyZaznam
from core.tests.runner import EXISTING_LOKALITA_IDENT, LOKALITA_DRUH, LOKALITA_TYP_NEW
from django.test import TestCase
from django.urls import reverse
from heslar.hesla_dynamicka import PRISTUPNOST_ANONYM_ID, PRISTUPNOST_ARCHEOLOG_ID
from heslar.models import RuianKatastr
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")

    def test_get_lokalita_detail(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("lokalita:detail", kwargs={"slug": EXISTING_LOKALITA_IDENT}))
        self.assertEqual(200, response.status_code)

    def test_get_lokalita_vyber(self):
        self.client.force_login(self.existing_user)
        response = self.client.get("/arch-z/lokalita/vyber")
        self.assertEqual(200, response.status_code)

    def test_get_lokalita_zapsat(self):
        self.client.force_login(self.existing_user)
        response = self.client.get("/arch-z/lokalita/zapsat")
        self.assertEqual(200, response.status_code)

    def test_post_zapsat(self):
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "hlavni_katastr": str(RuianKatastr.objects.filter(nazev="JOSEFOV").first().pk),
            "typ_lokality": str(LOKALITA_TYP_NEW),
            "druh": str(LOKALITA_DRUH),
            "uzivatelske_oznaceni": "",
            "nazev": "nazev lokality",
            "zachovalost": "",
            "jistota": "",
            "pristupnost": str(PRISTUPNOST_ANONYM_ID),
            "popis": "",
            "poznamka": "",
        }
        self.client.force_login(self.existing_user)
        response = self.client.post("/arch-z/lokalita/zapsat", data, follow=True)
        response_text = str(response.rendered_content)
        regex = re.compile(r"\w-\w-\w{10}")
        ident_cely = regex.findall(response_text)[0]
        az = ArcheologickyZaznam.objects.filter(ident_cely=ident_cely).first()
        self.assertEqual(200, response.status_code)
        self.assertEqual(az.lokalita.typ_lokality.pk, LOKALITA_TYP_NEW)
        self.assertEqual(az.pristupnost.pk, PRISTUPNOST_ANONYM_ID)
        self.assertEqual(len(ArcheologickyZaznam.objects.filter(ident_cely=ident_cely)), 1)

    def test_get_editovat(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(f"/arch-z/lokalita/edit/{EXISTING_LOKALITA_IDENT}")
        self.assertEqual(200, response.status_code)

    def test_post_editovat(self):
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "hlavni_katastr": str(RuianKatastr.objects.filter(nazev="JOSEFOV").first().pk),
            "typ_lokality": str(LOKALITA_TYP_NEW),
            "druh": str(LOKALITA_DRUH),
            "uzivatelske_oznaceni": "",
            "nazev": "nazev",
            "zachovalost": "",
            "jistota": "",
            "pristupnost": str(PRISTUPNOST_ARCHEOLOG_ID),
            "popis": "",
            "poznamka": "",
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(f"/arch-z/lokalita/edit/{EXISTING_LOKALITA_IDENT}", data, follow=True)
        az = ArcheologickyZaznam.objects.filter(ident_cely=EXISTING_LOKALITA_IDENT).first()
        az.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(az.lokalita.typ_lokality.pk, LOKALITA_TYP_NEW)
        self.assertEqual(az.pristupnost.pk, PRISTUPNOST_ARCHEOLOG_ID)
        self.assertTrue(len(ArcheologickyZaznam.objects.filter(ident_cely=EXISTING_LOKALITA_IDENT)) == 1)
