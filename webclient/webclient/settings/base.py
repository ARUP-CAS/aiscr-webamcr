import json
import os
from pathlib import Path

import structlog
from core.message_constants import AUTOLOGOUT_AFTER_LOGOUT
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent

file_path = (
    "/run/secrets/db_conf"
    if os.path.exists("/run/secrets/db_conf")
    # else path will be used in case a docker secret is not used during instantiation. 
    # Doesn't catch case where docker secrets points to missing file on local disk.
    else os.path.join(BASE_DIR,"webclient/settings/sample_secrets_db.json")
)

with open(file_path, "r") as f:
    secrets = json.load(f)


def get_secret(setting, default_value=None):
    if default_value is None:
        try:
            return secrets[setting]
        except KeyError:
            error_msg = "Add {0} variable to secrets.json file".format(setting)
            raise ImproperlyConfigured(error_msg)
    else:
        secrets.get(setting, default_value)


def get_mail_secret(setting, default_value=None):
    file_mail_path = (
        "/run/secrets/mail_conf"
        if os.path.exists("/run/secrets/mail_conf")
        # else path will be used in case a docker secret is not used during instantiation.
        # Doesn't catch case where docker secrets points to missing file on local disk.
        else os.path.join(BASE_DIR, "webclient/settings/sample_secrets_mail_client.json")
    )
    with open(file_mail_path, "r") as file:
        secrets_mail = json.load(file)
    if default_value is None:
        try:
            return secrets_mail[setting]
        except KeyError:
            error_msg = "Add {0} variable to secrets.json file".format(setting)
            raise ImproperlyConfigured(error_msg)
    else:
        secrets_mail.get(setting, default_value)


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
    "core.apps.CoreConfig",
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
    "django_cron",
    "lokalita",
    "bs4",
    "django_extensions",
    "watchdog",
    'django_select2',
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
    "django_structlog.middlewares.RequestMiddleware",
    "django_auto_logout.middleware.auto_logout",
    "django.middleware.locale.LocaleMiddleware",
]

CRON_CLASSES = [
    "cron.job01.MyCronJobPianToJTSK",
    "cron.job02.MyCronJobPianToWGS84",
    "cron.notifications.Notifications",
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
        "DIRS": [BASE_DIR / "templates", "/vol/web/nginx/data"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.constants_import",
                "core.context_processors.digi_links_from_settings",
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
    ("cs", "Czech"),
    ("en", "English"),
]

TIME_ZONE = "Europe/Prague"

USE_I18N = True

USE_L10N = False
DATE_FORMAT = "%d.%m.%Y"
DATE_INPUT_FORMATS = [
    "%d.%m.%Y",
    '%d/%m/%Y',
    '%Y-%m-%d'
]

USE_TZ = True

LOCALE_PATHS = ["/vol/web/locale"]

ROSETTA_SHOW_AT_ADMIN_PANEL = True
ROSETTA_WSGI_AUTO_RELOAD = True
ROSETTA_UWSGI_AUTO_RELOAD = True


def rosetta_translation_rights(user):
    from core.constants import ROLE_UPRAVA_TEXTU
    return user.groups.filter(id=ROLE_UPRAVA_TEXTU).count() > 0


ROSETTA_ACCESS_CONTROL_FUNCTION = rosetta_translation_rights
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
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
        },
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
        "cron": {
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
        "lokalita": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "neidentakce": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "services": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "django_cron": {
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
EMAIL_HOST = get_mail_secret("EMAIL_HOST")
EMAIL_PORT = get_mail_secret("EMAIL_PORT")
EMAIL_HOST_USER = get_mail_secret("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = get_mail_secret("EMAIL_HOST_PASSWORD")
EMAIL_SERVER_DOMAIN_NAME = get_mail_secret("EMAIL_SERVER_DOMAIN_NAME", "")
# DEFAULT_FROM_EMAIL = "noreply@amcr.cz"

ACCOUNT_ACTIVATION_DAYS = 10

AUTHENTICATION_BACKENDS = ["core.authenticators.AMCRAuthUser"]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": "memcached:11211",
    }
}

DIGI_LINKS = {
    "Digi_archiv_link": "https://digiarchiv.aiscr.cz/id/",
    "OAPI_link_part1": "https://api.aiscr.cz/dapro/oai?verb=GetRecord&identifier=https://api.aiscr.cz/id/",
    "OAPI_link_part2": "&metadataPrefix=oai_amcr",
    "ARU_PRAHA": "https://www.arup.cas.cz/",
    "ARU_BRNO": "https://www.arub.cz/",
    "ARUP_MAIL": '<a href="mailto:oznameni@arup.cas.cz">oznameni@arup.cas.cz</a>',
    "ARUB_MAIL": "<a href='mailto:oznameni@arub.cas.cz'>oznameni@arub.cz</a>",
}

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
# auto logout settings
AUTO_LOGOUT = {
    "IDLE_TIME": 3600,
    "MAINTENANCE_LOGOUT_TIME": 600,
    "MESSAGE": AUTOLOGOUT_AFTER_LOGOUT,
    "REDIRECT_TO_LOGIN_IMMEDIATELY": True,
    "IDLE_WARNING_TIME": 600,
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

COMPRESS_REBUILD_TIMEOUT = 3600
