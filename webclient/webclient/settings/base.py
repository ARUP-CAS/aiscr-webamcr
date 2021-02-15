import json
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent

file_path = ""
if os.path.exists("webclient/settings/secrets.json"):
    file_path = "webclient/settings/secrets.json"
else:
    # This is secrets file for the tests
    file_path = "webclient/settings/secrets_test.json"

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
    }
}

DEBUG = False

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django_filters",
    "crispy_forms",
    "captcha",
    "core",
    "historie",
    "oznameni",
    "projekt.apps.ProjektConfig",
    "heslar",
    "uzivatel.apps.UzivatelConfig",
    "pian",
    "arch_z.apps.ArchZConfig",
    "dokument",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# DEFAULT_CHARSET = "utf-8"

STATIC_URL = "/static/static/"
MEDIA_URL = "/static/media/"

STATIC_ROOT = "/vol/web/static"
MEDIA_ROOT = "/vol/web/media"

CRISPY_TEMPLATE_PACK = "bootstrap4"
AUTH_USER_MODEL = "uzivatel.User"

LOGIN_REDIRECT_URL = "/"

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
        "historie": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "core": {
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
    },
}
