from .base import *

DEBUG = False
ALLOWED_HOSTS += ["web"]
LOGGING["handlers"]["logstash"]["tags"] = "dev_test"

if "debug_toolbar" in INSTALLED_APPS:
    INSTALLED_APPS.remove("debug_toolbar")
if "debug_toolbar.middleware.DebugToolbarMiddleware" in MIDDLEWARE:
    MIDDLEWARE.remove("debug_toolbar.middleware.DebugToolbarMiddleware")
DEBUG_TOOLBAR_PANELS = []
SITE_URL = "http://localhost:8000"

CLAMD_HOST = get_secret("CLAMD_HOST")
CLAMD_PORT = 3310


def get_test_secret(setting, default_value=None):
    """Funkce `get_test_secret` v modulu `webclient.webclient.settings.dev_test`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param setting: Vstupní hodnota používaná při zpracování.
    :param default_value: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    file_test_path = (
        "/run/secrets/test_conf"
        if os.path.exists("/run/secrets/test_conf")
        else os.path.join(BASE_DIR, "webclient/settings/sample_secrets_test_client.json")
    )
    with open(file_test_path, "r") as file:
        secrets_test = json.load(file)
    if default_value is None:
        try:
            return secrets_test[setting]
        except KeyError:
            error_msg = f"Add {setting} variable to {file_test_path} file"
            if not DEBUG:
                raise ImproperlyConfigured(error_msg)
    else:
        return secrets_test.get(setting, default_value)


TEST_RUNNER = "core.tests.runner.AMCRSeleniumTestRunner"

SELENIMUM_ADDRESS = get_test_secret("TEST_SELENIMUM_ADDRESS")
SELENIUM_PORT = get_test_secret("TEST_SELENIUM_PORT")
WEB_SERVER_ADDRESS = get_test_secret("TEST_WEB_SERVER_ADDRESS")  # adresa na které běží test a kterou použije selenium
TEST_DATABASE_NAME = get_test_secret("TEST_DATABASE_NAME")  # jmeno vzorové databáze, která se klonuje
USE_REMOTE_WEB_BROWSER = True

FEDORA_SERVER_NAME = get_test_secret("TEST_FEDORA_SERVER_NAME")
FEDORA_SERVER_HOSTNAME = get_test_secret("TEST_FEDORA_SERVER_HOSTNAME")
FEDORA_PORT_NUMBER = get_test_secret("TEST_FEDORA_PORT_NUMBER")
FEDORA_PROTOCOL = get_test_secret("TEST_FEDORA_PROTOCOL")
FEDORA_PATH = get_test_secret("TEST_FEDORA_PATH")

TEST_SCREENSHOT_PATH = get_test_secret("TEST_SCREENSHOT_PATH")
DATABASES["default"]["TEST"] = {"MIGRATE": False}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
LOGGING["handlers"]["console"]["level"] = "ERROR"
SILENCED_SYSTEM_CHECKS = ["django_recaptcha.recaptcha_test_key_error"]

DATABASES["test_db"] = {
    "ENGINE": "django_prometheus.db.backends.postgis",
    "NAME": TEST_DATABASE_NAME,
    "USER": get_secret("DB_USER"),
    "PASSWORD": get_secret("DB_PASS"),
    "HOST": get_secret("DB_HOST"),
    "PORT": get_secret("DB_PORT"),
    "ATOMIC_REQUESTS": True,
    "DISABLE_SERVER_SIDE_CURSORS": True,
}
