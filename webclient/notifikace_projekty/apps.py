from django.apps import AppConfig


class NotifikaceProjektyConfig(AppConfig):
    """Implementuje komponentu ``NotifikaceProjektyConfig`` v rámci aplikace."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "notifikace_projekty"

    def ready(self):
        """Provádí operaci ready."""
        super(NotifikaceProjektyConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import notifikace_projekty.signals
