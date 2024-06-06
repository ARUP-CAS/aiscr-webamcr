from .dev import *

LOGGING["handlers"]["logstash"]["tags"] = "dev_test"

if "debug_toolbar" in INSTALLED_APPS: INSTALLED_APPS.remove("debug_toolbar")
if "debug_toolbar.middleware.DebugToolbarMiddleware" in MIDDLEWARE: MIDDLEWARE.remove("debug_toolbar.middleware.DebugToolbarMiddleware")
DEBUG_TOOLBAR_PANELS=[]

SELENIMUM_ADDRESS = 'selenium'
SELENIUM_PORT='4444'
WEB_SERVER_ADDRESS='web' #adresa na které běží test a kterou použije selenium
TEST_DATABASE_NAME="test_vzor" #jmeno vzorové databáze, která se klonuje
USE_REMOTE_WEB_BROWSER=True

FEDORA_SERVER_NAME = "AMCR-selenium-test"
FEDORA_SERVER_HOSTNAME = "192.168.254.24"
FEDORA_PORT_NUMBER = 8081
FEDORA_PROTOCOL = "http"
FEDORA_PATH = "/opt/fcrepo/fcrepo-home/data/ocfl-root"

TEST_SCREENSHOT_PATH = "/vol/web/selenium_test/"
DATABASES["default"]['TEST']={'MIGRATE': False}

EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = "/vol/web/selenium_test"  
LOGGING["handlers"]["console"]["level"]="ERROR"
SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']

DATABASES["test_db"] = {   
        "ENGINE": "django_prometheus.db.backends.postgis",
        "NAME": TEST_DATABASE_NAME,
        "USER": get_secret("DB_USER"),
        "PASSWORD": get_secret("DB_PASS"),
        "HOST": get_secret("DB_HOST"),
        "PORT": get_secret("DB_PORT"),
        "ATOMIC_REQUESTS": True,
        "DISABLE_SERVER_SIDE_CURSORS": True,   
}
