from django.apps import AppConfig


class PidConfig(AppConfig):
    """Zapouzdřuje chování třídy ``PidConfig`` pro modul ``webclient.pid.apps``."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "pid"
