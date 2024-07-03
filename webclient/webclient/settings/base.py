import json
import os
from pathlib import Path


from core.message_constants import AUTOLOGOUT_AFTER_LOGOUT
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_PATH = "/run/logs/"


def get_secret(setting, default_value=None):
    file_path = (
        "/run/secrets/db_conf"
        if os.path.exists("/run/secrets/db_conf")
        # else path will be used in case a docker secret is not used during instantiation.
        # Doesn't catch case where docker secrets points to missing file on local disk.
        else os.path.join(BASE_DIR, "webclient/settings/sample_secrets_db.json")
    )

    with open(file_path, "r") as f:
        secrets = json.load(f)
    if setting != "RECAPTCHA_PRIVATE_KEY":
        if default_value is None:
            try:
                return secrets[setting]
            except KeyError:
                error_msg = error_msg = f"Add {setting} variable to {file_path} file"
                raise ImproperlyConfigured(error_msg)
        else:
            return secrets.get(setting, default_value)
    else:
        return secrets.get(setting, "X")


def get_mail_secret(setting, default_value=None):
    file_mail_path = (
        "/run/secrets/mail_conf"
        if os.path.exists("/run/secrets/mail_conf")
        # else path will be used in case a docker secret is not used during instantiation.
        # Doesn't catch case where docker secrets points to missing file on local disk.
        else os.path.join(
            BASE_DIR, "webclient/settings/sample_secrets_mail_client.json"
        )
    )
    with open(file_mail_path, "r") as file:
        secrets_mail = json.load(file)
    if default_value is None:
        try:
            return secrets_mail[setting]
        except KeyError:
            error_msg = f"Add {setting} variable to {file_mail_path} file"
            if not DEBUG:
                raise ImproperlyConfigured(error_msg)
    else:
        return secrets_mail.get(setting, default_value)


# REDIS SETTINGS
def get_plain_redis_pass(default_value=""):
    if os.path.exists("/run/secrets/redis_pass"):
        with open("/run/secrets/redis_pass", "r") as file:
            return file.readline().rstrip()
    else:
        return default_value


def get_redis_pass(default_value=""):
    if os.path.exists("/run/secrets/redis_pass"):
        with open("/run/secrets/redis_pass", "r") as file:
            return ":" + file.readline().rstrip() + "@"
    else:
        return default_value

REDIS_HOST = get_secret("REDIS_HOST")
REDIS_PORT = get_secret("REDIS_PORT")

CACHEOPS_REDIS = f"redis://{get_redis_pass()}{REDIS_HOST}:{REDIS_PORT}"

CACHEOPS = {
    "adb.Adb": {"ops": ("fetch", ), "timeout": 60*10},
    "arch_z.Akce": {"ops": ("fetch", ), "timeout": 60*10},
    "arch_z.ArcheologickyZaznam": {"ops": ("fetch", ), "timeout": 60*10},
    "projekt.Projekt": {"ops": ("fetch", ), "timeout": 60*10},
    "ez.ExterniZdroj": {"ops": ("fetch", ), "timeout": 60*10},
    "dokument.Dokument": {"ops": ("fetch", ), "timeout": 60*10},
    "dokument.DokumentExtraData": {"ops": ("fetch", ), "timeout": 60*10},
    "historie.Historie": {"ops": ("fetch", ), "timeout": 60*10},
    "pas.SamostatnyNalez": {"ops": ("fetch", ), "timeout": 60*10},
    "core.Permissions": {"ops": ("fetch", ), "timeout": 60*60},
    "komponenta.Komponenta": {"ops": ("fetch", ), "timeout": 60*10},
    "pian.Pian": {"ops": ("fetch", ), "timeout": 60*10},
    "nalez.*": {"ops": ("fetch", ), "timeout": 60*10},
    "lokalita.Lokalita": {"ops": ("fetch", ), "timeout": 60*10},
    "dj.DokumentacniJednotka": {"ops": ("fetch", ), "timeout": 60*10},
    "uzivatel.User": {"ops": ("fetch", ), "timeout": 60},
}

SECRET_KEY = get_secret("SECRET_KEY")

