import logging

from core.constants import D_STAV_ODESLANY
from core.message_constants import DOKUMENT_NELZE_ARCHIVOVAT
from core.tests.runner import (
    AMCR_TESTOVACI_ORGANIZACE_ID,
    ARCHEOLOGICKY_POSUDEK_ID,
    AREAL_HRADISTE_ID,
    DOKUMENT_CAST_IDENT,
    DOKUMENT_CAST_IDENT2,
    DOKUMENT_KOMPONENTA_IDENT,
    EXISTIN_NEIDENT_AKCE_IDENT,
    EXISTING_EVENT_IDENT2,
    EXISTING_PROJECT_IDENT_PRUZKUMNY,
    JAZYK_DOKUMENTU_CESTINA_ID,
    LETFOTO_TVAR_ID,
    MATERIAL_DOKUMENTU_DIGI_SOUBOR_ID,
    OBDOBI_STREDNI_PALEOLIT_ID,
    TYP_DOKUMENTU_PLAN_SONDY_ID,
    ZACHOVALOST_30_80_ID,
    add_middleware_to_request,
    EL_CHEFE_ID,
    ARCHIV_ARUB,
    TESTOVACI_DOKUMENT_IDENT,
    DOCUMENT_NALEZOVA_ZPRAVA_IDENT,
    EXISTING_DOCUMENT_ID,
)
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from dokument.models import Dokument, DokumentCast, Tvar
from dokument.views import (
    archivovat,
    create_model_3D,
    edit,
    odeslat,
    get_dokument_table_row,
)
from heslar.hesla import PRISTUPNOST_ANONYM_ID
from heslar.models import Heslar
from uzivatel.models import User
from arch_z.models import ArcheologickyZaznam
from projekt.models import Projekt
from neidentakce.models import NeidentAkce

