from unittest import mock

from core.tests.runner import add_middleware_to_request
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from uzivatel.models import User
from uzivatel.views import create_osoba


class TestUzivatel(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_create_osoba(self):
        request = self.factory.get("/uzivatel/osoba/create/")
        request.user = User.objects.get(email="amcr@arup.cas.cz")
        request = add_middleware_to_request(request, SessionMiddleware)
        request.session.save()

        response = create_osoba(request)
        self.assertEqual(200, response.status_code)

    @mock.patch("uzivatel.views.messages.add_message", return_value=None)
    def test_post_create_osoba(self, mock_add_message):
        data = {
            "jmeno": "Tester",
            "prijmeni": "Testovaci",
            "next": "/testovaci/redirect",
        }
        request = self.factory.post("/uzivatel/osoba/create/", data)
        request.user = User.objects.get(email="amcr@arup.cas.cz")
        request = add_middleware_to_request(request, SessionMiddleware)
        request.session.save()

        response = create_osoba(request)
        self.assertEqual(302, response.status_code)
        self.assertTrue("error" not in response.content.decode("utf-8"))
