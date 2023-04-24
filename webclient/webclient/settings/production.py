from .base import *

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "proxy", "192.168.254.24", "192.168.254.30"]

RECAPTCHA_PUBLIC_KEY = "6LcgsmQaAAAAAPqzAQkryJGl34AWzU3DsN9Pyf__"
RECAPTCHA_PRIVATE_KEY = get_secret("RECAPTCHA_PRIVATE_KEY")

SITE_URL = 'http://192.168.254.30:8080'
DEFAULT_FROM_EMAIL = "info@amapa.cz"
