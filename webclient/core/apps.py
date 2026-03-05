from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Implementuje komponentu ``CoreConfig`` v rámci aplikace."""

    name = "core"

    def ready(self):
        """Provádí operaci ready."""
        super(CoreConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import core.signals
