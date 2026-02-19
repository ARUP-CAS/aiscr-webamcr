from django.apps import AppConfig


class PianConfig(AppConfig):
    name = "pian"

    def ready(self):
        super(PianConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import pian.signals
