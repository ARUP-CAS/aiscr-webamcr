from django.apps import AppConfig


class ProjektConfig(AppConfig):
    """Zapouzdřuje chování třídy ``ProjektConfig`` pro modul ``webclient.projekt.apps``."""
    name = "projekt"

    def ready(self):
        """Provádí funkci ``ProjektConfig.ready`` v rámci modulu ``webclient.projekt.apps``."""
        super(ProjektConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import projekt.signals
