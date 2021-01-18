from django.apps import AppConfig


class ProjektConfig(AppConfig):
    name = "projekt"

    def ready(self):
        super(ProjektConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import projekt.signals
