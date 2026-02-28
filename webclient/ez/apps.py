from django.apps import AppConfig


class EzConfig(AppConfig):
    """Implementuje komponentu ``EzConfig`` v rámci aplikace."""

    name = "ez"

    def ready(self):
        """Provádí operaci ready."""
        super(EzConfig, self).ready()
        # noinspection PyUnresolvedReferences  # Potlačení varování IDE pro dynamický import signálů.
        import ez.signals
