from core.constants import SN_ZAPSANY
from core.models import Soubor
from core.message_constants import PROJEKT_NELZE_SMAZAT
from core.tests.runner import KATASTR_ODROVICE_ID, add_middleware_to_request
from django.contrib.gis.geos import Point
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404
from django.test import RequestFactory, TestCase
from heslar.hesla import PRISTUPNOST_ANONYM_ID, TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import Heslar, RuianKatastr
from oznameni.models import Oznamovatel
from pas.models import SamostatnyNalez
from projekt.models import Projekt
from projekt.views import create, detail, edit, smazat
from uzivatel.models import User, UserNotificationType


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        UserNotificationType(ident_cely='E-P-01a', predmet="Test", cesta_sablony="emails/new_cooperator.html").save()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")
        self.lokace_zahradky = Point(50.40, 15.70)
        self.projekt = Projekt(
            typ_projektu=Heslar.objects.get(id=TYP_PROJEKTU_ZACHRANNY_ID),
            ident_cely="M-202212541",
            lokalizace="Je to na zahradce",
            geom=self.lokace_zahradky,
            hlavni_katastr=RuianKatastr.objects.get(id=KATASTR_ODROVICE_ID),
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
        request = self.factory.get("/projekt/detail/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request.session.save()

        with self.assertRaises(Http404, msg="No Projekt matches the given query."):
            detail(request, ident_cely="not_existing_project_ident")

    def test_get_detail_found(self):
        request = self.factory.get("/projekt/detail/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request.session.save()

        response = detail(request, ident_cely=self.projekt.ident_cely)
        self.assertEqual(200, response.status_code)

    def test_edit_get_success(self):
        request = self.factory.get("/projekt/edit/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request.session.save()

        response = edit(request, ident_cely=self.projekt.ident_cely)
        self.assertEqual(200, response.status_code)

    def test_edit_post_success(self):
        nova_lokalizace = "Neni to na zahradce"

        data = {
            "lokalizace": nova_lokalizace,
            "csrfmiddlewaretoken": "NYrbj266E2EKwDd9FQ5Nj4mtBRqnxhkWdxVjSfoXePMaDHQ6cfLYiqJKcJ7mhhKH",
            "typ_projektu": str(TYP_PROJEKTU_ZACHRANNY_ID),
            "hlavni_katastr": str(KATASTR_ODROVICE_ID),
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

        request = self.factory.post("/projekt/edit/", data)
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = edit(request, self.projekt.ident_cely)
        projekt = Projekt.objects.get(ident_cely=self.projekt.ident_cely)
        self.assertEqual(302, response.status_code)
        self.assertTrue("error" not in response.content.decode("utf-8"))
        self.assertTrue(projekt.lokalizace == nova_lokalizace)
        self.assertTrue(projekt.geom.coords != self.lokace_zahradky.coords)

    def test_get_smazat_check(self):
        request = self.factory.get("/projekt/smazat/")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = smazat(request, ident_cely=self.projekt.ident_cely)
        self.assertEqual(200, response.status_code)

        # Add samostatny nalez
        nalez = SamostatnyNalez(
            projekt=self.projekt,
            pristupnost=Heslar.objects.get(id=PRISTUPNOST_ANONYM_ID),
            stav=SN_ZAPSANY,
        )
        nalez.save()

        # Client is used there to follow redirect
        self.client.force_login(self.existing_user)
        response = self.client.get(f"/projekt/smazat/{self.projekt.ident_cely}", follow=True)
        self.assertEqual(403, response.status_code)

    def test_post_create_success(self):
        data = {
            "csrfmiddlewaretoken": "NYrbj266E2EKwDd9FQ5Nj4mtBRqnxhkWdxVjSfoXePMaDHQ6cfLYiqJKcJ7mhhKH",
            "typ_projektu": str(TYP_PROJEKTU_ZACHRANNY_ID),
            "hlavni_katastr": str(KATASTR_ODROVICE_ID),
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
        request = self.factory.post("/projekt/create/", data)
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        projects_before = Projekt.objects.all().count()
        response = create(request)
        projects_after = Projekt.objects.all().count()
        self.assertEqual(302, response.status_code)
        self.assertTrue("error" not in response.content.decode("utf-8"))
        self.assertTrue(projects_before < projects_after)

    def test_get_create_success(self):
        request = self.factory.get("/projekt/create")
        request.user = self.existing_user
        request = add_middleware_to_request(request, SessionMiddleware)
        request = add_middleware_to_request(request, MessageMiddleware)
        request.session.save()

        response = create(request)
        self.assertEqual(200, response.status_code)


