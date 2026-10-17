"""Volitelné HTTP testy uploadu na testovací aplikaci nebo lokálně s DEBUG=True."""

import base64
import hashlib
import http.client
import io
import json
import os
import struct
import time
import zlib
from unittest import SkipTest
from unittest.mock import patch
from urllib.parse import quote, urlsplit

from core.constants import MAX_PAS_API_FOTOGRAFIE_FILE_SIZE_BYTES
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

_CHUNK_SIZE = 64 * 1024
_SMALL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4//8/AAX+Av4N70a4AAAAAElFTkSuQmCC"
)
_SIZE_ERROR = "The uploaded file exceeds the maximum allowed size."


def _integration_configuration():
    """Povolí síťový test na testovací aplikaci nebo lokálně s DEBUG=True.

    :return: URL proxy, token a identifikátor vyhrazeného nálezu.
    :raises SkipTest: Pokud není nastavena cílová adresa nebo lokální test nemá DEBUG=True.
    :raises ImproperlyConfigured: Pokud chybí vstupy nebo URL neukazuje na povolené prostředí.
    """
    if not os.environ.get("PAS_UPLOAD_BASE_URL"):
        raise SkipTest("Set PAS_UPLOAD_BASE_URL to select the integration-test target.")
    names = ("PAS_UPLOAD_BASE_URL", "PAS_UPLOAD_TOKEN", "PAS_UPLOAD_IDENT_CELY")
    if any(not os.environ.get(name) for name in names):
        raise ImproperlyConfigured(f"Required environment variables: {', '.join(names)}")
    base_url, token, ident_cely = (os.environ[name] for name in names)
    url = urlsplit(base_url)
    if (
        url.scheme not in {"http", "https"}
        or url.username is not None
        or url.password is not None
        or url.path not in {"", "/"}
        or url.query
        or url.fragment
    ):
        raise ImproperlyConfigured("PAS_UPLOAD_BASE_URL must be an HTTP(S) origin without credentials.")
    try:
        port = url.port
    except ValueError as error:
        raise ImproperlyConfigured("PAS_UPLOAD_BASE_URL has an invalid port.") from error
    is_test_application = url.scheme == "https" and url.hostname == "amcr-test.aiscr.cz" and port in {None, 443}
    is_local = url.hostname in {"localhost", "127.0.0.1", "::1"}
    if not is_test_application:
        if not is_local:
            raise ImproperlyConfigured("Only https://amcr-test.aiscr.cz or a DEBUG-enabled loopback origin is allowed.")
        if settings.DEBUG is not True:
            raise SkipTest("Local PAS upload integration test requires DEBUG=True.")
    return url, token, ident_cely


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


class UploadFotoIntegrationGuardTests(SimpleTestCase):
    """Ověří cílovou adresu a ochranu produkce bez síťových požadavků."""

    def _configuration_for(self, base_url, debug):
        """Vyhodnotí pojistku s úplnými testovacími vstupy bez skutečného tokenu.

        :param base_url: Cílová adresa ověřovaná pojistkou.
        :param debug: DEBUG testovacího procesu.
        :return: Ověřená konfigurace pro povolené prostředí.
        """
        with (
            override_settings(DEBUG=debug),
            patch.dict(
                os.environ,
                {
                    "PAS_UPLOAD_BASE_URL": base_url,
                    "PAS_UPLOAD_TOKEN": "guard-test-placeholder",
                    "PAS_UPLOAD_IDENT_CELY": "C-TEST-N00001",
                },
            ),
        ):
            return _integration_configuration()

    def test_test_application_is_allowed_without_debug(self):
        """Přesná HTTPS adresa testovací aplikace je povolena i při DEBUG=False."""
        for origin in ("https://amcr-test.aiscr.cz", "https://amcr-test.aiscr.cz:443/"):
            with self.subTest(origin=origin):
                url, _, _ = self._configuration_for(origin, debug=False)
                self.assertEqual(url.hostname, "amcr-test.aiscr.cz")

    def test_local_application_requires_debug(self):
        """Loopback lze použít pouze s DEBUG=True."""
        for origin in ("http://127.0.0.1:8080", "http://localhost:8080", "http://[::1]:8080"):
            with self.subTest(origin=origin):
                with self.assertRaises(SkipTest):
                    self._configuration_for(origin, debug=False)
                self.assertEqual(self._configuration_for(origin, debug=True)[0].scheme, "http")

    def test_production_and_lookalike_urls_are_rejected(self):
        """Produkce ani podobné adresy nejsou povoleny, a to ani s DEBUG=True."""
        origins = (
            "https://amcr.aiscr.cz",
            "https://amcr-test.aiscr.cz.example.org",
            "https://amcr-test.aiscr.cz@amcr.aiscr.cz",
            "https://amcr.aiscr.cz@amcr-test.aiscr.cz",
            "http://amcr-test.aiscr.cz",
            "https://amcr-test.aiscr.cz:444",
            "https://amcr.aiscr.cz/?next=https://amcr-test.aiscr.cz",
            "https://amcr-test.aiscr.cz/accounts/login/?next=/",
        )
        for origin in origins:
            for debug in (False, True):
                with self.subTest(origin=origin, debug=debug):
                    with self.assertRaises(ImproperlyConfigured):
                        self._configuration_for(origin, debug)

    def test_missing_target_skips(self):
        """Bez cílové adresy se test přeskočí i s DEBUG=True."""
        for debug in (False, True):
            with self.subTest(debug=debug), override_settings(DEBUG=debug), patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(SkipTest):
                    _integration_configuration()


