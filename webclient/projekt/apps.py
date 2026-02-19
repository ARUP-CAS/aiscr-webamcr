from django.apps import AppConfig


class ProjektConfig(AppConfig):
    name = "projekt"

    def ready(self):
        super(ProjektConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import projekt.signals
