"""Volitelné HTTP testy uploadu na testovací aplikaci nebo lokálně s DEBUG=True."""

import base64
import hashlib
import http.client
import io
import json
import os
import ssl
import struct
import time
import zlib
from unittest import SkipTest
from urllib.parse import quote

from core.constants import MAX_PAS_API_FOTOGRAFIE_FILE_SIZE_BYTES
from core.tests.integration import is_debug_local_origin, require_integration_environment
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

_CHUNK_SIZE = 64 * 1024
_SMALL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4//8/AAX+Av4N70a4AAAAAElFTkSuQmCC"
)
_SIZE_ERROR = "The uploaded file exceeds the maximum allowed size."


def _integration_configuration():
    """Povolí síťový test na testovací aplikaci nebo lokálně s DEBUG=True.

    :return: URL proxy, uživatelské jméno, heslo a identifikátor vyhrazeného nálezu.
    :raises SkipTest: Pokud chybí přihlašovací údaje, nejsou povoleny testy nebo nevyhovuje lokální DEBUG.
    :raises ImproperlyConfigured: Pokud chybí vstupy nebo URL neukazuje na povolené prostředí.
    """
    url = require_integration_environment(os.environ.get("PAS_UPLOAD_BASE_URL"))
    username = settings.INTEGRATION_API_TEST_USERNAME
    password = settings.INTEGRATION_API_TEST_PASSWORD
    if not username or not password:
        raise SkipTest("Configure INTEGRATION_API_TEST_USERNAME and INTEGRATION_API_TEST_PASSWORD in Django secrets.")
    ident_cely = os.environ.get("PAS_UPLOAD_IDENT_CELY")
    if not ident_cely:
        raise ImproperlyConfigured("Required environment variable: PAS_UPLOAD_IDENT_CELY")
    return url, username, password, ident_cely


def _http_connection(url, timeout):
    """Vytvoří HTTP spojení; lokální HTTPS s DEBUG=True povolí vývojový certifikát.

    :param url: Adresa ověřená společnou kontrolou prostředí.
    :param timeout: Časový limit spojení v sekundách.
    :return: HTTP nebo HTTPS spojení; vzdálené HTTPS vždy ověřuje certifikát.
    """
    if url.scheme != "https":
        return http.client.HTTPConnection(url.hostname, url.port, timeout=timeout)
    if is_debug_local_origin(url):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return http.client.HTTPSConnection(url.hostname, url.port, timeout=timeout, context=context)
    return http.client.HTTPSConnection(url.hostname, url.port, timeout=timeout)


