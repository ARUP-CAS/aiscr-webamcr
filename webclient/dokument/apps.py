from django.apps import AppConfig


class DokumentConfig(AppConfig):
    name = "dokument"

    def ready(self):
        super(DokumentConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import dokument.signals
