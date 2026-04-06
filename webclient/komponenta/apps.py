from django.apps import AppConfig


class KomponentaConfig(AppConfig):
    """Implementuje komponentu ``KomponentaConfig`` v rámci aplikace."""

    name = "komponenta"

    def ready(self):
        """Načte signály aplikace komponenta po spuštění Django."""
        super(KomponentaConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import komponenta.signals
