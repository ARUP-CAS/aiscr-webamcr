from django.apps import AppConfig


class ArchZConfig(AppConfig):
    """Zapouzdřuje chování třídy ``ArchZConfig`` pro modul ``webclient.arch_z.apps``."""
    name = "arch_z"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(ArchZConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import arch_z.signals
