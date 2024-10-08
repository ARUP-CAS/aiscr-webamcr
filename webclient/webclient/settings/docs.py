from .base import *

DEBUG = True

INSTALLED_APPS.remove("django_prometheus")

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
        }
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",
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
