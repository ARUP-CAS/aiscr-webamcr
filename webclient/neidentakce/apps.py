from django.apps import AppConfig


class NeidentakceConfig(AppConfig):
    """Implementuje komponentu ``NeidentakceConfig`` v rámci aplikace."""

    name = "neidentakce"

    def ready(self):
        """Načte signály aplikace neidentakce po spuštění Django."""
        super(NeidentakceConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import neidentakce.signals
