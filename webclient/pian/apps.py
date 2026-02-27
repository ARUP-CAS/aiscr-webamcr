from django.apps import AppConfig


class PianConfig(AppConfig):
    """Zapouzdřuje chování třídy ``PianConfig`` pro modul ``webclient.pian.apps``."""
    name = "pian"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(PianConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import pian.signals
