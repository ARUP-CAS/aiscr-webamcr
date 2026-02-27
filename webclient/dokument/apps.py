from django.apps import AppConfig


class DokumentConfig(AppConfig):
    """Zapouzdřuje chování třídy ``DokumentConfig`` pro modul ``webclient.dokument.apps``."""
    name = "dokument"

    def ready(self):
        """Provádí funkci ``DokumentConfig.ready`` v rámci modulu ``webclient.dokument.apps``."""
        super(DokumentConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import dokument.signals
