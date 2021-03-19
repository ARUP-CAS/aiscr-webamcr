from core.tests.runner import (
    AMCR_TESTOVACI_ORGANIZACE_ID,
    ARCHEOLOGICKY_POSUDEK_ID,
    JAZYK_DOKUMENTU_CESTINA_ID,
    MATERIAL_DOKUMENTU_DIGI_SOUBOR,
    TYP_DOKUMENTU_PLAN_SONDY_ID,
    add_middleware_to_request,
)
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from dokument.models import Dokument
from dokument.views import detail, edit
from heslar.hesla import PRISTUPNOST_ANONYM_ID
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")
        self.existing_dokument = "C-TX-201501985"

    def test_get_detail(self):
        request = self.factory.get("/dokument/detail/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = detail(request, ident_cely=self.existing_dokument)
        self.assertEqual(200, response.status_code)

    def test_get_edit(self):
        request = self.factory.get("/dokument/edit/")
        request = add_middleware_to_request(request, SessionMiddleware)
        request.user = self.existing_user
        request.session.save()

        response = edit(request, ident_cely=self.existing_dokument)
        self.assertEqual(200, response.status_code)

    def test_post_edit(self):
        data = {
            "csrfmiddlewaretoken": "OxkETGL2ZdGqjVIqmDUxCYQccG49OOmBe6OMsT3Tz0OQqZlnT2AIBkdtNyL8yOMm",
            "organizace": str(AMCR_TESTOVACI_ORGANIZACE_ID),
            "rok_vzniku": "2019",
            "material_originalu": str(MATERIAL_DOKUMENTU_DIGI_SOUBOR),
            "typ_dokumentu": str(TYP_DOKUMENTU_PLAN_SONDY_ID),
            "pristupnost": str(PRISTUPNOST_ANONYM_ID),
            "datum_zverejneni": "",
            "jazyky": str(JAZYK_DOKUMENTU_CESTINA_ID),
            "posudky": str(ARCHEOLOGICKY_POSUDEK_ID),
            "save": "Upravit",
        }
        request = self.factory.post("/dokument/edit/", data)
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = edit(request, self.existing_dokument)
        self.assertEqual(200, response.status_code)
        self.assertTrue("error" not in response.content.decode("utf-8"))
        self.assertTrue(
            Dokument.objects.get(ident_cely=self.existing_dokument).rok_vzniku == 2019
        )
