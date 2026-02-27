from django.apps import AppConfig


class LokalitaConfig(AppConfig):
    """Zapouzdřuje chování třídy ``LokalitaConfig`` pro modul ``webclient.lokalita.apps``."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "lokalita"

    def ready(self):
        """Provádí funkci ``LokalitaConfig.ready`` v rámci modulu ``webclient.lokalita.apps``."""
        super(LokalitaConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import lokalita.signals
