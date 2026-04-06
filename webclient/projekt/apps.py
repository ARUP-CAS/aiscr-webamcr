from django.apps import AppConfig


class ProjektConfig(AppConfig):
    """Implementuje komponentu ``ProjektConfig`` v rámci aplikace."""

    name = "projekt"

    def ready(self):
        """Zaregistruje signály aplikace projekt po spuštění Django."""
        super(ProjektConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import projekt.signals
