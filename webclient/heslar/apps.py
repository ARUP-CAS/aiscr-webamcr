from django.apps import AppConfig


class HeslarConfig(AppConfig):
    """Zapouzdřuje chování třídy ``HeslarConfig`` pro modul ``webclient.heslar.apps``."""
    name = "heslar"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(HeslarConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import heslar.signals
