from django.apps import AppConfig


class DokumentConfig(AppConfig):
    """Zapouzdřuje chování třídy ``DokumentConfig`` pro modul ``webclient.dokument.apps``."""
    name = "dokument"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(DokumentConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import dokument.signals
