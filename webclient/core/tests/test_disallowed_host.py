"""Testy odpovědi na neplatnou hlavičku Host (issue #4119)."""

from core.context_processors import auto_logout_client, main_shows
from django.test import Client, RequestFactory, SimpleTestCase, override_settings


class DisallowedHostTest(SimpleTestCase):
    """Neplatný Host musí skončit odpovědí 400, ne 500."""

    @override_settings(ALLOWED_HOSTS=["amcr.aiscr.cz"], DEBUG=False)
    def test_neplatny_host_vraci_400(self):
        """``DisallowedHost`` vzniká v ``CommonMiddleware`` před autentizací, chybová stránka se musí vykreslit bez ``request.user``."""
        client = Client(raise_request_exception=False)
        response = client.get("/", HTTP_HOST="digiarchiv.aiscr.cz")
        self.assertEqual(response.status_code, 400)

    def test_context_processory_bez_request_user(self):
        """Context processory nesmí padnout na požadavku bez atributu ``user`` a chovají se jako pro anonyma."""
        request = RequestFactory().get("/")
        self.assertFalse(hasattr(request, "user"))
        self.assertEqual(auto_logout_client(request), {})
        self.assertNotIn("show_administrace", main_shows(request))
