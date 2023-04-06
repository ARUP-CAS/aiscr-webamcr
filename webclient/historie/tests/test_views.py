import logging

from core.tests.runner import (
    EXISTING_EVENT_IDENT,
    EXISTING_PROJECT_IDENT,
    TESTOVACI_DOKUMENT_IDENT,
    TESTOVACI_SOUBOR_ID,
    EXISTING_LOKALITA_IDENT,
)
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from historie.views import (
    AkceHistorieListView,
    DokumentHistorieListView,
    LokalitaHistorieListView,
    ProjektHistorieListView,
)
from uzivatel.models import User

logger = logging.getLogger(__name__)


class HistorieTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.existing_user = User.objects.get(email="amcr@arup.cas.cz")

    def test_get_projekt_historie(self):
        self.client.force_login(self.existing_user)
        request = self.factory.get("/historie/projekt")

        response = ProjektHistorieListView.as_view()(
            request, ident_cely=EXISTING_PROJECT_IDENT
        )
        self.assertEqual(200, response.status_code)

    def test_get_akce_historie(self):
        self.client.force_login(self.existing_user)
        request = self.factory.get("/historie/arch_z")
        response = AkceHistorieListView.as_view()(
            request, ident_cely=EXISTING_EVENT_IDENT
        )
        self.assertEqual(200, response.status_code)

    def test_get_dokument_historie(self):
        self.client.force_login(self.existing_user)
        request = self.factory.get("/historie/dokument")

        response = DokumentHistorieListView.as_view()(
            request, ident_cely=TESTOVACI_DOKUMENT_IDENT
        )
        self.assertEqual(200, response.status_code)

    def test_get_soubor_historie(self):
        self.client.force_login(self.existing_user)
        response = self.client.get(f"/historie/soubor/{TESTOVACI_SOUBOR_ID}")
        self.assertEqual(200, response.status_code)
        self.assertTrue("nazev_zkraceny" in response.content.decode("utf-8"))
        self.assertTrue("metadata_form" in response.context)

    def test_get_lokalita_historie(self):
        self.client.force_login(self.existing_user)
        request = self.factory.get("/historie/lokalita")

        response = LokalitaHistorieListView.as_view()(
            request, ident_cely=EXISTING_LOKALITA_IDENT
        )
        self.assertEqual(200, response.status_code)
