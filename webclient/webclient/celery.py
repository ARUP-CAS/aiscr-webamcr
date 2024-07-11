# django_celery/celery.py


import os

from celery import Celery
from celery.schedules import crontab   


if os.getenv("DJANGO_SETTINGS_MODULE") is None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webclient.settings.production")

app = Celery("webclient")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
