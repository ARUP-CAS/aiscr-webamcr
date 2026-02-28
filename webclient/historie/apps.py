from django.apps import AppConfig


class HistorieConfig(AppConfig):
    """Implementuje komponentu ``HistorieConfig`` v rámci aplikace."""

    name = "historie"

    def ready(self):
        """Provádí operaci ready."""
        super(HistorieConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import historie.signals
