from django.apps import AppConfig


class EzConfig(AppConfig):
    """Zapouzdřuje chování třídy ``EzConfig`` pro modul ``webclient.ez.apps``."""
    name = "ez"

    def ready(self):
        """Provádí funkci ``EzConfig.ready`` v rámci modulu ``webclient.ez.apps``."""
        super(EzConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import ez.signals