DATABASES = {
    "default": {
        "ENGINE": "django_prometheus.db.backends.postgis",
        "NAME": get_secret("DB_NAME"),
        "USER": get_secret("DB_USER"),
        "PASSWORD": get_secret("DB_PASS"),
        "HOST": get_secret("DB_HOST"),
        "PORT": get_secret("DB_PORT"),
        "ATOMIC_REQUESTS": True,
        "DISABLE_SERVER_SIDE_CURSORS": True,
        'OPTIONS': {
            'options': '-c statement_timeout=90000',         
        },
    },
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
    "django.contrib.sessions.backends.signed_cookies",
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
    "lokalita",
    "notifikace_projekty",
    "dal",
    "dal_select2",
    "django_filters",
    "django_tables2",
    "django_tables2_column_shifter",
    "crispy_forms",
    "crispy_bootstrap4",
    "django_registration",
    "compressor",
    "django_recaptcha",
    "widget_tweaks",
    "rosetta",
    "bs4",
    "django_extensions",
    "django_celery_beat",
    "django_celery_results",
    'django_prometheus',
    "cron",
    'rest_framework',
    'rest_framework.authtoken',
    "django_object_actions",
    "cacheops",
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.TestEnvPopupMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_auto_logout.middleware.auto_logout",
    "django.middleware.locale.LocaleMiddleware",
    'django_prometheus.middleware.PrometheusAfterMiddleware',
    'core.middleware.PermissionMiddleware',
    'core.middleware.ErrorMiddleware',
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
    BASE_DIR / "static" / "fonts",
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
                "core.context_processors.main_shows",
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
DATE_FORMAT = "d.m.Y"
DATE_INPUT_FORMATS = ["%-d.%-m.%Y","%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"]

USE_TZ = True

LOCALE_PATHS = ["/vol/web/locale"]

ROSETTA_SHOW_AT_ADMIN_PANEL = False
ROSETTA_WSGI_AUTO_RELOAD = False
ROSETTA_UWSGI_AUTO_RELOAD = False


def rosetta_translation_rights(user):
    from core.constants import ROLE_UPRAVA_TEXTU

    return user.groups.filter(id=ROLE_UPRAVA_TEXTU).count() > 0


ROSETTA_ACCESS_CONTROL_FUNCTION = rosetta_translation_rights
# DEFAULT_CHARSET = "utf-8"

STATIC_URL = "/static/static/"
MEDIA_URL = "/static/media/"

STATIC_ROOT = "/vol/web/static"
MEDIA_ROOT = "/vol/web/media"

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
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
        'logstash': {
            'level': 'DEBUG',
            'class': 'logstash.TCPLogstashHandler',
            'host': 'logstash',
            'port': 5959,
            'version': 1,
            'message_type': 'logstash',
            'fqdn': False,
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "timestamp",
        }
    },
    "loggers": {
        "django": {
            "handlers": ["logstash", "console"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["logstash", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        "tests": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "historie": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "oznameni": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "projekt": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "heslar": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "core": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "cron": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "ez": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "pian": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "uzivatel": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "arch_z": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "dokument": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "dj": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "komponenta": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "nalez": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "adb": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "pas": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "lokalita": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "neidentakce": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "services": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "django_cron": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "notifikace_projekty": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "xml_generator": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "healthcheck": {
            "handlers": ["logstash", "console"],
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
EMAIL_SERVER_DOMAIN_NAME = get_mail_secret("EMAIL_SERVER_DOMAIN_NAME", "http://mailtrap.io")
# DEFAULT_FROM_EMAIL = "noreply@amcr.cz"

ACCOUNT_ACTIVATION_DAYS = 10

AUTHENTICATION_BACKENDS = ["core.authenticators.AMCRAuthUser"]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{get_redis_pass()}{REDIS_HOST}:{REDIS_PORT}" ,
    }
}

DIGI_LINKS = {
    "Digi_archiv_link": "https://digiarchiv.aiscr.cz/id/",
    "OAPI_link": "https://api.aiscr.cz/id/",
    "ARU_PRAHA": "https://www.arup.cas.cz/",
    "ARU_BRNO": "https://www.arub.cz/",
    "ARUP_MAIL": '<a href="mailto:oznameni@arup.cas.cz">oznameni@arup.cas.cz</a>',
    "ARUB_MAIL": "<a href='mailto:oznameni@arub.cz'>oznameni@arub.cz</a>",
}

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

# CELERY SETTINGS
CELERY_REDIRECT_STDOUTS = False
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

SKIP_SELENIUM_TESTS = False

CELERY_BROKER_URL = f"redis://{get_redis_pass()}{REDIS_HOST}:{REDIS_PORT}"
CELERY_RESULT_BACKEND = "django-db"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

FEDORA_USER = get_secret("FEDORA_USER", "")
FEDORA_USER_PASSWORD = get_secret("FEDORA_USER_PASSWORD", "")
FEDORA_SERVER_HOSTNAME = get_secret("FEDORA_SERVER_HOSTNAME", "")
FEDORA_SERVER_NAME = get_secret("FEDORA_SERVER_NAME", "")
FEDORA_PORT_NUMBER = get_secret("FEDORA_PORT_NUMBER", "")
FEDORA_ADMIN_USER = get_secret("FEDORA_ADMIN_USER", "")
FEDORA_ADMIN_USER_PASSWORD = get_secret("FEDORA_ADMIN_USER_PASSWORD", "")
FEDORA_PROTOCOL = get_secret("FEDORA_PROTOCOL", "https")
FEDORA_TRANSACTION_URL = get_secret("FEDORA_TRANSACTION_URL", "")

DIGIARCHIV_SERVER_URL = get_secret("DIGIARCHIV_SERVER_URL", "https://digiarchiv.aiscr.cz/")

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ]
}
TOKEN_EXPIRATION_HOURS = 24

SKIP_RECAPTCHA = False

TEST_ENV = os.getenv("TEST_ENV_SETTING", False)

CLAMD_HOST = None
CLAMD_PORT = None
