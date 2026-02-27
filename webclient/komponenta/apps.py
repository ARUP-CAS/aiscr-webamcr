from django.apps import AppConfig


class KomponentaConfig(AppConfig):
    """Zapouzdřuje chování třídy ``KomponentaConfig`` pro modul ``webclient.komponenta.apps``."""
    name = "komponenta"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(KomponentaConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import komponenta.signals
