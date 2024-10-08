from unittest import mock

from core.tests.runner import AMCR_TESTOVACI_ORGANIZACE_ID
from django.test import RequestFactory, TestCase
from django.urls import reverse
from uzivatel.models import User


class TestUzivatel(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_create_osoba(self):
        self.client.force_login(User.objects.get(email="amcr@arup.cas.cz"))
        response = self.client.get(reverse("heslar:create_osoba"))
        self.assertEqual(200, response.status_code)

    @mock.patch("uzivatel.views.messages.add_message", return_value=None)
    def test_post_create_osoba(self, mock_add_message):
        data = {
            "jmeno": "Tester",
            "prijmeni": "Testovaci",
        }
        self.client.force_login(User.objects.get(email="amcr@arup.cas.cz"))
        response = self.client.post(reverse("heslar:create_osoba"), data)
        self.assertEqual(200, response.status_code)
        self.assertTrue("error" not in response.content.decode("utf-8"))

    def test_post_register(self):
        data = {
            "csrfmiddlewaretoken": "4NS9fHO417U5EKpG84rdhfvXNhm3fMdtz0WWmkOMwwpxtsZkClhzm6VCXjEDjGm1",
            "first_name": "Jarko",
            "last_name": "Mrkvicka",
            "telefon": "",
            "organizace": str(AMCR_TESTOVACI_ORGANIZACE_ID),
            "email": "mrkvicka@neaktivni.com",
            "password1": "mojesupertajneheslo",
            "password2": "mojesupertajneheslo",
        }

        user_count_before = User.objects.all().count()
        response = self.client.post("/accounts/register/", data, follow=True)
        user_count_after = User.objects.all().count()
        self.assertEqual(200, response.status_code)
        self.assertTrue(user_count_after > user_count_before)
