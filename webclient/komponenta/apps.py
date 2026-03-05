from django.apps import AppConfig


class KomponentaConfig(AppConfig):
    """Implementuje komponentu ``KomponentaConfig`` v rámci aplikace."""

    name = "komponenta"

    def ready(self):
        """Provádí operaci ready."""
        super(KomponentaConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import komponenta.signals
