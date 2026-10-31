"""Testy výběru rendereru pohledu ``GetUserInfo`` pro úspěšnou a chybovou cestu."""

import json
from types import SimpleNamespace
from unittest.mock import patch

from api.views import GetUserInfo
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

USER_METADATA = b'<?xml version="1.0" encoding="utf-8"?><amcr:uzivatel xmlns:amcr="x">U-000001</amcr:uzivatel>'


class GetUserInfoRendererTests(SimpleTestCase):
    """Ověřuje, že úspěch vrací XML metadata a chyba JSON, bez potlačení výjimek."""

    def setUp(self):
        """Připraví továrnu požadavků, pohled ``GetUserInfo`` a vypne kontrolu odstávky."""
        maintenance_patcher = patch("core.decorators.get_set_maintenance_in_cache", return_value=None)
        maintenance_patcher.start()
        self.addCleanup(maintenance_patcher.stop)
        self.factory = APIRequestFactory()
        self.view = GetUserInfo.as_view()

    def _authenticated_request(self, **extra):
        """
        Sestaví GET požadavek přihlášený fiktivním uživatelem s pevnými metadaty.

        :param extra: Dodatečné hlavičky WSGI předávané do ``APIRequestFactory.get()``.
        :return: Požadavek s vynuceným přihlášením.
        """
        request = self.factory.get("/api/uzivatel-info/", **extra)
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True, metadata=USER_METADATA))
        return request

    def test_success_returns_user_metadata_as_xml(self):
        """Úspěšná cesta vrací ``user.metadata`` beze změny s typem ``application/xml; charset=utf-8``."""
        response = self.view(self._authenticated_request())
        response.render()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml; charset=utf-8")
        self.assertEqual(response.content, USER_METADATA)

    def test_unauthenticated_error_is_rendered_as_json(self):
        """Chybová cesta (chybějící token) se vykreslí jako JSON, ne jako XML."""
        response = self.view(self.factory.get("/api/uzivatel-info/"))
        response.render()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("detail", json.loads(response.content))

    def test_not_acceptable_error_is_rendered_as_json(self):
        """Selhání negociace (``Accept: text/html``) vede na 406 vykreslené jako JSON."""
        response = self.view(self._authenticated_request(HTTP_ACCEPT="text/html"))
        response.render()

        self.assertEqual(response.status_code, 406)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_finalize_response_does_not_swallow_exceptions(self):
        """Výjimka z negociace ve ``finalize_response`` se propaguje, místo aby byla potlačena."""
        original = GetUserInfo.perform_content_negotiation

        def fail_when_forced(view, request, force=False):
            # Only the forced call made from finalize_response fails; initial() still negotiates normally.
            if force:
                raise RuntimeError("boom")
            return original(view, request, force)

        with patch.object(GetUserInfo, "perform_content_negotiation", fail_when_forced):
            with self.assertRaises(RuntimeError):
                self.view(self.factory.get("/api/uzivatel-info/"))
