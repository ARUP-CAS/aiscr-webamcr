from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Zapouzdřuje chování třídy ``CoreConfig`` pro modul ``webclient.core.apps``."""
    name = "core"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(CoreConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import core.signals
