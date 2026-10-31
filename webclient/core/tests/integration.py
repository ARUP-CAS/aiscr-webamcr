"""Společná kontrola prostředí pro síťové integrační testy."""

from unittest import SkipTest
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

#: Hostitelé, které integrační testy považují za lokální (loopback) cíl.
LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def is_local_origin(url):
    """Určí, zda adresa míří na loopback hostitele z :data:`LOOPBACK_HOSTS`.

    :param url: Rozparsovaná adresa (výsledek ``urlsplit``).
    :return: ``True``, pokud je hostitel adresy loopback.
    """
    return url.hostname in LOOPBACK_HOSTS


def is_debug_local_origin(url):
    """Určí, zda jde o lokální cíl povolený jen při ``settings.DEBUG=True``.

    Na tuto klasifikaci se váže i povolení neověřeného vývojového certifikátu u lokálního HTTPS.

    :param url: Rozparsovaná adresa (výsledek ``urlsplit``).
    :return: ``True``, pokud je hostitel loopback a ``settings.DEBUG`` je ``True``.
    """
    return is_local_origin(url) and settings.DEBUG is True


def require_integration_environment(base_url):
    """Povolí integrační testy pouze na testovací aplikaci nebo lokálně s DEBUG=True.

    :param base_url: Adresa cílové aplikace; pro přímé testy Fedory hodnota SITE_URL.
    :return: Rozparsovaná a ověřená adresa aplikace.
    :raises SkipTest: Pokud chybí přepínač, cílová adresa nebo lokální DEBUG=True.
    :raises ImproperlyConfigured: Pokud adresa neoznačuje povolené prostředí.
    """
    if settings.FEDORA_INTEGRATION_TESTS is not True:
        raise SkipTest("Enable settings.FEDORA_INTEGRATION_TESTS to run integration tests.")
    if not base_url:
        raise SkipTest("Configure the integration-test application URL to select the target.")
    url = urlsplit(base_url)
    if (
        url.scheme not in {"http", "https"}
        or url.username is not None
        or url.password is not None
        or url.path not in {"", "/"}
        or url.query
        or url.fragment
    ):
        raise ImproperlyConfigured("Integration-test target URL must be an HTTP(S) origin without credentials.")
    try:
        port = url.port
    except ValueError as error:
        raise ImproperlyConfigured("Integration-test target URL has an invalid port.") from error
    is_test_application = url.scheme == "https" and url.hostname == "amcr-test.aiscr.cz" and port in {None, 443}
    if not is_test_application:
        if not is_local_origin(url):
            raise ImproperlyConfigured("Only https://amcr-test.aiscr.cz or a DEBUG-enabled loopback origin is allowed.")
        if not is_debug_local_origin(url):
            raise SkipTest("Local integration test requires DEBUG=True.")
    return url
