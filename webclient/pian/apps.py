from django.apps import AppConfig


class PianConfig(AppConfig):
    """Zapouzdřuje chování třídy ``PianConfig`` pro modul ``webclient.pian.apps``."""
    name = "pian"

    def ready(self):
        """Provádí funkci ``PianConfig.ready`` v rámci modulu ``webclient.pian.apps``."""
        super(PianConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import pian.signals
