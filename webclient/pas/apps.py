from django.apps import AppConfig


class PasConfig(AppConfig):
    name = "pas"

    def ready(self):
        super(PasConfig, self).ready()
        # noinspection PyUnresolvedReferences
