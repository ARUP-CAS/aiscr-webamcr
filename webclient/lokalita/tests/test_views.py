from arch_z.models import ArcheologickyZaznam
from core.tests.runner import (
    EXISTING_LOKALITA_IDENT,
    KATASTR_PRAHA_ID,
    LOKALITA_DRUH,
    LOKALITA_TYP_NEW,
    add_middleware_to_request,
)
from django.test import RequestFactory, TestCase
from django.utils.translation import gettext as _
from heslar.hesla import PRISTUPNOST_ANONYM_ID, PRISTUPNOST_ARCHEOLOG_ID
from uzivatel.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from lokalita.views import LokalitaDetailView


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")

    def test_get_lokalita_detail(self):
        request = self.factory.get("/arch_z/lokalita/detail/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request.session.save()

        response = LokalitaDetailView.as_view()(request, slug=EXISTING_LOKALITA_IDENT)
        self.assertEqual(200, response.status_code)

    def test_get_lokalita_vyber(self):
        self.client.force_login(self.existing_user)
        response = self.client.get("/arch-z/lokalita/vyber")
        self.assertEqual(200, response.status_code)

    def test_get_lokalita_zapsat(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(f"/arch-z/lokalita/zapsat")
        self.assertEqual(200, response.status_code)

    def test_post_zapsat(self):
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "hlavni_katastr": str(KATASTR_PRAHA_ID),
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
        response = self.client.post(f"/arch-z/lokalita/zapsat", data, follow=True)
        az = ArcheologickyZaznam.objects.filter(ident_cely="X-C-M0000001").first()
        az.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(az.lokalita.typ_lokality.pk, LOKALITA_TYP_NEW)
        self.assertEqual(az.pristupnost.pk, PRISTUPNOST_ANONYM_ID)
        self.assertTrue(
            len(ArcheologickyZaznam.objects.filter(ident_cely="X-C-M0000001")) == 1
        )

    def test_get_editovat(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(f"/arch-z/lokalita/edit/{EXISTING_LOKALITA_IDENT}")
        self.assertEqual(200, response.status_code)

    def test_post_editovat(self):
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "hlavni_katastr": "149",
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
        response = self.client.post(
            f"/arch-z/lokalita/edit/{EXISTING_LOKALITA_IDENT}", data, follow=True
        )
        az = ArcheologickyZaznam.objects.filter(
            ident_cely=EXISTING_LOKALITA_IDENT
        ).first()
        az.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(az.lokalita.typ_lokality.pk, LOKALITA_TYP_NEW)
        self.assertEqual(az.pristupnost.pk, PRISTUPNOST_ARCHEOLOG_ID)
        self.assertTrue(
            len(ArcheologickyZaznam.objects.filter(ident_cely=EXISTING_LOKALITA_IDENT))
            == 1
        )
