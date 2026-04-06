from django.apps import AppConfig


class PasConfig(AppConfig):
    """Implementuje komponentu ``PasConfig`` v rámci aplikace."""

    name = "pas"

    def ready(self):
        """Registruje signály aplikace pas při spuštění Django."""
        super(PasConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import pas.signals
