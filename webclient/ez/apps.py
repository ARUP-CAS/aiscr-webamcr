from django.apps import AppConfig


class EzConfig(AppConfig):
    name = "ez"

    def ready(self):
        super(EzConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import ez.signals
