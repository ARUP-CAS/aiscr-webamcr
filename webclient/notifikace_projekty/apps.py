from django.apps import AppConfig


class NotifikaceProjektyConfig(AppConfig):
    """Zapouzdřuje chování třídy ``NotifikaceProjektyConfig`` pro modul ``webclient.notifikace_projekty.apps``."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifikace_projekty"

    def ready(self):
        """Zajišťuje logiku funkce ``ready``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(NotifikaceProjektyConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import notifikace_projekty.signals
