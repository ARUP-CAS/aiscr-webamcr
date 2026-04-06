from django.apps import AppConfig


class UzivatelConfig(AppConfig):
    """Implementuje komponentu ``UzivatelConfig`` v rámci aplikace."""

    name = "uzivatel"

    def ready(self):
        """Zaregistruje signály aplikace uzivatel po spuštění Django."""
        super(UzivatelConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import uzivatel.signals
