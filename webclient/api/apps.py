from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Konfigurace Django aplikace ``api`` — registruje signály při startu."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        """Načte signály při startu aplikace."""
        from api import signals  # noqa: F401
