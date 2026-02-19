from django.apps import AppConfig


class AdbConfig(AppConfig):
    name = "adb"

    def ready(self):
        super(AdbConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import adb.signals
