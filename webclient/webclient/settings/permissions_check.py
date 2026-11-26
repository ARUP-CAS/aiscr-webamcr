"""Izolované nastavení pro kontrolu matice bez přístupu k externím službám."""

from .docs import *  # noqa: F401,F403
from .docs import DATABASES as DOCS_DATABASES
from .docs import LOGGING as DOCS_LOGGING

# Importy URL načítají některé číselníky při startu. Backend zachová SQL
# kompilátor PostGIS, ale odmítne vytvoření skutečného databázového spojení.
DATABASES = {name: {**config, "ENGINE": "webclient.permission_check_db"} for name, config in DOCS_DATABASES.items()}
CACHEOPS_ENABLED = False
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
LOGGING = {
    **DOCS_LOGGING,
    "handlers": {**DOCS_LOGGING["handlers"], "permission_check_null": {"class": "logging.NullHandler"}},
    "loggers": {
        **DOCS_LOGGING["loggers"],
        "heslar": {"handlers": ["permission_check_null"], "level": "CRITICAL", "propagate": False},
    },
}
