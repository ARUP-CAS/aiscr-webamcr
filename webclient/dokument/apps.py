from django.apps import AppConfig


class DokumentConfig(AppConfig):
    """Implementuje komponentu ``DokumentConfig`` v rámci aplikace."""

    name = "dokument"

    def ready(self):
        """
        Inicializuje aplikaci a zaregistruje signály ze modulu dokument.
        """
        super(DokumentConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import dokument.signals
