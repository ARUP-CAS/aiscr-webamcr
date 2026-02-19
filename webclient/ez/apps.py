from django.apps import AppConfig


class EzConfig(AppConfig):
    name = "ez"

    def ready(self):
        super(EzConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import ez.signals