def _obtain_api_token(url, username, password):
    """Získá token přes API přihlášení bez přesměrování a výpisu citlivých odpovědí.

    :param url: Adresa ověřená společnou kontrolou prostředí.
    :param username: Jméno testovacího uživatele z Django settings.
    :param password: Heslo testovacího uživatele z Django settings.
    :return: Token pro následné Bearer požadavky.
    :raises AssertionError: Pokud přihlášení nevrátí HTTP 200 a neprázdný token.
    """
    connection = _http_connection(url, timeout=30)
    try:
        connection.request(
            "POST",
            "/api/token-auth/",
            body=json.dumps({"username": username, "password": password}),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        response = connection.getresponse()
        if response.status != 200:
            raise AssertionError(f"Integration API login failed with HTTP {response.status}.")
        try:
            body = json.loads(response.read())
        except (ValueError, UnicodeError):
            raise AssertionError("Integration API login did not return valid JSON.") from None
        token = body.get("token") if isinstance(body, dict) else None
        if not isinstance(token, str) or not token.strip():
            raise AssertionError("Integration API login did not return a nonempty token.")
        return token
    finally:
        connection.close()


def _png_with_size(size):
    """Vytvoří PNG s platným pomocným chunkem, bez velkého rastrového obrázku.

    :param size: Požadovaný počet bajtů celého PNG souboru.
    :return: BytesIO obsahující PNG o přesné velikosti, připravené ke čtení.
    :raises ValueError: Pokud velikost nestačí na původní PNG a hlavičku chunku.
    """
    padding_size = size - len(_SMALL_PNG) - 12
    if padding_size < 0:
        raise ValueError("Requested PNG size is too small.")
    result = io.BytesIO()
    result.write(_SMALL_PNG[:-12])
    chunk_type = b"paDd"
    result.write(struct.pack("!I", padding_size) + chunk_type)
    crc = zlib.crc32(chunk_type)
    zeros = bytes(_CHUNK_SIZE)
    remaining = padding_size
    while remaining:
        chunk = zeros[: min(remaining, _CHUNK_SIZE)]
        result.write(chunk)
        crc = zlib.crc32(chunk, crc)
        remaining -= len(chunk)
    result.write(struct.pack("!I", crc))
    result.write(_SMALL_PNG[-12:])
    result.seek(0)
    return result


class UploadFotoHttpIntegrationTests(SimpleTestCase):
    """Ověří skutečné limity bez test clientu, změny konstanty a přímého přístupu do DB.

    URL musí vést na https://amcr-test.aiscr.cz nebo na lokální nginx s DEBUG=True
    v testovacím procesu. Použijte vyhrazený nález a token s oprávněním nahrát soubor;
    všechny testované soubory jsou nad limitem. HTTP přesměrování se nenásledují.
    """

    @classmethod
    def setUpClass(cls):
        """Ověří cílové prostředí před vytvořením PNG nebo síťovým požadavkem."""
        cls.url, username, password, cls.ident_cely = _integration_configuration()
        cls.token = _obtain_api_token(cls.url, username, password)
        super().setUpClass()

    def _upload(self, image, digest, *, expect_continue=False):
        """Odešle multipart přímo přes HTTP bez další úplné kopie PNG v paměti.

        :param image: PNG v BytesIO, které bude čteno od začátku.
        :param digest: Hodnota Content-Digest vypočtená nad PNG.
        :param expect_continue: Přidá hlavičku Expect: 100-continue.
        :return: Stavový kód, typ obsahu a dekódovaná JSON odpověď.
        """
        boundary = "amcr-pas-upload-integration"
        prefix = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="integration.png"\r\n'
            "Content-Type: image/png\r\n\r\n"
        ).encode("ascii")
        suffix = f"\r\n--{boundary}--\r\n".encode("ascii")
        image.seek(0, io.SEEK_END)
        body_size = len(prefix) + image.tell() + len(suffix)
        image.seek(0)
        connection = _http_connection(self.url, timeout=600)
        deadline = time.monotonic() + 600

        def send(data):
            """Odešle část těla v rámci společného časového limitu.

            :param data: Bajty jedné části multipart těla.
            """
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("PAS upload exceeded 600 seconds.")
            connection.sock.settimeout(remaining)
            connection.send(data)

        try:
            path = f"/api/pas/nalez/{quote(self.ident_cely, safe='')}/upload-foto"
            connection.putrequest("POST", path)
            connection.putheader("Authorization", f"Bearer {self.token}")
            connection.putheader("Content-Digest", digest)
            connection.putheader("Content-Type", f"multipart/form-data; boundary={boundary}")
            connection.putheader("Accept", "application/json")
            connection.putheader("Accept-Language", "en")
            connection.putheader("Connection", "close")
            connection.putheader("Content-Length", body_size)
            if expect_continue:
                connection.putheader("Expect", "100-continue")
            connection.endheaders()
            try:
                send(prefix)
                while chunk := image.read(_CHUNK_SIZE):
                    send(chunk)
                send(suffix)
            except (BrokenPipeError, ConnectionResetError):
                # nginx may reject Content-Length before consuming the body.
                # Only a complete HTTP/JSON response below counts as success.
                pass
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("PAS upload exceeded 600 seconds.")
            connection.sock.settimeout(remaining)
            response = connection.getresponse()
            return response.status, response.getheader("Content-Type", ""), json.loads(response.read())
        finally:
            connection.close()

    def test_oversized_png_returns_422_through_proxy(self):
        """Aplikace i nginx opakovaně vracejí JSON 422 pro skutečné nadlimitní PNG."""
        sizes = (
            MAX_PAS_API_FOTOGRAFIE_FILE_SIZE_BYTES + 1,
            MAX_PAS_API_FOTOGRAFIE_FILE_SIZE_BYTES + 5 * 1024**2,
            MAX_PAS_API_FOTOGRAFIE_FILE_SIZE_BYTES + 11 * 1024**2,
            MAX_PAS_API_FOTOGRAFIE_FILE_SIZE_BYTES * 2,
        )
        for size in sizes:
            with _png_with_size(size) as image:
                digest = hashlib.sha512()
                while chunk := image.read(_CHUNK_SIZE):
                    digest.update(chunk)
                content_digest = f"sha-512=:{base64.b64encode(digest.digest()).decode('ascii')}:"
                modes = (False, True) if size == sizes[2] else (False,)
                for expect_continue in modes:
                    for repetition in range(3):
                        with self.subTest(size=size, expect=expect_continue, repetition=repetition):
                            code, content_type, body = self._upload(
                                image, content_digest, expect_continue=expect_continue
                            )
                            self.assertEqual(code, 422)
                            self.assertEqual(content_type.split(";")[0], "application/json")
                            self.assertEqual(body, {"detail": _SIZE_ERROR})
