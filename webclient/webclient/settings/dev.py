import socket

from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += [
    "debug_toolbar",
    "widget_tweaks",
    "django_extensions",
    "template_profiler_panel",
]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

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
    "template_profiler_panel.panels.template.TemplateProfilerPanel",
]

# This is only so that debug toolbar is shown when developing in docker
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[:-1] + "1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]

CRISPY_FAIL_SILENTLY = not DEBUG

SILENCED_SYSTEM_CHECKS = ["captcha.recaptcha_test_key_error"]

TEST_RUNNER = "core.tests.runner.AMCRTestRunner"

INSTALLED_APPS.insert(0, "livereload")
MIDDLEWARE.append("livereload.middleware.LiveReloadScript")

STATIC_ROOT = ""

SHELL_PLUS = "plain"
SHELL_PLUS_PRINT_SQL = True

# Development keys
# RECAPTCHA_PUBLIC_KEY ="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
# RECAPTCHA_PRIVATE_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"

# Send emails to FTP
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = "/vol/web/media/emails/"
