from django.apps import AppConfig


class PianConfig(AppConfig):
    """Implementuje komponentu ``PianConfig`` v rámci aplikace."""

    name = "pian"

    def ready(self):
        """Načte signály aplikace pian po spuštění Django."""
        super(PianConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import pian.signals
