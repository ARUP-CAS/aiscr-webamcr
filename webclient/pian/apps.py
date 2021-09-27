from django.apps import AppConfig


class PianConfig(AppConfig):
    name = "pian"

    def ready(self):
        super(PianConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import pian.signals
