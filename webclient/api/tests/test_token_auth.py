"""Testy evidence přihlášení přes ``POST /api/token-auth/`` (issue #4230)."""

import secrets
from unittest.mock import PropertyMock, patch

from core.constants import ROLE_BADATEL_ID
from core.tests.test_mappers.fixtures import create_dokument_fixture
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from uzivatel.models import User, UzivatelPrihlaseniLog

TOKEN_AUTH_URL = "/api/token-auth/"
USER_INFO_URL = "/api/uzivatel-info/"
EMAIL = "tokenauth@example.cz"
# Generated at runtime so no credential literal lives in the repo.
PASSWORD = secrets.token_urlsafe(16)


class ObtainAuthTokenLastLoginTests(TestCase):
    """Ověřuje, že token-auth eviduje přihlášení stejně jako webové přihlášení, ale bez session."""

    def setUp(self):
        """Vytvoří aktivního uživatele bez dosavadního přihlášení a API klienta."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        organizace = create_dokument_fixture(ident_cely="C-TX-423001").organizace
        with patch(
            "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
            return_value=True,
        ):
            self.user = User.objects.create_user(  # type: ignore[attr-defined]
                email=EMAIL,
                password=PASSWORD,
                is_active=True,
                ident_cely="U-423001",
                organizace=organizace,
            )
        self.client = APIClient()

    def _obtain_token(self, password=PASSWORD):
        """Odešle přihlašovací údaje na token-auth endpoint.

        :param password: Heslo odeslané v těle požadavku.
        :return: Odpověď testovacího klienta.
        """
        return self.client.post(
            TOKEN_AUTH_URL,
            {"username": EMAIL, "password": password},
            format="json",
            REMOTE_ADDR="192.0.2.10",
        )

    def test_success_sets_last_login_and_writes_login_log(self):
        """Úspěšný token-auth nastaví ``last_login`` a zapíše řádek logu s IP adresou klienta."""
        response = self._obtain_token()

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)
        log = UzivatelPrihlaseniLog.objects.get(user=self.user)
        self.assertEqual(log.ip_adresa, "192.0.2.10")

    def test_success_does_not_create_session(self):
        """Token-auth nevolá ``django.contrib.auth.login()``, takže nevznikne session cookie."""
        response = self._obtain_token()

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("sessionid", response.cookies)

    def test_invalid_password_changes_nothing(self):
        """Neúspěšné ověření nemění ``last_login`` ani nezapisuje log přihlášení."""
        response = self._obtain_token(password=secrets.token_urlsafe(16))

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.last_login)
        self.assertFalse(UzivatelPrihlaseniLog.objects.filter(user=self.user).exists())

    def test_bearer_request_does_not_bump_last_login(self):
        """Běžný požadavek s Bearer tokenem se za přihlášení nepovažuje."""
        token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token.key)

        # The view returns metadata from Fedora, which is unavailable in tests.
        with patch("uzivatel.models.User.metadata", new_callable=PropertyMock, return_value=b"<uzivatel/>"):
            response = self.client.get(USER_INFO_URL)

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.last_login)
        self.assertFalse(UzivatelPrihlaseniLog.objects.filter(user=self.user).exists())
