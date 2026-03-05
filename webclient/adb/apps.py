from django.apps import AppConfig


class AdbConfig(AppConfig):
    """Implementuje komponentu ``AdbConfig`` v rámci aplikace."""

    name = "adb"

    def ready(self):
        """Provádí operaci ready."""
        super(AdbConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import adb.signals
