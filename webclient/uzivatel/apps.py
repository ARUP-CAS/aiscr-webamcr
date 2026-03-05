from django.apps import AppConfig


class UzivatelConfig(AppConfig):
    """Implementuje komponentu ``UzivatelConfig`` v rámci aplikace."""

    name = "uzivatel"

    def ready(self):
        """Provádí operaci ready."""
        super(UzivatelConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import uzivatel.signals
