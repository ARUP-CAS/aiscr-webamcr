from django.apps import AppConfig


class HeslarConfig(AppConfig):
    """Implementuje komponentu ``HeslarConfig`` v rámci aplikace."""

    name = "heslar"

    def ready(self):
        """Provádí operaci ready."""
        super(HeslarConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import heslar.signals
