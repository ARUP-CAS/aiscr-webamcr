from django.apps import AppConfig


class LokalitaConfig(AppConfig):
    """Implementuje komponentu ``LokalitaConfig`` v rámci aplikace."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "lokalita"

    def ready(self):
        """Provádí operaci ready."""
        super(LokalitaConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import lokalita.signals
