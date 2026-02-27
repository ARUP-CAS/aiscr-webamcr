from django.apps import AppConfig


class ArchZConfig(AppConfig):
    """Zapouzdřuje chování třídy ``ArchZConfig`` pro modul ``webclient.arch_z.apps``."""
    name = "arch_z"

    def ready(self):
        """Provádí funkci ``ArchZConfig.ready`` v rámci modulu ``webclient.arch_z.apps``."""
        super(ArchZConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import arch_z.signals
