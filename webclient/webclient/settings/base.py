import json
import os
from pathlib import Path

from core.message_constants import AUTOLOGOUT_AFTER_LOGOUT
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_PATH = "/run/logs/"


def get_secret(setting, default_value=None):
    """
    Vrací tajnou hodnotu ze settings nebo dodanou výchozí hodnotu.

    :param setting: Kolekce ``setting`` zpracovávaná touto funkcí.
    :param default_value: Parametr ``default_value`` se předává do volání ``get()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: vybranou hodnotu z kolekce, výsledek volání ``get()``.
        :raises ImproperlyConfigured: Vyvolá se při zpracování zachycené výjimky typu ``KeyError``.
    """
    file_path = (
        "/run/secrets/db_conf"
        if os.path.exists("/run/secrets/db_conf")
        # Jinak se použije cesta, pokud při inicializaci není použit Docker secret.
        # Nezachytí případ, kdy Docker secret ukazuje na chybějící lokální soubor.
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
    """
    Vrací mail secret.

    :param setting: Kolekce ``setting`` zpracovávaná touto funkcí.
    :param default_value: Parametr ``default_value`` se předává do volání ``get()``, ovlivňuje větvení podmínek, vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: vybranou hodnotu z kolekce, výsledek volání ``get()``.
        :raises ImproperlyConfigured: Vyvolá se při zpracování zachycené výjimky typu ``KeyError``.
    """
    file_mail_path = (
        "/run/secrets/mail_conf"
        if os.path.exists("/run/secrets/mail_conf")
        # Jinak se použije cesta, pokud při inicializaci není použit Docker secret.
        # Nezachytí případ, kdy Docker secret ukazuje na chybějící lokální soubor.
        else os.path.join(BASE_DIR, "webclient/settings/sample_secrets_mail_client.json")
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
    """
    Vrací plain redis pass.

    :param default_value: Parametr ``default_value`` vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``rstrip()``, proměnná ``default_value``.
    """
    if os.path.exists("/run/secrets/redis_pass"):
        with open("/run/secrets/redis_pass", "r") as file:
            return file.readline().rstrip()
    else:
        return default_value


def get_redis_pass(default_value=""):
    """
    Vrací redis pass.

    :param default_value: Parametr ``default_value`` vstupuje do návratové hodnoty.

        :return: Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, proměnná ``default_value``.
    """
    if os.path.exists("/run/secrets/redis_pass"):
        with open("/run/secrets/redis_pass", "r") as file:
            return ":" + file.readline().rstrip() + "@"
    else:
        return default_value


REDIS_HOST = get_secret("REDIS_HOST", "redis")
REDIS_PORT = get_secret("REDIS_PORT", 6379)

CACHEOPS_REDIS = f"redis://{get_redis_pass()}{REDIS_HOST}:{REDIS_PORT}/2"

CACHEOPS = {
    "lokalita.Lokalita": {"ops": (), "timeout": 60 * 10},
    "projekt.Projekt": {"ops": (), "timeout": 60 * 10},
    "arch_z.Akce": {
        "ops": (),
        "timeout": 60 * 10,
    },
    "pas.SamostatnyNalez": {"ops": (), "timeout": 60 * 10},
    "dokument.Dokument": {"ops": (), "timeout": 60 * 10},
    "ez.ExterniZdroj": {"ops": (), "timeout": 60 * 10},
    "pas.UzivatelSpoluprace": {"ops": (), "timeout": 60 * 10},
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
        "OPTIONS": {
            "options": "-c statement_timeout=90000",
        },
    },
    "urgent": {
        "ENGINE": "django_prometheus.db.backends.postgis",
        "NAME": get_secret("DB_NAME"),
        "USER": get_secret("DB_USER"),
        "PASSWORD": get_secret("DB_PASS"),
        "HOST": get_secret("DB_HOST"),
        "PORT": get_secret("DB_PORT"),
        "DISABLE_SERVER_SIDE_CURSORS": True,
        "OPTIONS": {
            "options": "-c statement_timeout=90000",
        },
    },
}

DEBUG = False

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "core.apps.AmcrAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django.contrib.sessions.backends.signed_cookies",
    "core.apps.CoreConfig",
    "uzivatel.apps.UzivatelConfig",
    "api.apps.ApiConfig",
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
    "django_registration",
    "compressor",
    "django_recaptcha",
    "widget_tweaks",
    "rosetta",
    "bs4",
    "django_extensions",
    "django_celery_beat",
    "django_celery_results",
    "django_prometheus",
    "cron",
    "rest_framework",
    "rest_framework.authtoken",
    "django_object_actions",
    "cacheops",
    "fedora_management",
    "pid.apps.PidConfig",
    "vypis",
    "crispy_bootstrap5",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.InactiveUserMiddleware",
    "django_auto_logout.middleware.auto_logout",
    "django.middleware.locale.LocaleMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
    "core.middleware.PermissionMiddleware",
    "core.middleware.ErrorMiddleware",
    "core.middleware.StatusMessageMiddleware",
    "core.log_middleware.LogMiddleware",
]


