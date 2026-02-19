from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        super(CoreConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import core.signals
