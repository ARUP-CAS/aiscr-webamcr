from unittest import mock

from core.tests.runner import AMCR_TESTOVACI_ORGANIZACE_ID, add_middleware_to_request
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from uzivatel.models import User
from uzivatel.views import UserRegistrationView, create_osoba


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

    def test_post_register(self):
        data = {
            "csrfmiddlewaretoken": "4NS9fHO417U5EKpG84rdhfvXNhm3fMdtz0WWmkOMwwpxtsZkClhzm6VCXjEDjGm1",
            "first_name": "Jarko",
            "last_name ": "Mrkvicka",
            "organizace ": str(AMCR_TESTOVACI_ORGANIZACE_ID),
            "email": "mrkvicka@neaktivni.com",
            "password1 ": "mojesupertajneheslo",
            "password2 ": "mojesupertajneheslo",
        }
        request = self.factory.post("/accounts/register", data)
        request = add_middleware_to_request(request, SessionMiddleware)
        request.user = AnonymousUser()
        request.session.save()

        user_count_before = User.objects.all().count()
        response = UserRegistrationView.as_view()(request)
        user_count_after = User.objects.all().count()
        self.assertEqual(302, response.status_code)
        self.assertTrue(user_count_after > user_count_before)
