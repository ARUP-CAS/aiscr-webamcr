from django.apps import AppConfig


class DjConfig(AppConfig):
    """Zapouzdřuje chování třídy ``DjConfig`` pro modul ``webclient.dj.apps``."""
    name = "dj"

    def ready(self):
        """Provádí funkci ``DjConfig.ready`` v rámci modulu ``webclient.dj.apps``."""
        super(DjConfig, self).ready()
        import dj.signals
