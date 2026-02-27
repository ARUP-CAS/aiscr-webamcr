from django.apps import AppConfig


class ProjektConfig(AppConfig):
    """Zapouzdřuje chování třídy ``ProjektConfig`` pro modul ``webclient.projekt.apps``."""
    name = "projekt"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(ProjektConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import projekt.signals
