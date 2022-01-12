from arch_z.models import ArcheologickyZaznam
from arch_z.views import detail, odeslat, pripojit_dokument, vratit, zapsat
from core.tests.runner import (
    EL_CHEFE_ID,
    EXISTING_DOCUMENT_ID,
    EXISTING_EVENT_IDENT,
    HLAVNI_TYP_SONDA_ID,
    KATASTR_ODROVICE_ID,
    add_middleware_to_request,
)
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from dokument.models import Dokument
from heslar.hesla import PRISTUPNOST_ANONYM_ID
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_projekt_ident = "C-202000001"
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")

    def test_get_detail(self):
        request = self.factory.get("/arch_z/detail/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request.session.save()

        response = detail(request, EXISTING_EVENT_IDENT)
        self.assertEqual(200, response.status_code)

    def test_get_zapsat(self):
        request = self.factory.get("/arch_z/zapsat/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request.session.save()

        response = zapsat(request, self.existing_projekt_ident)
        self.assertEqual(200, response.status_code)

    def test_post_zapsat(self):
        data = {
            "csrfmiddlewaretoken": "27ZVK57GOldButY8IAxsDdqBlpUtsWBcpykJT7DgTENfOsy7uqkfoSoYWkbXmcu2",
            "hlavni_katastr": str(KATASTR_ODROVICE_ID),
            "pristupnost": str(PRISTUPNOST_ANONYM_ID),
            "uzivatelske_oznaceni": "",
            "hlavni_vedouci": str(EL_CHEFE_ID),
            "datum_zahajeni": "15.11.2020",
            "datum_ukonceni": "15.12.2020",
            "specifikace_data": 885,
            "lokalizace_okolnosti": "Nekde proste to je",
            "ulozeni_nalezu": "",
            "hlavni_typ": str(HLAVNI_TYP_SONDA_ID),
            "vedlejsi_typ": "",
        }
        request = self.factory.post("/arch_z/zapsat/", data)
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = zapsat(request, self.existing_projekt_ident)
        self.assertEqual(302, response.status_code)
        self.assertTrue("error" not in response.content.decode("utf-8"))
        self.assertTrue(
            len(ArcheologickyZaznam.objects.filter(ident_cely="C-202000001B")) == 1
        )

    def test_get_odeslat(self):
        request = self.factory.get("/arch_z/odeslat/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = odeslat(request, EXISTING_EVENT_IDENT)
        self.assertEqual(200, response.status_code)

    def test_get_vratit(self):
        request = self.factory.get("/arch_z/vratit/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()
        with self.assertRaises(PermissionDenied, msg=""):
            vratit(request, ident_cely=EXISTING_EVENT_IDENT)

    def test_get_pripojit_dokument(self):
        request = self.factory.get("/arch_z/pripojit/dokument/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = pripojit_dokument(request, arch_z_ident_cely=EXISTING_EVENT_IDENT)
        self.assertEqual(200, response.status_code)

    def test_post_pripojit_dokument(self):
        data = {
            "csrfmiddlewaretoken": "27ZVK57GOldButY8IAxsDdqBlpUtsWBcpykJT7DgTENfOsy7uqkfoSoYWkbXmcu2",
            "dokument": str(EXISTING_DOCUMENT_ID),
        }
        request = self.factory.post("/arch_z/pripojit/dokument/", data)
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        documents_before = Dokument.objects.filter(
            casti__archeologicky_zaznam__ident_cely=EXISTING_EVENT_IDENT
        ).count()
        response = pripojit_dokument(request, arch_z_ident_cely=EXISTING_EVENT_IDENT)
        documents_after = Dokument.objects.filter(
            casti__archeologicky_zaznam__ident_cely=EXISTING_EVENT_IDENT
        ).count()
        self.assertEqual(302, response.status_code)
        self.assertTrue("error" not in response.content.decode("utf-8"))
        self.assertEqual(documents_before + 1, documents_after)
