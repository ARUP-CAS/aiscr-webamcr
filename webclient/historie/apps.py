from django.apps import AppConfig


class HistorieConfig(AppConfig):
    """Zapouzdřuje chování třídy ``HistorieConfig`` pro modul ``webclient.historie.apps``."""
    name = "historie"

    def ready(self):
        """Provádí funkci ``HistorieConfig.ready`` v rámci modulu ``webclient.historie.apps``."""
        super(HistorieConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import historie.signals
