from django.apps import AppConfig


class NalezConfig(AppConfig):
    """Implementuje komponentu ``NalezConfig`` v rámci aplikace."""

    name = "nalez"

    def ready(self):
        """Provádí operaci ready."""
        super(NalezConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import nalez.signals
