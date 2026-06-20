from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Konfigurace Django aplikace ``api`` — registruje signály při startu.

    Atribut ``default_auto_field`` cíleně NEPŘEPISUJEME — historicky byla tabulka
    ``api_log_pozadavku`` vytvořena v aplikaci ``core`` s ``AutoField`` PK. Nová
    aplikace musí ponechat projektový default (``DEFAULT_AUTO_FIELD = "django.db.models.AutoField"``
    v ``settings/base.py``), jinak by ``makemigrations`` opakovaně generoval
    ``AlterField`` na PK a vznikla by drift mezi modelem a skutečným schématem.
    """

    name = "api"

    def ready(self):
        """Načte signály při startu aplikace."""
        from api import signals  # noqa: F401
