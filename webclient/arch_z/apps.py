from django.apps import AppConfig


class ArchZConfig(AppConfig):
    name = "arch_z"

    def ready(self):
        super(ArchZConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import arch_z.signals
