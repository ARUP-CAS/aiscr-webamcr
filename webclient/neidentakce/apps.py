from django.apps import AppConfig


class NeidentakceConfig(AppConfig):
    """Implementuje komponentu ``NeidentakceConfig`` v rámci aplikace."""

    name = "neidentakce"

    def ready(self):
        """Provádí operaci ready."""
        super(NeidentakceConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import neidentakce.signals
