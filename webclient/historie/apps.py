from django.apps import AppConfig


class HistorieConfig(AppConfig):
    """Zapouzdřuje chování třídy ``HistorieConfig`` pro modul ``webclient.historie.apps``."""
    name = "historie"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(HistorieConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import historie.signals
