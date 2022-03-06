import json
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from core.message_constants import AUTOLOGOUT_AFTER_LOGOUT

BASE_DIR = Path(__file__).resolve().parent.parent.parent

file_path = (
    "webclient/settings/secrets.json"
    if os.path.exists(BASE_DIR / "webclient/settings/secrets.json")
    else "webclient/settings/secrets_test.json"
)
with open(BASE_DIR / file_path, "r") as f:
    secrets = json.load(f)


def get_secret(setting, file=secrets):
    try:
        return file[setting]
    except KeyError:
        error_msg = "Add {0} variable to secrets.json file".format(setting)
        raise ImproperlyConfigured(error_msg)


SECRET_KEY = get_secret("SECRET_KEY")

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": get_secret("DB_NAME"),
        "USER": get_secret("DB_USER"),
        "PASSWORD": get_secret("DB_PASS"),
        "HOST": get_secret("DB_HOST"),
        "PORT": get_secret("DB_PORT"),
        "ATOMIC_REQUESTS": True,
    },
}

DEBUG = False

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "dal",
    "dal_select2",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django.contrib.sessions.backends.signed_cookies",
    "django_filters",
    "django_tables2",
    "django_tables2_column_shifter",
    "crispy_forms",
    "django_registration",
    "compressor",
    "captcha",
    "core",
    "uzivatel.apps.UzivatelConfig",
    "ez",
    "historie",
    "oznameni",
    "projekt.apps.ProjektConfig",
    "heslar",
    "pian.apps.PianConfig",
    "arch_z.apps.ArchZConfig",
    "dokument.apps.DokumentConfig",
    "nalez",
    "adb",
    "neidentakce",
    "pas.apps.PasConfig",
    "komponenta",
    "dj",
    "simple_history",
    "widget_tweaks",
    "rosetta",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "django_auto_logout.middleware.auto_logout",
]

ROOT_URLCONF = "webclient.urls"

STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "static" / "js",
    BASE_DIR / "static" / "css",
    BASE_DIR / "static" / "scss",
    BASE_DIR / "static" / "loga",
    BASE_DIR / "static" / "img",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.constants_import",
                "core.context_processors.digi_links_from_settings"
                "core.context_processors.auto_logout_client",  # for auto logout aftert idle
            ],
        },
    },
]

WSGI_APPLICATION = "webclient.wsgi.application"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "webclient.hashers.PBKDF2WrappedSHA1PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "cs"

LANGUAGES = [
    ('cs', 'Czech'),
    ('en', 'English'),
]

TIME_ZONE = "Europe/Prague"

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = ["/vol/web/locale"]

ROSETTA_SHOW_AT_ADMIN_PANEL = True
# DEFAULT_CHARSET = "utf-8"

STATIC_URL = "/static/static/"
MEDIA_URL = "/static/media/"

STATIC_ROOT = "/vol/web/static"
MEDIA_ROOT = "/vol/web/media"

CRISPY_TEMPLATE_PACK = "bootstrap4"
AUTH_USER_MODEL = "uzivatel.User"

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "timestamp": {
            "format": "{asctime} {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "timestamp",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "propagate": True,
        },
        "historie": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "oznameni": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "projekt": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "heslar": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "core": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "ez": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "pian": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "uzivatel": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "arch_z": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "dokument": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "dj": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "komponenta": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "nalez": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "adb": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "pas": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "neident_akce": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}

COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "192.168.254.17"
EMAIL_PORT = "25"
EAMIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = "noreply@amcr.cz"

ACCOUNT_ACTIVATION_DAYS = 10

AUTHENTICATION_BACKENDS = ["core.authenticators.AMCRAuthUser"]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'memcached:11211',
    }
}

DIGI_LINKS = {
    "Digi_archiv_link": 'https://digiarchiv.aiscr.cz/id/',
    "OAPI_link_part1": 'https://api.aiscr.cz/dapro/oai?verb=GetRecord&identifier=https://api.aiscr.cz/id/',
    "OAPI_link_part2": '&metadataPrefix=oai_amcr',
}
# auto logout settings
AUTO_LOGOUT = {
    "IDLE_TIME": 605,
    "IDLE_WARNING_TIME": "10:00",
    "MESSAGE": AUTOLOGOUT_AFTER_LOGOUT,
    "REDIRECT_TO_LOGIN_IMMEDIATELY": True,
}
