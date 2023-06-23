from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        super(CoreConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import core.signals
