from django.apps import AppConfig


class DjConfig(AppConfig):
    name = "dj"

    def ready(self):
        super(DjConfig, self).ready()
        import dj.signals
