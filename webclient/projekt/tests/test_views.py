from core.tests.runner import add_middleware_to_request
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404
from django.test import RequestFactory, TestCase
from heslar.hesla import TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import Heslar
from oznameni.models import Oznamovatel
from projekt.models import Projekt
from projekt.views import detail, edit
from uzivatel.models import User


class UrlTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")

        self.projekt = Projekt(
            typ_projektu=Heslar.objects.get(id=TYP_PROJEKTU_ZACHRANNY_ID),
            ident_cely="M-202212541",
        )
        self.oznamovatel = Oznamovatel(
            email="tester@example.com",
            adresa="Nekde 123",
            odpovedna_osoba="Juraj Skvarla",
            oznamovatel="Juraj Skvarla",
            telefon="+420874521325",
        )
        self.oznamovatel.save()
        self.projekt.oznamovatel = self.oznamovatel
        self.projekt.save()

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
