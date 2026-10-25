"""Společná kontrola prostředí pro síťové integrační testy."""

from unittest import SkipTest
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


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
    is_local = url.hostname in {"localhost", "127.0.0.1", "::1"}
    if not is_test_application:
        if not is_local:
            raise ImproperlyConfigured("Only https://amcr-test.aiscr.cz or a DEBUG-enabled loopback origin is allowed.")
        if settings.DEBUG is not True:
            raise SkipTest("Local integration test requires DEBUG=True.")
    return url
