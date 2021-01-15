import socket

from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += [
    "debug_toolbar",
]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# This is only so that debug toolbar is shown when developing in docker
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[:-1] + "1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]

CRISPY_FAIL_SILENTLY = not DEBUG

SILENCED_SYSTEM_CHECKS = ["captcha.recaptcha_test_key_error"]

TEST_RUNNER = "core.tests.runner.AMCRTestRunner"
