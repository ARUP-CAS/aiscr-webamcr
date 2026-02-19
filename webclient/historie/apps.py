from django.apps import AppConfig


class HistorieConfig(AppConfig):
    name = "historie"

    def ready(self):
        super(HistorieConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import historie.signals
