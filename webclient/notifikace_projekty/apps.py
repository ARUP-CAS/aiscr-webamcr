from django.apps import AppConfig


class NotifikaceProjektyConfig(AppConfig):
    """Implementuje komponentu ``NotifikaceProjektyConfig`` v rámci aplikace."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "notifikace_projekty"

    def ready(self):
        """Načte signály aplikace notifikace_projekty po spuštění Django."""
        super(NotifikaceProjektyConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import notifikace_projekty.signals