class UploadFotoHttpIntegrationTests(SimpleTestCase):
    """Ověří skutečné limity bez test clientu, změny konstanty a přímého přístupu do DB.

    URL musí vést na https://amcr-test.aiscr.cz nebo na lokální nginx s DEBUG=True
    v testovacím procesu. Použijte vyhrazený nález a token s oprávněním nahrát soubor;
    všechny testované soubory jsou nad limitem. HTTP přesměrování se nenásledují.
    """

    @classmethod
    def setUpClass(cls):
        """Ověří cílové prostředí před vytvořením PNG nebo síťovým požadavkem."""
        cls.url, cls.token, cls.ident_cely = _integration_configuration()
        super().setUpClass()

    def _upload(self, image, digest, *, chunked=False, expect_continue=False):
        """Odešle multipart přímo přes HTTP bez další úplné kopie PNG v paměti.

        :param image: PNG v BytesIO, které bude čteno od začátku.
        :param digest: Hodnota Content-Digest vypočtená nad PNG.
        :param chunked: Použije chunked přenos místo Content-Length.
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
        connection_type = http.client.HTTPSConnection if self.url.scheme == "https" else http.client.HTTPConnection
        connection = connection_type(self.url.hostname, self.url.port, timeout=600)
        deadline = time.monotonic() + 600

        def send(data):
            """Odešle část těla v rámci společného časového limitu.

            :param data: Bajty jedné části multipart těla.
            """
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("PAS upload exceeded 600 seconds.")
            connection.sock.settimeout(remaining)
            if chunked:
                connection.send(f"{len(data):x}\r\n".encode("ascii"))
                connection.send(data)
                connection.send(b"\r\n")
            else:
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
            connection.putheader(
                "Transfer-Encoding" if chunked else "Content-Length", "chunked" if chunked else body_size
            )
            if expect_continue:
                connection.putheader("Expect", "100-continue")
            connection.endheaders()
            try:
                send(prefix)
                while chunk := image.read(_CHUNK_SIZE):
                    send(chunk)
                send(suffix)
                if chunked:
                    connection.send(b"0\r\n\r\n")
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
        sizes = (MAX_PAS_API_FOTOGRAFIE_FILE_SIZE_BYTES + 1, 255 * 1024**2, 261 * 1024**2, 512 * 1024**2)
        for size in sizes:
            with _png_with_size(size) as image:
                digest = hashlib.sha512()
                while chunk := image.read(_CHUNK_SIZE):
                    digest.update(chunk)
                content_digest = f"sha-512=:{base64.b64encode(digest.digest()).decode('ascii')}:"
                modes = [(False, False)]
                if size == 261 * 1024**2:
                    modes += [(True, False), (False, True), (True, True)]
                for chunked, expect_continue in modes:
                    for repetition in range(3):
                        with self.subTest(size=size, chunked=chunked, expect=expect_continue, repetition=repetition):
                            code, content_type, body = self._upload(
                                image, content_digest, chunked=chunked, expect_continue=expect_continue
                            )
                            self.assertEqual(code, 422)
                            self.assertEqual(content_type.split(";")[0], "application/json")
                            self.assertEqual(body, {"detail": _SIZE_ERROR})
