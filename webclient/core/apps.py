from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class AmcrAdminConfig(AdminConfig):
    """Vlastní konfigurace admin aplikace s přizpůsobeným admin site."""

    default_site = "core.admin_sites.AmcrCustomAdminSite"


class CoreConfig(AppConfig):
    """Implementuje komponentu ``CoreConfig`` v rámci aplikace."""

    name = "core"

    def ready(self):
        """Provádí operaci ready."""
        super(CoreConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import core.signals
