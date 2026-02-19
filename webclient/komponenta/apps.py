from django.apps import AppConfig


class KomponentaConfig(AppConfig):
    name = "komponenta"

    def ready(self):
        super(KomponentaConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import komponenta.signals
