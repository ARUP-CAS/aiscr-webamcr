from django.apps import AppConfig


class UzivatelConfig(AppConfig):
    """Zapouzdřuje chování třídy ``UzivatelConfig`` pro modul ``webclient.uzivatel.apps``."""
    name = "uzivatel"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(UzivatelConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import uzivatel.signals
