from django.apps import AppConfig


class UzivatelConfig(AppConfig):
    name = "uzivatel"

    def ready(self):
        super(UzivatelConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import uzivatel.signals
