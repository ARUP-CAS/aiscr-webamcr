from django.apps import AppConfig


class EzConfig(AppConfig):
    """Zapouzdřuje chování třídy ``EzConfig`` pro modul ``webclient.ez.apps``."""
    name = "ez"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(EzConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import ez.signals
