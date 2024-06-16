import socket

from .base import *

DEBUG = True
USE_I18N = get_secret("USE_I18N", "true").lower() == "true"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += [
    "debug_toolbar",
]

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware",] + MIDDLEWARE

DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.history.HistoryPanel",
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.logging.LoggingPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
]

# This is only so that debug toolbar is shown when developing in docker
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[:-1] + "1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]

CRISPY_FAIL_SILENTLY = not DEBUG

SILENCED_SYSTEM_CHECKS = ["captcha.recaptcha_test_key_error"]

TEST_RUNNER = "core.tests.runner.AMCRSeleniumTestRunner"

INSTALLED_APPS.insert(0, "livereload")
MIDDLEWARE.append("livereload.middleware.LiveReloadScript")

SHELL_PLUS = "plain"
SHELL_PLUS_PRINT_SQL = True

# Development keys
# RECAPTCHA_PUBLIC_KEY =""
# RECAPTCHA_PRIVATE_KEY = ""

# Send emails to FTP
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = "/vol/web/media/emails/"

# auto logout settings
AUTO_LOGOUT = {}
SITE_URL = 'http://localhost:8000'

# Fake key
RECAPTCHA_PRIVATE_KEY = "OtKcTKoJwtIyCm0XFEf0EA5kVMV4hHaDaJfmyr"
RECAPTCHA_PUBLIC_KEY = ""
SKIP_RECAPTCHA = True

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda _request: DEBUG,
}
