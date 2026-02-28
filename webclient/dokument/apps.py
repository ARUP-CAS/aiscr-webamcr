from django.apps import AppConfig


class DokumentConfig(AppConfig):
    """Implementuje komponentu ``DokumentConfig`` v rámci aplikace."""

    name = "dokument"

    def ready(self):
        """Provádí operaci ready."""
        super(DokumentConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import dokument.signals
