from django.apps import AppConfig


class HeslarConfig(AppConfig):
    """Implementuje komponentu ``HeslarConfig`` v rámci aplikace."""

    name = "heslar"

    def ready(self):
        """Registruje signály aplikace heslar při spuštění Django."""
        super(HeslarConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import heslar.signals