ROOT_URLCONF = "webclient.urls"

# Záložní seznam balíčků pro ``collectstatic``, když chybí ``package.json`` (např. jen adresář
# ``webclient/`` bez kořene repozitáře). Držte v souladu s ``dependencies`` v kořenovém
# ``package.json`` repozitáře.
_NPM_VENDOR_PACKAGE_NAMES = (
    "bootstrap",
    "bootstrap-datepicker",
    "bootstrap-icons",
    "bootstrap-select",
    "daterangepicker",
    "dropzone",
    "jquery",
    "leaflet",
    "leaflet-draw",
    "leaflet-fullscreen",
    "leaflet-spin",
    "leaflet.featuregroup.subgroup",
    "leaflet.markercluster",
    "moment",
    "spin.js",
)


def _npm_staticfiles_dirs():
    """
    Vrací dvojice (prefix, cesta) pro přímé závislosti z ``package.json`` v ``node_modules``.

    Omezí ``collectstatic`` jen na tyto adresáře místo celého stromu ``node_modules``.

    ``package.json`` se hledá u kořene repozitáře (``BASE_DIR.parent``) nebo vedle projektu
    (``BASE_DIR``). Chybí-li soubor nebo sekce ``dependencies``, použije se
    ``_NPM_VENDOR_PACKAGE_NAMES``.

    ``node_modules`` se hledá u ``BASE_DIR.parent``, u ``BASE_DIR`` a vedle nalezeného
    ``package.json``.

    :return: Seznam dvojic ``(jméno_balíčku, Path)`` pro existující adresáře; při chybě
        ``node_modules`` prázdný seznam.
    """
    pkg_json = None
    for candidate in (BASE_DIR.parent / "package.json", BASE_DIR / "package.json"):
        if candidate.is_file():
            pkg_json = candidate
            break

    node_root = None
    for candidate in (BASE_DIR.parent / "node_modules", BASE_DIR / "node_modules"):
        if candidate.is_dir():
            node_root = candidate
            break
    if node_root is None and pkg_json is not None:
        fallback_root = pkg_json.parent / "node_modules"
        if fallback_root.is_dir():
            node_root = fallback_root

    if node_root is None:
        return []

    deps = {}
    if pkg_json is not None:
        try:
            with open(pkg_json, encoding="utf-8") as f:
                data = json.load(f)
            deps = data.get("dependencies") or {}
        except (OSError, json.JSONDecodeError):
            deps = {}

    names = sorted(deps) if deps else sorted(_NPM_VENDOR_PACKAGE_NAMES)

    out = []
    for name in names:
        pkg_path = node_root / name
        if pkg_path.is_dir():
            out.append((name, pkg_path))
    return out


STATICFILES_DIRS = [BASE_DIR / "static", *_npm_staticfiles_dirs()]

STORAGES = {
    "staticfiles": {
        "BACKEND": "core.storage.NonStrictManifestStaticFilesStorage",
    },
}

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
                "core.context_processors.logout_next_url",
                "core.context_processors.auto_logout_client",  # pro automatické odhlášení po nečinnosti
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

