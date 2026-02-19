from django.apps import AppConfig


class DokumentConfig(AppConfig):
    name = "dokument"

    def ready(self):
        super(DokumentConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import dokument.signals
