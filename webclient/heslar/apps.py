from django.apps import AppConfig


class HeslarConfig(AppConfig):
    """Zapouzdřuje chování třídy ``HeslarConfig`` pro modul ``webclient.heslar.apps``."""
    name = "heslar"

    def ready(self):
        """Provádí funkci ``HeslarConfig.ready`` v rámci modulu ``webclient.heslar.apps``."""
        super(HeslarConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import heslar.signals
