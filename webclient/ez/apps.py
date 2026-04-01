from django.apps import AppConfig


class EzConfig(AppConfig):
    """Implementuje komponentu ``EzConfig`` v rámci aplikace."""

    name = "ez"

    def ready(self):
        """Zaregistruje signály aplikace ez po spuštění Django."""
        super(EzConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import ez.signals
