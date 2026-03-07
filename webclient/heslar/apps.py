from django.apps import AppConfig


class HeslarConfig(AppConfig):
    """Implementuje komponentu ``HeslarConfig`` v rámci aplikace."""

    name = "heslar"

    def ready(self):
        """Provádí operaci ready."""
        super(HeslarConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import heslar.signals
