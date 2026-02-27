from django.apps import AppConfig


class KomponentaConfig(AppConfig):
    """Zapouzdřuje chování třídy ``KomponentaConfig`` pro modul ``webclient.komponenta.apps``."""
    name = "komponenta"

    def ready(self):
        """Provádí funkci ``KomponentaConfig.ready`` v rámci modulu ``webclient.komponenta.apps``."""
        super(KomponentaConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import komponenta.signals
