from django.apps import AppConfig


class ProjektConfig(AppConfig):
    """Implementuje komponentu ``ProjektConfig`` v rámci aplikace."""

    name = "projekt"

    def ready(self):
        """Provádí operaci ready."""
        super(ProjektConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import projekt.signals
