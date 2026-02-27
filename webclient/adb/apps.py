from django.apps import AppConfig


class AdbConfig(AppConfig):
    """Zapouzdřuje chování třídy ``AdbConfig`` pro modul ``webclient.adb.apps``."""
    name = "adb"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(AdbConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import adb.signals
