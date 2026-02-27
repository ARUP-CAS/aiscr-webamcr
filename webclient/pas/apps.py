from django.apps import AppConfig


class PasConfig(AppConfig):
    """Zapouzdřuje chování třídy ``PasConfig`` pro modul ``webclient.pas.apps``."""
    name = "pas"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(PasConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import pas.signals
