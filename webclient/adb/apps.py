from django.apps import AppConfig


class AdbConfig(AppConfig):
    """Implementuje komponentu ``AdbConfig`` v rámci aplikace."""

    name = "adb"

    def ready(self):
        """Provádí operaci ready.

        :return: Vrací výsledek provedené operace."""
        super(AdbConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import adb.signals
