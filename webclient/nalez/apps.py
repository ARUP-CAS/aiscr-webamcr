from django.apps import AppConfig


class NalezConfig(AppConfig):
    """Implementuje komponentu ``NalezConfig`` v rámci aplikace."""

    name = "nalez"

    def ready(self):
        """Načte signály aplikace nalez po spuštění Django."""
        super(NalezConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import nalez.signals
