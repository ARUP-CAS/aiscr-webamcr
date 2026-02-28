from django.apps import AppConfig


class ArchZConfig(AppConfig):
    """Implementuje komponentu ``ArchZConfig`` v rámci aplikace."""

    name = "arch_z"

    def ready(self):
        """Provádí operaci ready."""
        super(ArchZConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import arch_z.signals
