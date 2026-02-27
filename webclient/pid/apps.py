from django.apps import AppConfig


class PidConfig(AppConfig):
    """Třída `PidConfig` v modulu `webclient.pid.apps`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "pid"
