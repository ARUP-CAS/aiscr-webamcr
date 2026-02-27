from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Zapouzdřuje chování třídy ``CoreConfig`` pro modul ``webclient.core.apps``."""
    name = "core"

    def ready(self):
        """Provádí funkci ``CoreConfig.ready`` v rámci modulu ``webclient.core.apps``."""
        super(CoreConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import core.signals
