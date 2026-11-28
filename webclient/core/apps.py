from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class AmcrAdminConfig(AdminConfig):
    """Vlastní konfigurace admin aplikace s přizpůsobeným admin site."""

    default_site = "core.admin_sites.AmcrCustomAdminSite"


class CoreConfig(AppConfig):
    """Implementuje komponentu ``CoreConfig`` v rámci aplikace."""

    name = "core"

    def ready(self):
        """
        Registruje signály modulu core při startu aplikace.

        Kromě signálů modelů připojí kontrolu runtime překladových katalogů na signál Celery
        ``task_prerun``, aby úlohy překládaly podle aktuálních katalogů bez restartu workeru.
        """
        super(CoreConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import core.signals
        from core.translation import connect_translation_catalog_signals

        connect_translation_catalog_signals()
