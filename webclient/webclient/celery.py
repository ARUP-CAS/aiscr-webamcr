# django_celery/celery.py


import os

from celery import Celery

if os.getenv("DJANGO_SETTINGS_MODULE") is None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webclient.settings.production")

app = Celery("webclient")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.update(worker_send_task_events=True, task_send_sent_event=True)
