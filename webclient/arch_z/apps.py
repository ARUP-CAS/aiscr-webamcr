from django.apps import AppConfig


class ArchZConfig(AppConfig):
    """Implementuje komponentu ``ArchZConfig`` v rámci aplikace."""

    name = "arch_z"

    def ready(self):
        """Registruje signály aplikace arch_z při spuštění Django."""
        super(ArchZConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import arch_z.signals
