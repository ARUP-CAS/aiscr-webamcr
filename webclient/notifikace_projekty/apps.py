from django.apps import AppConfig


class NotifikaceProjektyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifikace_projekty"

    def ready(self):
        super(NotifikaceProjektyConfig, self).ready()
        # noinspection PyUnresolvedReferences
        import notifikace_projekty.signals
