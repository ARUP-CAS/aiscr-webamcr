import os

from .base import *

TEST_RUNNER = "django.test.runner.DiscoverRunner"
SKIP_SELENIUM_TESTS = True
FEDORA_INTEGRATION_TESTS = False
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# CI má vlastní lokální služby; ignoruje připojení z Docker secrets.
for alias in DATABASES:
    DATABASES[alias].update(
        NAME=os.environ.get("AMCR_CI_DB_NAME", "amcr_ci"),
        USER=os.environ.get("AMCR_CI_DB_USER", "amcr_ci"),
        PASSWORD=os.environ.get("AMCR_CI_DB_PASSWORD", "ci-only-password"),
        HOST="127.0.0.1",
        PORT=os.environ.get("AMCR_CI_DB_PORT", "5432"),
    )
DATABASES["urgent"]["TEST"] = {"MIRROR": "default"}

REDIS_HOST = "127.0.0.1"
REDIS_PORT = int(os.environ.get("AMCR_CI_REDIS_PORT", "6379"))
CACHEOPS_ENABLED = False
CACHEOPS_REDIS = {"host": REDIS_HOST, "port": REDIS_PORT, "db": 2}
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
    }
}
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
STORAGES = {"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
COMPRESS_ENABLED = False
COMPRESS_OFFLINE = False
COMPRESS_PRECOMPILERS = ()
SKIP_RECAPTCHA = True
RECAPTCHA_PUBLIC_KEY = ""
RECAPTCHA_PRIVATE_KEY = "ci-only-key"
SILENCED_SYSTEM_CHECKS = ["django_recaptcha.recaptcha_test_key_error"]
AUTO_LOGOUT = {}
SITE_URL = "http://localhost:8000"

# Neplatné domény zachovávají formát URL pro mocky; síť blokuje také CI wrapper.
OAI_PURL = "https://api.invalid/id/"
DIGIARCHIV_PURL = "https://digiarchiv.invalid/id/"
DIGIARCHIV_SERVER_URL = "https://digiarchiv.invalid/"
DIGIARCHIV_UPDATE = ""
DIGI_LINKS = {**DIGI_LINKS, "Digi_archiv_link": DIGIARCHIV_PURL, "OAPI_link": OAI_PURL}
NEWS_FEED_BASE_URL = "https://news.invalid/feed/amcr-info"
FEDORA_PROTOCOL = "http"
FEDORA_SERVER_HOSTNAME = "fedora.invalid"
FEDORA_SERVER_NAME = "AMCR"
FEDORA_PORT_NUMBER = "8080"
FEDORA_TRANSACTION_URL = "http://fedora.invalid:8080/rest/fcr:tx"
FEDORA_USER = FEDORA_USER_PASSWORD = FEDORA_ADMIN_USER = FEDORA_ADMIN_USER_PASSWORD = ""
DATACITE_URL = "https://datacite.invalid/"
DOI_USER = DOI_USER_PASSWORD = ""
CLAMD_HOST = None
