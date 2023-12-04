from django.apps import AppConfig


class NeidentakceConfig(AppConfig):
    name = "neidentakce"

    def ready(self):
        super(NeidentakceConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import neidentakce.signals
