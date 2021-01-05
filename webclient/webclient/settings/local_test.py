from .dev import *

# DATABASES["default"] = {"ENGINE": "django.db.backends.sqlite3"}
DATABASES["default"] = {"ENGINE": "django.contrib.gis.db.backends.spatialite"}
