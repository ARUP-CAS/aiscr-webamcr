from django.apps import AppConfig


class HeslarConfig(AppConfig):
    name = "heslar"

    def ready(self):
        super(HeslarConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import heslar.signals
