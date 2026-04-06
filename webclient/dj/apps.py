from django.apps import AppConfig


class DjConfig(AppConfig):
    """Implementuje komponentu ``DjConfig`` v rámci aplikace."""

    name = "dj"

    def ready(self):
        """Načte signály aplikace dj po spuštění Django."""
        super(DjConfig, self).ready()
        import dj.signals
