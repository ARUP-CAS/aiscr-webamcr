from django.apps import AppConfig


class NeidentakceConfig(AppConfig):
    """Zapouzdřuje chování třídy ``NeidentakceConfig`` pro modul ``webclient.neidentakce.apps``."""
    name = "neidentakce"

    def ready(self):
        """Provádí funkci ``NeidentakceConfig.ready`` v rámci modulu ``webclient.neidentakce.apps``."""
        super(NeidentakceConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import neidentakce.signals
