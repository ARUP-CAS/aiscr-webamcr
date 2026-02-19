from django.apps import AppConfig


class LokalitaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lokalita"

    def ready(self):
        super(LokalitaConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import lokalita.signals
