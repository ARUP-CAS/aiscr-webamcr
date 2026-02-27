from django.apps import AppConfig


class NalezConfig(AppConfig):
    """Zapouzdřuje chování třídy ``NalezConfig`` pro modul ``webclient.nalez.apps``."""
    name = "nalez"

    def ready(self):
        """Provádí funkci ``NalezConfig.ready`` v rámci modulu ``webclient.nalez.apps``."""
        super(NalezConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import nalez.signals
