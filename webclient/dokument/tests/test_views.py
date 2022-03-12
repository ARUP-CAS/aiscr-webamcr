import logging

from core.constants import D_STAV_ODESLANY
from core.message_constants import DOKUMENT_NELZE_ARCHIVOVAT
from core.tests.runner import (
    AMCR_TESTOVACI_ORGANIZACE_ID,
    ARCHEOLOGICKY_POSUDEK_ID,
    JAZYK_DOKUMENTU_CESTINA_ID,
    MATERIAL_DOKUMENTU_DIGI_SOUBOR_ID,
    TYP_DOKUMENTU_PLAN_SONDY_ID,
    ZACHOVALOST_30_80_ID,
    add_middleware_to_request, EL_CHEFE_ID, ARCHIV_ARUB,
    TESTOVACI_DOKUMENT_IDENT,
)
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from dokument.models import Dokument
from dokument.views import archivovat, create_model_3D, detail, edit, odeslat
from heslar.hesla import PRISTUPNOST_ANONYM_ID
from heslar.models import Heslar
from uzivatel.models import User

logger = logging.getLogger(__name__)


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")
        self.existing_dokument = TESTOVACI_DOKUMENT_IDENT

    def test_get_detail(self):
        request = self.factory.get("/dokument/detail/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = detail(request, ident_cely=self.existing_dokument)
        self.assertEqual(200, response.status_code)

    def test_get_create_model3D(self):
        request = self.factory.get("/dokument/create/model")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = create_model_3D(request)
        self.assertEqual(200, response.status_code)

    def test_get_edit(self):
        request = self.factory.get("/dokument/edit/")
        request = add_middleware_to_request(request, SessionMiddleware)
        request.user = self.existing_user
        request.session.save()

        response = edit(request, ident_cely=self.existing_dokument)
        self.assertEqual(200, response.status_code)

    def test_get_change_states(self):
        requestA = self.factory.get("/dokument/archivovat/")
        requestA = add_middleware_to_request(requestA, SessionMiddleware)
        requestA = add_middleware_to_request(requestA, MessageMiddleware)
        requestA.user = self.existing_user
        requestA.session.save()
        # Dokument je ve spatnem stavu
        with self.assertRaises(PermissionDenied, msg=""):
            archivovat(requestA, ident_cely=self.existing_dokument)
        request = self.factory.get("/dokument/odeslat/")
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.user = self.existing_user
        request.session.save()
        # Dokument lze odeslat
        response = odeslat(request, ident_cely=self.existing_dokument)
        self.assertEqual(200, response.status_code)

        data = {
            "csrfmiddlewaretoken": "OxkETGL2ZdGqjVIqmDUxCYQccG49OOmBe6OMsT3Tz0OQqZlnT2AIBkdtNyL8yOMm",
        }
        request = self.factory.post("/dokument/odeslat/", data)
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.user = self.existing_user
        request.session.save()
        # Stav se zmeni na odeslany
        response = odeslat(request, ident_cely=self.existing_dokument)
        self.assertEqual(302, response.status_code)
        self.assertEqual(
            Dokument.objects.get(ident_cely=self.existing_dokument).stav,
            D_STAV_ODESLANY,
        )
        # Nejde archivovat protoze neni prilozen soubor
        response = archivovat(requestA, ident_cely=self.existing_dokument)
        self.assertEqual(200, response.status_code)
        self.assertTrue(DOKUMENT_NELZE_ARCHIVOVAT in response.content.decode("utf-8"))

    def test_post_edit(self):
        data = {
            "csrfmiddlewaretoken": "OxkETGL2ZdGqjVIqmDUxCYQccG49OOmBe6OMsT3Tz0OQqZlnT2AIBkdtNyL8yOMm",
            "organizace": str(AMCR_TESTOVACI_ORGANIZACE_ID),
            "rok_vzniku": "2019",
            "material_originalu": str(MATERIAL_DOKUMENTU_DIGI_SOUBOR_ID),
            "typ_dokumentu": str(TYP_DOKUMENTU_PLAN_SONDY_ID),
            "pristupnost": str(PRISTUPNOST_ANONYM_ID),
            "datum_zverejneni": "",
            "jazyky": str(JAZYK_DOKUMENTU_CESTINA_ID),
            "posudky": str(ARCHEOLOGICKY_POSUDEK_ID),
            "duveryhodnost": "10",
            "zachovalost": str(ZACHOVALOST_30_80_ID),
            "popis": "test",
            "licence": "test",
            "ulozeni_originalu": str(ARCHIV_ARUB),
            "autori": str(EL_CHEFE_ID),

        }
        request = self.factory.post("/dokument/edit/", data)
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = edit(request, self.existing_dokument)
        self.assertEqual(302, response.status_code)
        updated_dokument = Dokument.objects.get(ident_cely=self.existing_dokument)
        logger.debug("Zachovalost: " + str(updated_dokument.extra_data.zachovalost))
        self.assertTrue(
            updated_dokument.rok_vzniku == 2019
            and updated_dokument.extra_data.zachovalost
            == Heslar.objects.get(id=ZACHOVALOST_30_80_ID)
        )
