from core.tests.runner import add_middleware_to_request
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404
from django.test import RequestFactory, TestCase
from heslar.hesla import TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import Heslar
from oznameni.models import Oznamovatel
from projekt.models import Projekt
from projekt.views import detail
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/projekt/detail/")
        self.request.user = User.objects.get(email="amcr@arup.cas.cz")
        self.request = add_middleware_to_request(self.request, SessionMiddleware)
        self.request.session.save()

    def test_get_detail_not_found(self):
        with self.assertRaises(Http404, msg="No Projekt matches the given query."):
            detail(self.request, ident_cely="not_existing_project_ident")

    def test_get_found(self):
        existing_ident = "M-202212541"
        p = Projekt(
            typ_projektu=Heslar.objects.get(id=TYP_PROJEKTU_ZACHRANNY_ID),
            ident_cely=existing_ident,
        )
        oznamovatel = Oznamovatel(
            email="tester@example.com",
            adresa="Nekde 123",
            odpovedna_osoba="Juraj Skvarla",
            oznamovatel="Juraj Skvarla",
            telefon="+420874521325",
        )
        oznamovatel.save()
        p.oznamovatel = oznamovatel
        p.save()
        response = detail(self.request, ident_cely=existing_ident)
        self.assertEqual(200, response.status_code)
