import logging

from core.tests.runner import (
    EXISTING_EVENT_IDENT,
    EXISTING_LOKALITA_IDENT,
    EXISTING_PROJECT_IDENT,
    TESTOVACI_DOKUMENT_IDENT,
    TESTOVACI_SOUBOR_ID,
)
from django.test import TestCase
from django.urls import reverse
from uzivatel.models import User

logger = logging.getLogger(__name__)


class HistorieTests(TestCase):
    def setUp(self):
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")

    def test_get_projekt_historie(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("historie:projekt", kwargs={"ident_cely": EXISTING_PROJECT_IDENT}))
        self.assertEqual(200, response.status_code)

    def test_get_akce_historie(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("historie:akce", kwargs={"ident_cely": EXISTING_EVENT_IDENT}))
        self.assertEqual(200, response.status_code)

    def test_get_dokument_historie(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("historie:dokument", kwargs={"ident_cely": TESTOVACI_DOKUMENT_IDENT}))
        self.assertEqual(200, response.status_code)

    def test_get_soubor_historie(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("historie:soubor", kwargs={"soubor_id": TESTOVACI_SOUBOR_ID}))
        self.assertEqual(200, response.status_code)
        self.assertTrue("nazev" in response.content.decode("utf-8"))
        self.assertTrue("metadata_form" in response.context)

    def test_get_lokalita_historie(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(reverse("historie:lokalita", kwargs={"ident_cely": EXISTING_LOKALITA_IDENT}))
        self.assertEqual(200, response.status_code)
