from django.apps import AppConfig


class AdbConfig(AppConfig):
    name = "adb"

    def ready(self):
        super(AdbConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import adb.signals
