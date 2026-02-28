from django.apps import AppConfig


class PasConfig(AppConfig):
    """Implementuje komponentu ``PasConfig`` v rámci aplikace."""

    name = "pas"

    def ready(self):
        """Provádí operaci ready."""
        super(PasConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import pas.signals
