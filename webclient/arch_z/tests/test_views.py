import datetime

from arch_z.models import ArcheologickyZaznam
from arch_z.views import detail, odeslat, pripojit_dokument, vratit, zapsat
from core.tests.runner import (
    EL_CHEFE_ID,
    EXISTING_DOCUMENT_ID,
    EXISTING_EVENT_IDENT,
    HLAVNI_TYP_SONDA_ID,
    KATASTR_ODROVICE_ID,
    D_STAV_ZAPSANY,
    EXISTING_EVENT_IDENT_INCOMPLETE,
    add_middleware_to_request,
)
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.utils.translation import gettext as _
from dokument.models import Dokument, DokumentCast
from heslar.hesla import PRISTUPNOST_ANONYM_ID, TYP_DOKUMENTU_NALEZOVA_ZPRAVA
from heslar.models import Heslar
from uzivatel.models import User, Organizace, Osoba


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_projekt_ident = "C-202000001"
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")

    def test_get_detail(self):
        request = self.factory.get("/arch-z/detail/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request.session.save()

        response = detail(request, EXISTING_EVENT_IDENT)
        self.assertEqual(200, response.status_code)

    def test_get_zapsat(self):
        request = self.factory.get("/arch-z/zapsat/")
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
        request = self.factory.post("/arch-z/zapsat/", data)
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = zapsat(request, self.existing_projekt_ident)
        az = ArcheologickyZaznam.objects.filter(ident_cely="C-202000001B").first()
        az.refresh_from_db()
        self.assertEqual(302, response.status_code)
        self.assertEqual(az.akce.specifikace_data.pk, 885)
        self.assertEqual(az.pristupnost.pk, PRISTUPNOST_ANONYM_ID)
        self.assertTrue("error" not in response.content.decode("utf-8"))
        self.assertTrue(
            len(ArcheologickyZaznam.objects.filter(ident_cely="C-202000001B")) == 1
        )

    def test_get_odeslat_s_chybami(self):
        request = self.factory.get("/arch-z/odeslat/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = odeslat(request, EXISTING_EVENT_IDENT_INCOMPLETE)
        self.assertTrue(_("Datum zahájení není vyplněn.") in request.session['temp_data'])
        self.assertTrue(_("Datum ukončení není vyplněn.") in request.session['temp_data'])
        self.assertTrue(_("Lokalizace okolností není vyplněna.") in request.session['temp_data'])
        self.assertTrue(_("Hlavní typ není vyplněn.") in request.session['temp_data'])
        self.assertTrue(_("Hlavní vedoucí není vyplněn.") in request.session['temp_data'])
        self.assertEqual(403, response.status_code)

    def test_get_odeslat(self):
        request = self.factory.get("/arch-z/odeslat/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = odeslat(request, EXISTING_EVENT_IDENT)
        self.assertEqual(200, response.status_code)

    def test_get_vratit(self):
        request = self.factory.get("/arch-z/vratit/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = vratit(request, EXISTING_EVENT_IDENT)
        self.assertEqual(403, response.status_code)

    def test_get_pripojit_dokument(self):
        request = self.factory.get("/arch-z/pripojit/dokument/")
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
        request = self.factory.post("/arch-z/pripojit/dokument/", data)
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
        self.assertEqual(200, response.status_code)
        self.assertTrue("error" not in response.content.decode("utf-8"))
        self.assertEqual(documents_before + 1, documents_after)
