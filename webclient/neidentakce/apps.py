from django.apps import AppConfig


class NeidentakceConfig(AppConfig):
    """Zapouzdřuje chování třídy ``NeidentakceConfig`` pro modul ``webclient.neidentakce.apps``."""
    name = "neidentakce"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(NeidentakceConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import neidentakce.signals
