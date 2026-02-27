from django.apps import AppConfig


class DjConfig(AppConfig):
    """Zapouzdřuje chování třídy ``DjConfig`` pro modul ``webclient.dj.apps``."""
    name = "dj"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(DjConfig, self).ready()
        import dj.signals
