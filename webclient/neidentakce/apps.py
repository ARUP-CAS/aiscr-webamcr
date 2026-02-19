from django.apps import AppConfig


class NeidentakceConfig(AppConfig):
    name = "neidentakce"

    def ready(self):
        super(NeidentakceConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import neidentakce.signals
