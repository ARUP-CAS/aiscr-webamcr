from django.apps import AppConfig


class PasConfig(AppConfig):
    name = "pas"

    def ready(self):
        super(PasConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import pas.signals