FORMAT_MODULE_PATH = ["webclient.formats"]

USE_TZ = True

LOCALE_PATHS = ["/vol/web/locale"]

ROSETTA_SHOW_AT_ADMIN_PANEL = False
ROSETTA_WSGI_AUTO_RELOAD = False
ROSETTA_UWSGI_AUTO_RELOAD = False


def rosetta_translation_rights(user):
    """
    Provádí operaci rosetta translation rights.

    :param user: Parametr ``user`` pracuje se s atributy ``groups``, vstupuje do návratové hodnoty.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
    """
    from core.constants import ROLE_UPRAVA_TEXTU

    return user.groups.filter(id=ROLE_UPRAVA_TEXTU).count() > 0


ROSETTA_ACCESS_CONTROL_FUNCTION = rosetta_translation_rights
# DEFAULT_CHARSET = "utf-8"

STATIC_URL = "/static/static/"
MEDIA_URL = "/static/media/"

STATIC_ROOT = "/vol/web/static"
MEDIA_ROOT = "/vol/web/media"

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
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
    "filters": {
        "user_filter": {
            "()": "core.logging_filters.UserLogFilter",
        }
    },
    "handlers": {
        "logstash": {
            "level": "DEBUG",
            "class": "logstash.TCPLogstashHandler",
            "host": "logstash",
            "port": 5959,
            "version": 1,
            "message_type": "logstash",
            "fqdn": False,
            "filters": ["user_filter"],
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "timestamp",
        },
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
        "request.timer": {
            "handlers": ["logstash", "console"],
            "level": "INFO",
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
        "pid": {
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
        "fedora_management": {
            "handlers": ["logstash", "console"],
            "level": "DEBUG",
        },
        "vypis": {
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
        "LOCATION": f"redis://{get_redis_pass()}{REDIS_HOST}:{REDIS_PORT}",
    }
}

API_URL = get_secret("API_URL", "https://api.aiscr.cz/id/")

DIGI_LINKS = {
    "Digi_archiv_link": get_secret("DIGIARCHIV_URL", "https://digiarchiv.aiscr.cz/id/"),
    "OAPI_link": API_URL,
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
    "MAINTENANCE_CACHE_TIMEOUT": 600,
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

SHOW_DARK_MODE = get_secret("SHOW_DARK_MODE", "True") == "True"

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

DATACITE_URL = get_secret("DATACITE_URL", "")
DOI_USER = get_secret("DOI_USER", "")
DOI_USER_PASSWORD = get_secret("DOI_USER_PASSWORD", "")
IGSN_USER = get_secret("IGSN_USER", "")
IGSN_USER_PASSWORD = get_secret("IGSN_USER_PASSWORD", "")
DOI_PREFIX = get_secret("DOI_PREFIX", "")
IGSN_PREFIX = get_secret("IGSN_PREFIX", "")

DIGIARCHIV_SERVER_URL = get_secret("DIGIARCHIV_SERVER_URL", "https://digiarchiv.aiscr.cz/")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ]
}
TOKEN_EXPIRATION_HOURS = 24

# Minimální interval (v milisekundách) mezi dvěma po sobě jdoucími požadavky
# na PAS API. Limit se aplikuje globálně na všechny uživatele a IP adresy
# (na rozdíl od rate_limits v ``CustomAdminSettings``, kde se nastavuje
# per-uživatel nebo per-IP). Hodnota 0 znamená, že limit není aktivní.
API_MIN_REQUEST_INTERVAL_USER_MS = 0
API_MIN_REQUEST_INTERVAL_IP_MS = 0

SKIP_RECAPTCHA = False

TEST_ENV = get_secret("TEST_ENV", "True") == "True"

CLAMD_HOST = None
CLAMD_PORT = None
CLAMD_TIMEOUT = 600

DIGIARCHIV_URL = get_secret("DIGIARCHIV_URL", "https://digiarchiv.aiscr.cz/id/")

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

EMAIL_ZADOST_UDAJE_OZNAMOVATELE = "info@amapa.cz"