logger = logging.getLogger(__name__)


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")
        self.existing_dokument = TESTOVACI_DOKUMENT_IDENT
        self.dokument_with_soubor = DOCUMENT_NALEZOVA_ZPRAVA_IDENT

    def test_get_detail(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(f"/dokument/detail/{self.existing_dokument}")
        self.assertEqual(200, response.status_code)

    def test_get_detail_cast(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            f"/dokument/detail/{self.existing_dokument}/cast/{DOKUMENT_CAST_IDENT}"
        )

        self.assertEqual(200, response.status_code)

    def test_get_cast_editovat(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(f"/dokument/edit-cast/{DOKUMENT_CAST_IDENT}")
        self.assertEqual(200, response.status_code)

    def test_post_cast_editovat(self):
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "poznamka": "test poznamka",
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/dokument/edit-cast/{DOKUMENT_CAST_IDENT}", data, follow=True
        )
        dok_cast = DokumentCast.objects.filter(ident_cely=DOKUMENT_CAST_IDENT).first()
        self.assertEqual(200, response.status_code)
        self.assertEqual(dok_cast.poznamka, "test poznamka")
        self.assertTrue(
            len(DokumentCast.objects.filter(ident_cely=DOKUMENT_CAST_IDENT)) == 1
        )

    def test_get_cast_zapsat(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            f"/dokument/vytvorit-cast/{TESTOVACI_DOKUMENT_IDENT}"
        )
        self.assertEqual(200, response.status_code)

    def test_post_cast_zapsat(self):
        dok = Dokument.objects.filter(ident_cely=TESTOVACI_DOKUMENT_IDENT).first()
        old_casti = dok.casti.count()
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "poznamka": "poznamka cast",
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/dokument/vytvorit-cast/{TESTOVACI_DOKUMENT_IDENT}",
            data,
            follow=True,
        )
        dok.refresh_from_db()
        new_casti = dok.casti.count()
        self.assertEqual(200, response.status_code)
        self.assertEqual(old_casti + 1, new_casti)

    def test_get_detail_komponenta(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            f"/dokument/detail/{self.existing_dokument}/komponenta/{DOKUMENT_KOMPONENTA_IDENT}"
        )

        self.assertEqual(200, response.status_code)

    def test_get_komponenta_zapsat(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            f"/dokument/detail/{TESTOVACI_DOKUMENT_IDENT}/cast/{DOKUMENT_CAST_IDENT}/komponenta/zapsat"
        )
        self.assertEqual(200, response.status_code)

    def test_post_komponenta_zapsat(self):
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "obdobi": str(OBDOBI_STREDNI_PALEOLIT_ID),
            "jistota": "0",
            "areal": str(AREAL_HRADISTE_ID),
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/komponenta/zapsat/{DOKUMENT_CAST_IDENT}?typ=cast",
            data,
            follow=True,
        )
        dok_cast = DokumentCast.objects.filter(ident_cely=DOKUMENT_CAST_IDENT).first()
        komponenty = len(dok_cast.komponenty.komponenty.all())
        self.assertEqual(200, response.status_code)
        self.assertEqual(komponenty, 2)

    def test_post_tvary_editovat(self):
        dok = Dokument.objects.filter(ident_cely=TESTOVACI_DOKUMENT_IDENT).first()

        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            f"{TESTOVACI_DOKUMENT_IDENT}_d-INITIAL_FORMS": 0,
            f"{TESTOVACI_DOKUMENT_IDENT}_d-TOTAL_FORMS": 1,
            f"{TESTOVACI_DOKUMENT_IDENT}_d-__prefix__-tvar": "",
            f"{TESTOVACI_DOKUMENT_IDENT}_d-__prefix__-poznamka": "",
            f"{TESTOVACI_DOKUMENT_IDENT}_d-__prefix__-id": "",
            f"{TESTOVACI_DOKUMENT_IDENT}_d-__prefix__-dokument": str(dok.pk),
            f"{TESTOVACI_DOKUMENT_IDENT}_d-0-tvar": str(LETFOTO_TVAR_ID),
            f"{TESTOVACI_DOKUMENT_IDENT}_d-0-poznamka": "poznamka",
            f"{TESTOVACI_DOKUMENT_IDENT}_d-0-id": "",
            f"{TESTOVACI_DOKUMENT_IDENT}_d-0-dokument": str(dok.pk),
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/dokument/edit-tvar/{TESTOVACI_DOKUMENT_IDENT}",
            data,
            follow=True,
        )
        dok.refresh_from_db()
        tvary = len(dok.tvary.all())
        self.assertEqual(200, response.status_code)
        self.assertEqual(tvary, 2)

    def test_get_tvary_smazat(self):
        tvar = Tvar.objects.first()
        self.client.force_login(self.existing_user)
        response = self.client.get(f"/dokument/smazat-tvar/{tvar.pk}")
        self.assertEqual(200, response.status_code)

    def test_post_tvary_smazat(self):
        tvar = Tvar.objects.first()
        old_tvary = Tvar.objects.count()
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/dokument/smazat-tvar/{tvar.pk}",
            data,
            follow=True,
        )
        new_tvary = Tvar.objects.count()
        self.assertEqual(200, response.status_code)
        self.assertEqual(new_tvary, old_tvary - 1)

    def test_get_pripojit_archz(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            f"/dokument/pripojit-arch-z/{DOKUMENT_CAST_IDENT}?type=akce"
        )
        self.assertEqual(200, response.status_code)

    def test_post_pripojit_archz(self):
        az = ArcheologickyZaznam.objects.get(ident_cely=EXISTING_EVENT_IDENT2)
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "arch_z": str(az.id),
            "old_stav": 1,
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/dokument/pripojit-arch-z/{DOKUMENT_CAST_IDENT}?type=akce",
            data,
            follow=True,
        )
        dok_cast = DokumentCast.objects.get(ident_cely=DOKUMENT_CAST_IDENT)
        self.assertEqual(200, response.status_code)
        self.assertEqual(dok_cast.archeologicky_zaznam, az)
        self.assertIsNone(dok_cast.projekt)

    def test_get_pripojit_projekt(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(f"/dokument/pripojit-projekt/{DOKUMENT_CAST_IDENT}")
        self.assertEqual(200, response.status_code)

    def test_post_pripojit_projekt(self):
        projekt = Projekt.objects.get(ident_cely=EXISTING_PROJECT_IDENT_PRUZKUMNY)
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "projekt": str(projekt.id),
            "old_stav": 1,
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/dokument/pripojit-projekt/{DOKUMENT_CAST_IDENT}",
            data,
            follow=True,
        )
        dok_cast = DokumentCast.objects.get(ident_cely=DOKUMENT_CAST_IDENT)
        self.assertEqual(200, response.status_code)
        self.assertEqual(dok_cast.projekt, projekt)
        self.assertIsNone(dok_cast.archeologicky_zaznam)

    def test_get_odpojit_vazbu_cast(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(f"/dokument/odpojit-cast/{DOKUMENT_CAST_IDENT}")
        self.assertEqual(200, response.status_code)

    def test_post_odpojit_vazbu_cast(self):
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "old_stav": 1,
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/dokument/odpojit-cast/{DOKUMENT_CAST_IDENT}",
            data,
            follow=True,
        )
        dok_cast = DokumentCast.objects.get(ident_cely=DOKUMENT_CAST_IDENT)
        self.assertEqual(200, response.status_code)
        self.assertIsNone(dok_cast.projekt)
        self.assertIsNone(dok_cast.archeologicky_zaznam)

    def test_get_smazat_cast(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(f"/dokument/smazat-cast/{DOKUMENT_CAST_IDENT2}")
        self.assertEqual(200, response.status_code)

    def test_post_smazat_cast(self):
        dok = DokumentCast.objects.get(ident_cely=DOKUMENT_CAST_IDENT2).dokument
        old_dok_casti = dok.casti.count()
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "old_stav": 1,
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/dokument/smazat-cast/{DOKUMENT_CAST_IDENT}",
            data,
            follow=True,
        )
        dok.refresh_from_db()
        new_dok_casti = dok.casti.count()
        self.assertEqual(200, response.status_code)
        self.assertEqual(new_dok_casti, old_dok_casti - 1)
        with self.assertRaises(DokumentCast.DoesNotExist):
            DokumentCast.objects.get(ident_cely=DOKUMENT_CAST_IDENT)

    def test_get_smazat_neident_akce(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(
            f"/dokument/smazat-neident-akce/{DOKUMENT_CAST_IDENT2}"
        )
        self.assertEqual(200, response.status_code)

    def test_post_smazat_neident_akce(self):
        data = {
            "csrfmiddlewaretoken": "5X8q5kjaiRg63lWg0WIriIwt176Ul396OK9AVj9ygODPd1XvT89rGek9Bv2xgIcv",
            "old_stav": 1,
        }
        self.client.force_login(self.existing_user)
        response = self.client.post(
            f"/dokument/smazat-neident-akce/{DOKUMENT_CAST_IDENT2}",
            data,
            follow=True,
        )
        cast = DokumentCast.objects.get(ident_cely=DOKUMENT_CAST_IDENT2)
        self.assertEqual(200, response.status_code)
        with self.assertRaises(NeidentAkce.DoesNotExist):
            NeidentAkce.objects.get(ident_cely=EXISTIN_NEIDENT_AKCE_IDENT)

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
        response = archivovat(requestA, ident_cely=self.existing_dokument)
        self.assertEqual(403, response.status_code)

        request = self.factory.get("/dokument/odeslat/")
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.user = self.existing_user
        request.session.save()
        # Dokument lze odeslat
        response = odeslat(request, ident_cely=self.dokument_with_soubor)
        self.assertEqual(200, response.status_code)

        data = {
            "csrfmiddlewaretoken": "OxkETGL2ZdGqjVIqmDUxCYQccG49OOmBe6OMsT3Tz0OQqZlnT2AIBkdtNyL8yOMm",
            "old_stav": 1,
        }
        request = self.factory.post("/dokument/odeslat/", data)
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.user = self.existing_user
        request.session.save()
        # Stav se zmeni na odeslany
        response = odeslat(request, ident_cely=self.existing_dokument)
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            Dokument.objects.get(ident_cely=self.existing_dokument).stav,
            D_STAV_ODESLANY,
        )
        # Nejde archivovat protoze neni prilozen soubor
        response = archivovat(requestA, ident_cely=self.existing_dokument)
        self.assertEqual(403, response.status_code)

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

    def test_get_table_row(self):
        data = {
            "id": EXISTING_DOCUMENT_ID,
        }
        request = self.factory.get("/dokument/dokument-radek-tabulky", data)
        request = add_middleware_to_request(request, SessionMiddleware)
        request.user = self.existing_user
        request.session.save()

        response = get_dokument_table_row(request)
        self.assertContains(response, TESTOVACI_DOKUMENT_IDENT)
