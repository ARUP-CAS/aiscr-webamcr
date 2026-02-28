from django.apps import AppConfig


class DjConfig(AppConfig):
    """Implementuje komponentu ``DjConfig`` v rámci aplikace."""

    name = "dj"

    def ready(self):
        """Provádí operaci ready."""
        super(DjConfig, self).ready()
        import dj.signals
