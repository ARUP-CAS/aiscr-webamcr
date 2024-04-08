from django.apps import AppConfig


class NalezConfig(AppConfig):
    name = "nalez"

    def ready(self):
        super(NalezConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import nalez.signals
