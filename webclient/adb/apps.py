from django.apps import AppConfig


class AdbConfig(AppConfig):
    """Zapouzdřuje chování třídy ``AdbConfig`` pro modul ``webclient.adb.apps``."""
    name = "adb"

    def ready(self):
        """Provádí funkci ``AdbConfig.ready`` v rámci modulu ``webclient.adb.apps``."""
        super(AdbConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import adb.signals
