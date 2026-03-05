from django.apps import AppConfig


class PasConfig(AppConfig):
    """Implementuje komponentu ``PasConfig`` v rámci aplikace."""

    name = "pas"

    def ready(self):
        """Provádí operaci ready."""
        super(PasConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import pas.signals
