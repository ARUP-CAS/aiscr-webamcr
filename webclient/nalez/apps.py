from django.apps import AppConfig


class NalezConfig(AppConfig):
    """Zapouzdřuje chování třídy ``NalezConfig`` pro modul ``webclient.nalez.apps``."""
    name = "nalez"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(NalezConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import nalez.signals
